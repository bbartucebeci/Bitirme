#!/usr/bin/env python3
"""Method 13: Forecast Combination (error-weighted median of three baselines).

EE / Signal Processing Rationale:
---------------------------------
Combining forecasts of structurally different models is a classic variance-reduction
tool (Bates & Granger, 1969). The members here are the three strongest index-domain
baselines:

    1. Period estimation      (epoch folding + tail phase lock)
    2. Kalman filter bank     (level / trend / periodic state-space models)
    3. ARIMA / seasonal ARIMA (Box-Jenkins)

Weights: each member is scored by its mean absolute one-step-ahead error INSIDE the
context, all three on the same gated sequence and the same pulses (after the first
max_period + 1 samples):

    period estimation - leave-one-out template error: x[n] against the median of the
                        OTHER samples of its phase slot (the value the template would
                        have predicted without seeing x[n]);
    Kalman bank       - prequential innovations of the selected model;
    ARIMA             - one-step prediction errors of the fitted model.

    w_i = 1 / (err_i + eps) ** POWER

Combination: weighted MEDIAN per horizon step, not a weighted mean. With pattern
forecasts the members usually disagree by a whole PRI element (a phase error); a mean
would produce a value that no member and no radar ever emits, whereas the median always
returns one of the members' values and ignores a single outlying member.
"""

from __future__ import annotations

from pathlib import Path
import sys
import warnings
from typing import Dict, Tuple

import numpy as np

warnings.filterwarnings("ignore")

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.arima import fit_best_arima, identify_differencing
from classic_methods.common import clean_pri_context
from classic_methods.kalman_filter import select_model
from classic_methods.period_estimation import estimate_period_and_template
from classic_methods.toa_utils import is_pri_target, run_cli, tuned, weighted_median

# Tuned on the validation split (see tune_robust_methods.py).
WEIGHT_POWER = tuned("forecast_combination.WEIGHT_POWER", 1.0)
WEIGHT_EPS = 1e-3      # us; keeps the weights finite when a member is exact

MEMBERS = ("period_estimation", "kalman", "arima")


def _period_member(x: np.ndarray, horizon_len: int, max_period: int, eval_start: int) -> Tuple[np.ndarray, float]:
    period, template = estimate_period_and_template(x, max_period=max_period)
    n = len(x)
    if period == 1:
        preds = np.full(horizon_len, template[0])
    else:
        tail_len = min(n, max(2 * period, 12))
        tail = x[-tail_len:]
        errs = [float(np.mean(np.abs(tail - template[(np.arange(-tail_len, 0) + s) % period])))
                for s in range(period)]
        shift = int(np.argmin(errs))
        preds = template[(np.arange(horizon_len) + shift) % period]

    # Leave-one-out one-step error of the phase-median template.
    abs_err = []
    for ph in range(period):
        idx = np.arange(ph, n, period)
        vals = x[idx]
        for a, i in enumerate(idx):
            if i < eval_start or len(vals) < 2:
                continue
            abs_err.append(abs(vals[a] - np.median(np.delete(vals, a))))
    err = float(np.mean(abs_err)) if abs_err else np.inf
    return preds, err


def _kalman_member(x: np.ndarray, horizon_len: int, max_period: int) -> Tuple[np.ndarray, float]:
    mean, scale = float(np.mean(x)), float(np.std(x))
    z = (x - mean) / scale
    best = select_model(z, max_period=max_period)
    kind, period, state = best["kind"], best["period"], best["state"]
    h = np.arange(1, horizon_len + 1)
    if kind == "level":
        fz = np.full(horizon_len, float(state))
    elif kind == "trend":
        fz = state[0] + h * state[1]
    else:
        fz = state[(len(z) - 1 + h) % period]
    return fz * scale + mean, float(best["score"]) * scale


def _arima_member(x: np.ndarray, horizon_len: int, max_period: int, eval_start: int) -> Tuple[np.ndarray, float]:
    mean, scale = float(np.mean(x)), float(np.std(x))
    z = (x - mean) / scale
    d, s = identify_differencing(z, max_period=max_period)
    _, res = fit_best_arima(z, d, s)
    if res is None:
        return np.full(horizon_len, float(np.median(x))), np.inf
    preds = np.asarray(res.forecast(horizon_len), dtype=np.float64) * scale + mean
    if not np.all(np.isfinite(preds)):
        return np.full(horizon_len, float(np.median(x))), np.inf
    resid = np.asarray(res.resid, dtype=np.float64)[eval_start:]
    resid = resid[np.isfinite(resid)]
    err = float(np.mean(np.abs(resid))) * scale if len(resid) >= 4 else np.inf
    return preds, err


def member_forecasts(
    context: np.ndarray,
    horizon_len: int = 32,
    target_param: str = "PRI",
    max_period: int = 24,
) -> Dict[str, Tuple[np.ndarray, float]]:
    """Forecast and in-context one-step MAE of every member (on the same gated context)."""
    raw = np.asarray(context, dtype=np.float64)
    x = clean_pri_context(raw) if is_pri_target(target_param) else raw.copy()

    if len(x) < 12 or float(np.std(x)) < 1e-9:
        flat = np.full(horizon_len, float(np.median(x)) if len(x) else 0.0)
        return {m: (flat, 0.0) for m in MEMBERS}

    eval_start = int(min(max_period, max(2, len(x) // 3))) + 1
    return {
        "period_estimation": _period_member(x, horizon_len, max_period, eval_start),
        "kalman": _kalman_member(x, horizon_len, max_period),
        "arima": _arima_member(x, horizon_len, max_period, eval_start),
    }


def combine(members: Dict[str, Tuple[np.ndarray, float]], power: float = WEIGHT_POWER) -> np.ndarray:
    """Weighted median of the member forecasts, weights from the in-context errors."""
    names = [m for m in MEMBERS if np.isfinite(members[m][1])]
    if not names:
        names = list(MEMBERS)
        weights = np.ones(len(names))
    else:
        weights = np.array([1.0 / (members[m][1] + WEIGHT_EPS) ** power for m in names])
    preds = np.vstack([members[m][0] for m in names])
    return np.array([weighted_median(preds[:, h], weights) for h in range(preds.shape[1])])


def combination_forecast(
    context: np.ndarray,
    horizon_len: int = 32,
    target_param: str = "PRI",
    max_period: int = 24,
    power: float = WEIGHT_POWER,
) -> np.ndarray:
    """Forecasts future PDW values with the error-weighted median of the three members."""
    if len(context) == 0:
        return np.zeros(horizon_len, dtype=np.float64)
    return combine(member_forecasts(context, horizon_len, target_param, max_period), power=power)


if __name__ == "__main__":
    run_cli("PULSAR Classic Baseline 13: forecast combination (period estimation + Kalman + ARIMA)",
            "Forecast Combination (weighted median)", "forecast_combination", combination_forecast)
