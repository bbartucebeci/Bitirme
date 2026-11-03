#!/usr/bin/env python3
"""Method 6: ARIMA / Seasonal ARIMA (Box-Jenkins with Automatic Order Selection).

EE / Signal Processing Rationale:
---------------------------------
An ARIMA(p, d, q) model treats the PRI sequence as the output of a rational (pole-zero)
linear filter driven by white noise, after d-th order differencing:

    phi(B) (1 - B)^d y[n] = c + theta(B) e[n]

where B is the one-pulse delay operator, phi(B) holds the p autoregressive poles and
theta(B) the q moving-average zeros. Periodic radar PRI laws are handled with seasonal
differencing (1 - B^S), i.e. a comb filter that removes any waveform repeating every S
pulses (SARIMA(p, d, q)(0, 1, 0)_S):

  - Stable / Jittered PRI   -> ARMA(p, q) around a constant (d = 0, no seasonal term)
  - Staggered PRI           -> (1 - B^S) with S = stagger length cancels the pattern
  - Dwell-and-Switch        -> (1 - B^S) with S = full dwell cycle
  - Sliding PRI (sawtooth)  -> (1 - B^S) with S = pulses per ramp

Box-Jenkins procedure per context window:
  1. ESM front-end gating (clean_pri_context), shared with all classic baselines.
  2. Identification:
       - Seasonal: if the strongest ACF peak (seasonality.seasonal_candidates) has
         r[S] >= 0.5, apply one seasonal difference with that S.
       - Non-seasonal: otherwise choose d in {0, 1} with the KPSS stationarity test.
  3. Estimation: fit (p, q) in {0, 1, 2} x {0, 1} by exact Gaussian maximum likelihood
     (Kalman-filter state space, statsmodels) and keep the lowest-AIC model. AIC is only
     compared between models sharing the same differencing, as Box-Jenkins requires.
  4. Forecast the 32-pulse horizon from the selected model.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import warnings
from typing import Optional, Tuple

import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import kpss

warnings.filterwarnings("ignore")

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
from classic_methods.seasonality import acf, seasonal_candidates, winsorize

P_GRID = (0, 1, 2)
Q_GRID = (0, 1)
SEASONAL_ACF_MIN = 0.5
KPSS_ALPHA = 0.05


def identify_differencing(x: np.ndarray, max_period: int = 24) -> Tuple[int, int]:
    """Box-Jenkins identification step. Returns (d, S); S = 0 means no seasonal difference."""
    cands = seasonal_candidates(x, max_period=max_period, top_k=1)
    if cands:
        s = cands[0]
        if acf(winsorize(x), s)[s] >= SEASONAL_ACF_MIN:
            return 0, s

    # KPSS: H0 = level-stationary. Reject -> difference once.
    try:
        _, p_value, _, _ = kpss(winsorize(x), regression="c", nlags="auto")
        d = 1 if p_value < KPSS_ALPHA else 0
    except Exception:
        d = 0
    return d, 0


def fit_best_arima(x: np.ndarray, d: int, s: int):
    """Fits the (p, q) grid for fixed differencing and returns (order, result) with lowest AIC."""
    seasonal_order = (0, 1, 0, s) if s > 0 else (0, 0, 0, 0)
    best_order, best_res, best_aic = None, None, np.inf
    for p in P_GRID:
        for q in Q_GRID:
            try:
                res = ARIMA(x, order=(p, d, q), seasonal_order=seasonal_order).fit()
            except Exception:
                continue
            aic = float(res.aic)
            if np.isfinite(aic) and aic < best_aic:
                best_order, best_res, best_aic = (p, d, q), res, aic
    return best_order, best_res


def arima_forecast(
    context: np.ndarray,
    horizon_len: int = 32,
    target_param: str = "PRI",
    max_period: int = 24,
    use_gate: bool = True,
) -> np.ndarray:
    """Forecasts future PDW values with an automatically identified (S)ARIMA model."""
    raw = np.asarray(context, dtype=np.float64)
    if len(raw) == 0:
        return np.zeros(horizon_len, dtype=np.float64)

    if use_gate and target_param.upper() in ["PRI", "MEASURED_DELTA_TOA"]:
        x = clean_pri_context(raw)
    else:
        x = raw.copy()

    # Degenerate (constant) context, e.g. clean Stable PRI.
    if len(x) < 12 or float(np.std(x)) < 1e-9:
        return np.full(horizon_len, float(np.median(x)), dtype=np.float64)

    # Fit in normalised units for numerical conditioning of the optimiser.
    mu, sd = float(np.mean(x)), float(np.std(x))
    z = (x - mu) / sd

    d, s = identify_differencing(z, max_period=max_period)
    _, res = fit_best_arima(z, d, s)
    if res is None:
        return np.full(horizon_len, float(np.median(x)), dtype=np.float64)

    preds = np.asarray(res.forecast(horizon_len), dtype=np.float64) * sd + mu
    if not np.all(np.isfinite(preds)):
        return np.full(horizon_len, float(np.median(x)), dtype=np.float64)
    return preds


def main():
    parser = argparse.ArgumentParser(description="PULSAR Classic Baseline 6: ARIMA / Seasonal ARIMA Predictor")
    parser.add_argument("--profile-mode", choices=["fixed", "varying"], default="fixed")
    parser.add_argument("--target-param", choices=list(PARAM_SPECS.keys()), default="PRI")
    parser.add_argument("--radar-type", choices=RADAR_TYPES + ["all"], default="all")
    parser.add_argument("--error-level", choices=ERROR_LEVELS + ["all"], default="all")
    parser.add_argument("--max-period", type=int, default=24, help="Largest seasonal period S (pulses)")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    rtypes = RADAR_TYPES if args.radar_type == "all" else [args.radar_type]
    elevels = ERROR_LEVELS if args.error_level == "all" else [args.error_level]

    predict_fn = lambda ctx, h, p: arima_forecast(ctx, horizon_len=h, target_param=p, max_period=args.max_period)

    evaluate_method_across_benchmarks(
        method_name="ARIMA (Box-Jenkins, AIC-selected)",
        method_slug="arima",
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
