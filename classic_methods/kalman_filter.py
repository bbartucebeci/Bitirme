#!/usr/bin/env python3
"""Method 4: Kalman Filter Bank (Multiple-Model Linear-Gaussian State-Space Predictor).

EE / Signal Processing Rationale:
---------------------------------
The Kalman filter is the minimum-mean-square-error recursive estimator for a linear
state-space model with Gaussian noise:

    State:        s[n] = F s[n-1] + w[n],   w ~ N(0, Q)
    Observation:  y[n] = H s[n]   + v[n],   v ~ N(0, R)

In ESM pulse-train tracking it is the standard tool for smoothing a measured PRI
sequence, because TOA measurement noise (v) and genuine transmitter PRI evolution
(w) are naturally separated by the Q/R ratio.

A single fixed state model cannot represent all radar PRI laws, so this script runs a
bank of candidate models and selects one per sequence (a static multiple-model filter):

  1. Local level (random walk):      s = [L],       F = [1]
     -> Stable PRI, Jittered PRI (L tracks the mean, R absorbs the jitter)
  2. Local linear trend:             s = [L, B],    F = [[1, 1], [0, 1]]
     -> Slowly ramping PRI (Sliding PRI within one ramp)
  3. Periodic level with period P:   s = [c_0 .. c_{P-1}], F = cyclic shift
     -> Staggered PRI, Dwell-and-Switch, Sliding (sawtooth) PRI
     Each phase slot c_k is its own random walk, observed once every P pulses.
     Because F is a permutation and Q, P0 are diagonal, the P-dimensional filter
     decouples exactly into P independent scalar filters (O(n) total cost).

Hyperparameters per model: q = Q/R in a log grid. R is concentrated out of the
likelihood (closed-form MLE of the innovation scale), so only q is searched.

Model selection is prequential: every candidate is scored by the mean absolute value of
its one-step-ahead innovations (honest out-of-sample prediction errors) over the same
evaluation window (pulses after the largest candidate period), so all models are compared
on identical data. Over-fitted periods (e.g. harmonics 2P, 3P or a period fitted to random
jitter) predict worse one step ahead and are rejected without hand-tuned thresholds.
The L1 score is used instead of the Gaussian log-likelihood because PDW errors are a
mixture of tiny clock noise and rare gross outliers (residual missing / false pulses):
a single outlier would otherwise dominate the likelihood and decide the model.

Robustness (residual false / missing-pulse outliers that survive the ESM gate):
  - Huber-clipped innovation update (Masreliez-type robust Kalman filter): the
    innovation used in the state update is clipped to +/- c * sqrt(S) * sigma, so an
    outlier has bounded influence but the filter can never lock itself out.
  - sigma is the RMS of the standardised innovations from a first, unclipped pass;
    the clipped second pass is the one that is scored and forecast. (A MAD scale was
    tested and rejected on the validation split: it collapses to the clock-noise level,
    so the clip becomes too tight to re-lock after a genuine phase change.)

The selected model's final state is propagated over the forecast horizon.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Dict, Tuple

import numpy as np

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.common import (
    ERROR_LEVELS,
    PARAM_SPECS,
    RADAR_TYPES,
    clean_pri_context,
    evaluate_method_across_benchmarks,
)

Q_RATIO_GRID = (1e-4, 1e-3, 1e-2, 1e-1, 1.0)
HUBER_C = 2.0  # Innovation clipping threshold (in innovation standard deviations)
DIFFUSE_VAR = 1e7  # Large prior variance (in normalised units) = diffuse initialisation


# ---------------------------------------------------------------------------
# Elementary filters (run in normalised units, R = 1, Q = q)
# ---------------------------------------------------------------------------

def _clip(nu: float, f: float, sigma: float | None) -> float:
    """Huber clipping of an innovation with predicted variance f * sigma^2."""
    if sigma is None:
        return nu
    lim = HUBER_C * sigma * np.sqrt(f)
    return min(max(nu, -lim), lim)


def _scalar_rw_filter(
    y: np.ndarray,
    q: float,
    sigma: float | None = None,
) -> Tuple[float, np.ndarray, np.ndarray]:
    """Scalar random-walk KF. Returns final level, innovations, innovation variances.

    Innovations are one-step-ahead prediction errors y[n] - L[n|n-1]. The first
    sample only initialises the state (its innovation is NaN).
    """
    n = len(y)
    innov = np.full(n, np.nan)
    fvar = np.full(n, np.nan)
    if n == 0:
        return 0.0, innov, fvar

    level = float(y[0])
    p = 1.0  # posterior variance after absorbing y[0] with R = 1
    for k in range(1, n):
        p_pred = p + q
        f = p_pred + 1.0
        nu = y[k] - level
        innov[k] = nu
        fvar[k] = f
        gain = p_pred / f
        level = level + gain * _clip(nu, f, sigma)
        p = (1.0 - gain) * p_pred
    return level, innov, fvar


def _trend_filter(
    y: np.ndarray,
    q: float,
    sigma: float | None = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Local linear trend KF. Returns final state [L, B], innovations, variances."""
    n = len(y)
    innov = np.full(n, np.nan)
    fvar = np.full(n, np.nan)
    F = np.array([[1.0, 1.0], [0.0, 1.0]])
    Qm = np.diag([q, q * 0.1])
    s = np.array([float(y[0]), 0.0])
    P = np.diag([1.0, DIFFUSE_VAR])
    for k in range(1, n):
        s_pred = F @ s
        P_pred = F @ P @ F.T + Qm
        f = P_pred[0, 0] + 1.0
        nu = y[k] - s_pred[0]
        # The slope is only identified after the second sample: skip scoring k = 1.
        if k >= 2:
            innov[k] = nu
            fvar[k] = f
        K = P_pred[:, 0] / f
        s = s_pred + K * (_clip(nu, f, sigma) if k >= 2 else nu)
        P = P_pred - np.outer(K, P_pred[0, :])
    return s, innov, fvar


