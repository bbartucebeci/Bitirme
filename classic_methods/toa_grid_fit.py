#!/usr/bin/env python3
"""Method 10: TOA-Domain Grid Fit (RANSAC) and Grid-Point Forecast.

EE / Signal Processing Rationale:
---------------------------------
A periodic emitter transmits on the time grid

    TOA = t0 + k * T + o_m          (T = frame period, o_m = M positions in the frame)

The index-domain baselines (period estimation, Kalman bank, ARIMA) fit a pattern to the
Delta-TOA sequence and lose phase at every missed or false pulse, then try to re-lock.
Fitting the grid directly to the TOAs avoids the problem: a missed pulse is an empty
grid point and a false pulse is an outlier, and neither moves any other pulse.

Procedure (context only):
  1. Candidate frame periods come from SDIF, CDIF and the PRI transform
     (cdif_sdif.py, pri_transform.py), in that order. Later sources are only run while
     no candidate explains the context well.
  2. RANSAC for each candidate: the minimal sample is two pulses that sit on the same
     position several frames apart; it fixes T = (t_j - t_i) / k. The consensus set is
     the pulses that fall into dense, narrow phase clusters when the TOAs are folded
     modulo T (toa_utils.fold_and_cluster). False pulses never join a cluster.
  3. Least-squares refit of [T, o_0 .. o_{M-1}] on the consensus set
     (the model is linear once k and m are assigned).
  4. The smallest period that explains (almost) as many pulses as the best one is kept,
     so 2T and 3T are not preferred over T.
  5. Forecast = spacing of the next grid points after the last context TOA. Pulses
     missed at the end of the context are handled automatically, because the grid
     position of "now" comes from time, not from a pulse count.
  6. No acceptable grid (jittered PRI) -> gated rolling median.

Optional slip hedge (`hedge=True`, toa_utils.hedged_grid_forecast): the benchmark scores
horizon row h against the PRI of the h-th RECEIVED pulse. Pulses missed inside the
horizon shift the later rows along the pattern, which no context-only method can
predict. The hedge estimates the miss rate from the empty grid points of the context
and forecasts the median PRI over the resulting shift distribution.
On the validation split the hedge did NOT reduce the MAE (see robust_tuning_val): the
miss rate estimated from one 96-pulse context (0 to 4 events) is too noisy, and even with
the true rate the gain is a few microseconds on stagger only. It is kept as an option and
is not part of the benchmark table.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Callable, List, Optional, Sequence

import numpy as np

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.cdif_sdif import candidate_periods, cdif_candidates, sdif_candidates
from classic_methods.pri_transform import pri_transform_periods
from classic_methods.toa_utils import (
    FALLBACK_WINDOW,
    PHASE_TOL_US,
    SEARCH_TOL_US,
    GridModel,
    fallback_forecast,
    fold_and_cluster,
    grid_forecast,
    hedged_grid_forecast,
    is_acceptable,
    is_pri_target,
    refine_period,
    refit_least_squares,
    run_cli,
    toas_from_context,
    tuned,
)

# Tuned on the validation split (see tune_robust_methods.py).
RANSAC_ITERS = tuned("toa_grid_fit.RANSAC_ITERS", 12)  # random two-pulse hypotheses per candidate period
GOOD_INLIER_FRACTION = 0.93  # a model this good stops the search over further sources
RANSAC_SEED = 20261020     # fixed seed: forecasts are reproducible

PERIOD_SOURCES = ("sdif", "cdif", "pri_transform")


def _source_periods(name: str, toas: np.ndarray):
    if name == "sdif":
        return candidate_periods(sdif_candidates, toas)
    if name == "cdif":
        return candidate_periods(cdif_candidates, toas)
    if name == "pri_transform":
        return pri_transform_periods(toas)
    if name == "lomb_scargle":
        from classic_methods.lomb_scargle import lomb_scargle_periods

        return lomb_scargle_periods(toas)
    raise ValueError(f"Unknown period source: {name}")


def _n_inliers(model: Optional[GridModel]) -> int:
    return int(model.inlier_mask().sum()) if model is not None else 0


def ransac_grid(
    toas: np.ndarray,
    period: float,
    n_iter: int = RANSAC_ITERS,
    tol: float = PHASE_TOL_US,
    rng: Optional[np.random.Generator] = None,
) -> Optional[GridModel]:
    """RANSAC fit of the TOA grid around one candidate frame period."""
    if rng is None:
        rng = np.random.default_rng(RANSAC_SEED)
    n = len(toas)
    t0 = refine_period(toas, period)
    best = fold_and_cluster(toas, t0, tol=tol)

    for _ in range(n_iter):
        i = int(rng.integers(0, n))
        d = toas - toas[i]
        k = np.rint(d / t0)
        cand = np.nonzero((k >= 1) & (np.abs(d - k * t0) < SEARCH_TOL_US))[0]
        if len(cand) == 0:
            continue
        # Long baselines give the most accurate period: sample from the far half.
        far = cand[k[cand] >= np.median(k[cand])]
        j = int(rng.choice(far))
        model = fold_and_cluster(toas, d[j] / k[j], tol=tol)
        if _n_inliers(model) > _n_inliers(best):
            best = model

    if best is None:
        return None
    # Least-squares refit, re-assign the pulses with the refined period, refit the offsets.
    refit = refit_least_squares(best, toas)
    again = fold_and_cluster(toas, refit.period, tol=tol)
    if _n_inliers(again) >= _n_inliers(best):
        best = refit_least_squares(again, toas)
    else:
        best = refit
    return best


def _reduce_to_fundamental(toas: np.ndarray, model: GridModel, tol: float) -> GridModel:
    """Replaces T by T/2 or T/3 when the shorter period explains the pulses as well."""
    for div in (3, 2):
        sub = fold_and_cluster(toas, model.period / div, tol=tol)
        if is_acceptable(sub) and _n_inliers(sub) >= _n_inliers(model) - 1:
            return _reduce_to_fundamental(toas, refit_least_squares(sub, toas), tol)
    return model


def fit_toa_grid(
    toas: np.ndarray,
    sources: Sequence[str] = PERIOD_SOURCES,
    n_iter: int = RANSAC_ITERS,
    tol: float = PHASE_TOL_US,
) -> Optional[GridModel]:
    """Best acceptable grid model of the context TOAs, or None."""
    if len(toas) < 16:
        return None
    rng = np.random.default_rng(RANSAC_SEED)
    best: Optional[GridModel] = None
    tried: List[float] = []
    for name in sources:
        for period in _source_periods(name, toas):
            if any(abs(period - p) < 1e-3 * p for p in tried):
                continue
            tried.append(period)
            model = ransac_grid(toas, period, n_iter=n_iter, tol=tol, rng=rng)
            if not is_acceptable(model):
                continue
            model = _reduce_to_fundamental(toas, model, tol)
            if best is None or _n_inliers(model) > _n_inliers(best) + 1 or (
                abs(_n_inliers(model) - _n_inliers(best)) <= 1 and model.period < 0.75 * best.period
            ):
                best = model
        if best is not None and best.inlier_fraction >= GOOD_INLIER_FRACTION:
            break
    return best


def toa_grid_forecast(
    context: np.ndarray,
    horizon_len: int = 32,
    target_param: str = "PRI",
    hedge: bool = False,
    sources: Sequence[str] = PERIOD_SOURCES,
    fallback_window: int = FALLBACK_WINDOW,
) -> np.ndarray:
    """Forecasts the next PRIs as the spacing of the next TOA grid points."""
    raw = np.asarray(context, dtype=np.float64)
    if len(raw) == 0:
        return np.zeros(horizon_len, dtype=np.float64)
    if is_pri_target(target_param):
        toas = toas_from_context(raw)
        model = fit_toa_grid(toas, sources=sources)
        if model is not None:
            if hedge:
                preds = hedged_grid_forecast(model, toas, horizon_len)
            else:
                preds = grid_forecast(model, toas[-1], horizon_len)
            if len(preds) == horizon_len and np.all(np.isfinite(preds)):
                return preds
    return fallback_forecast(raw, horizon_len, target_param, window=fallback_window)


def toa_grid_hedged_forecast(context: np.ndarray, horizon_len: int = 32, target_param: str = "PRI") -> np.ndarray:
    return toa_grid_forecast(context, horizon_len, target_param, hedge=True)


if __name__ == "__main__":
    if "--hedge" in sys.argv:
        sys.argv.remove("--hedge")
        run_cli("PULSAR Classic Baseline 10b: TOA grid fit with slip hedge",
                "TOA Grid Fit (RANSAC, slip-hedged)", "toa_grid_fit_hedged", toa_grid_hedged_forecast)
    else:
        run_cli("PULSAR Classic Baseline 10: TOA grid fit (use --hedge for the slip-hedged forecast)",
                "TOA Grid Fit (RANSAC)", "toa_grid_fit", toa_grid_forecast)
