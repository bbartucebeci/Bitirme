#!/usr/bin/env python3
"""Method 5: Exponential Smoothing (SES / Holt / Holt-Winters with Automatic Selection).

EE / Signal Processing Rationale:
---------------------------------
Exponential smoothing is a family of recursive first-order IIR smoothers. Simple
Exponential Smoothing (SES) is the steady-state Kalman filter of the local-level model:

    l[n] = alpha * y[n] + (1 - alpha) * l[n-1],       y_hat[n+h] = l[n]

and the Holt / Holt-Winters extensions add slope and seasonal recursions:

    Level:     l[n] = alpha * (y[n] - s[n-S]) + (1 - alpha) * (l[n-1] + phi * b[n-1])
    Trend:     b[n] = beta  * (l[n] - l[n-1]) + (1 - beta) * phi * b[n-1]
    Season:    s[n] = gamma * (y[n] - l[n])  + (1 - gamma) * s[n-S]

Mapping to radar PRI laws:
  - SES                      -> Stable PRI, Jittered PRI (alpha small = long averaging)
  - Holt, damped trend (phi) -> slowly drifting PRI
  - Holt-Winters, additive   -> Staggered PRI (S = number of stagger positions),
    season S                    Dwell-and-Switch (S = full dwell cycle),
                                Sliding PRI (S = pulses per ramp; sawtooth = season)

Procedure per context window:
  1. ESM front-end gating (clean_pri_context), shared with all classic baselines.
  2. Candidate season lengths S from the ACF (seasonality.seasonal_candidates).
  3. Fit SES, damped Holt, and additive Holt-Winters for each candidate S by maximum
     likelihood (statsmodels), with estimated initial states.
  4. Select the model with the lowest AICc (corrected Akaike Information Criterion),
     the standard ETS selection rule, and forecast the 32-pulse horizon.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import warnings
from typing import List, Tuple

import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

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
from classic_methods.seasonality import seasonal_candidates


def _candidate_specs(x: np.ndarray, max_period: int) -> List[Tuple[str, dict]]:
    specs = [
        ("SES", {}),
        ("Holt (damped)", {"trend": "add", "damped_trend": True}),
    ]
    for s in seasonal_candidates(x, max_period=max_period):
        specs.append((f"Holt-Winters (S={s})", {"seasonal": "add", "seasonal_periods": s}))
    return specs


def fit_best_ets(x: np.ndarray, max_period: int = 24):
    """Fits all candidate ETS models and returns (label, fitted_result) with lowest AICc."""
    best_label, best_res, best_aicc = None, None, np.inf
    for label, kw in _candidate_specs(x, max_period):
        try:
            res = ExponentialSmoothing(x, initialization_method="estimated", **kw).fit()
        except Exception:
            continue
        aicc = float(res.aicc)
        if np.isfinite(aicc) and aicc < best_aicc:
            best_label, best_res, best_aicc = label, res, aicc
    return best_label, best_res


def exponential_smoothing_forecast(
    context: np.ndarray,
    horizon_len: int = 32,
    target_param: str = "PRI",
    max_period: int = 24,
    use_gate: bool = True,
) -> np.ndarray:
    """Forecasts future PDW values with the AICc-selected exponential smoothing model."""
    raw = np.asarray(context, dtype=np.float64)
    if len(raw) == 0:
        return np.zeros(horizon_len, dtype=np.float64)

    if use_gate and target_param.upper() in ["PRI", "MEASURED_DELTA_TOA"]:
        x = clean_pri_context(raw)
    else:
        x = raw.copy()

    # Degenerate (constant) context, e.g. clean Stable PRI: every smoother returns the level.
    if len(x) < 8 or float(np.std(x)) < 1e-9:
        return np.full(horizon_len, float(np.median(x)), dtype=np.float64)

    _, res = fit_best_ets(x, max_period=max_period)
    if res is None:
        return np.full(horizon_len, float(np.median(x)), dtype=np.float64)

    preds = np.asarray(res.forecast(horizon_len), dtype=np.float64)
    if not np.all(np.isfinite(preds)):
        return np.full(horizon_len, float(np.median(x)), dtype=np.float64)
    return preds


def main():
    parser = argparse.ArgumentParser(description="PULSAR Classic Baseline 5: Exponential Smoothing Predictor")
    parser.add_argument("--profile-mode", choices=["fixed", "varying"], default="fixed")
    parser.add_argument("--target-param", choices=list(PARAM_SPECS.keys()), default="PRI")
    parser.add_argument("--radar-type", choices=RADAR_TYPES + ["all"], default="all")
    parser.add_argument("--error-level", choices=ERROR_LEVELS + ["all"], default="all")
    parser.add_argument("--max-period", type=int, default=24, help="Largest Holt-Winters season length (pulses)")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    rtypes = RADAR_TYPES if args.radar_type == "all" else [args.radar_type]
    elevels = ERROR_LEVELS if args.error_level == "all" else [args.error_level]

    predict_fn = lambda ctx, h, p: exponential_smoothing_forecast(
        ctx, horizon_len=h, target_param=p, max_period=args.max_period
    )

    evaluate_method_across_benchmarks(
        method_name="Exponential Smoothing (AICc-selected ETS)",
        method_slug="exponential_smoothing",
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