def _periodic_filter(
    y: np.ndarray,
    period: int,
    q: float,
    sigma: float | None = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Periodic-level KF, decoupled into `period` scalar random-walk filters.

    Returns per-phase final levels (indexed by n mod period), innovations, variances.
    """
    n = len(y)
    innov = np.full(n, np.nan)
    fvar = np.full(n, np.nan)
    levels = np.zeros(period)
    for ph in range(period):
        idx = np.arange(ph, n, period)
        lvl, nu, f = _scalar_rw_filter(y[idx], q, sigma)
        levels[ph] = lvl
        innov[idx] = nu
        fvar[idx] = f
    return levels, innov, fvar


# ---------------------------------------------------------------------------
# Model scoring & forecasting
# ---------------------------------------------------------------------------

def _innovation_sigma(innov: np.ndarray, fvar: np.ndarray, start: int) -> float:
    """RMS scale of the standardised innovations nu / sqrt(f) (used for clipping)."""
    u = innov[start:] / np.sqrt(fvar[start:])
    u = u[np.isfinite(u)]
    if len(u) == 0:
        return 1.0
    return max(float(np.sqrt(np.mean(u ** 2))), 1e-6)


def _prequential_l1(innov: np.ndarray, start: int) -> float:
    """Mean absolute one-step-ahead prediction error over innovations[start:]."""
    nu = innov[start:]
    nu = nu[np.isfinite(nu)]
    return float(np.mean(np.abs(nu))) if len(nu) >= 4 else np.inf


def _run(kind: str, z: np.ndarray, period: int, q: float, sigma: float | None):
    if kind == "level":
        return _scalar_rw_filter(z, q, sigma)
    if kind == "trend":
        return _trend_filter(z, q, sigma)
    return _periodic_filter(z, period, q, sigma)


def select_model(z: np.ndarray, max_period: int = 24) -> Dict:
    """Runs the model bank and returns the best (model, period, q) by prequential
    one-step L1 error, together with the final state of that model."""
    n = len(z)
    max_p = int(min(max_period, max(2, n // 3)))
    eval_start = max_p + 1  # common scoring window for all candidates

    candidates = [("level", 1), ("trend", 1)] + [("periodic", p) for p in range(2, max_p + 1)]
    best: Dict = {"score": np.inf}
    for q in Q_RATIO_GRID:
        for kind, period in candidates:
            # Pass 1 (unclipped) -> innovation scale for the clip
            _, nu, f = _run(kind, z, period, q, None)
            sigma = _innovation_sigma(nu, f, eval_start)
            # Pass 2 (clipped robust KF) -> score + final state
            state, nu, f = _run(kind, z, period, q, sigma)
            score = _prequential_l1(nu, eval_start)
            if score < best["score"] - 1e-12:  # strict: ties keep the simpler, earlier model
                best = {"kind": kind, "period": period, "q": q, "score": score,
                        "sigma": sigma, "state": state}
    return best


def kalman_forecast(
    context: np.ndarray,
    horizon_len: int = 32,
    target_param: str = "PRI",
    max_period: int = 24,
    use_gate: bool = True,
) -> np.ndarray:
    """Forecasts future PDW values with the robust Kalman filter bank."""
    raw = np.asarray(context, dtype=np.float64)
    if len(raw) == 0:
        return np.zeros(horizon_len, dtype=np.float64)

    if use_gate and target_param.upper() in ["PRI", "MEASURED_DELTA_TOA"]:
        x = clean_pri_context(raw)
    else:
        x = raw.copy()

    # Degenerate (constant) context, e.g. clean Stable PRI: the filter is exact.
    scale = float(np.std(x))
    if len(x) < 8 or scale < 1e-9:
        return np.full(horizon_len, float(np.median(x)), dtype=np.float64)

    # Work in normalised units so the q grid is scale-free.
    mu = float(np.mean(x))
    z = (x - mu) / scale

    best = select_model(z, max_period=max_period)
    kind, period, state = best["kind"], best["period"], best["state"]
    h = np.arange(1, horizon_len + 1)

    if kind == "level":
        fz = np.full(horizon_len, float(state))
    elif kind == "trend":
        fz = state[0] + h * state[1]
    else:
        fz = state[(len(z) - 1 + h) % period]

    return fz * scale + mu


def main():
    parser = argparse.ArgumentParser(description="PULSAR Classic Baseline 4: Kalman Filter Bank Predictor")
    parser.add_argument("--profile-mode", choices=["fixed", "varying"], default="fixed")
    parser.add_argument("--target-param", choices=list(PARAM_SPECS.keys()), default="PRI")
    parser.add_argument("--radar-type", choices=RADAR_TYPES + ["all"], default="all")
    parser.add_argument("--error-level", choices=ERROR_LEVELS + ["all"], default="all")
    parser.add_argument("--max-period", type=int, default=24, help="Largest periodic-level model in the bank (pulses)")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    rtypes = RADAR_TYPES if args.radar_type == "all" else [args.radar_type]
    elevels = ERROR_LEVELS if args.error_level == "all" else [args.error_level]

    predict_fn = lambda ctx, h, p: kalman_forecast(ctx, horizon_len=h, target_param=p, max_period=args.max_period)

    evaluate_method_across_benchmarks(
        method_name="Kalman Filter Bank",
        method_slug="kalman_filter",
        predict_fn=predict_fn,
        profile_mode=args.profile_mode,
        target_param=args.target_param,
        radar_types=rtypes,
        error_levels=elevels,
        context_len=args.context_len,
        horizon_len=args.horizon,
        max_test_seqs=args.max_test_seqs,
        smoke_test=args.smoke_test,
    )


if __name__ == "__main__":
    main()
