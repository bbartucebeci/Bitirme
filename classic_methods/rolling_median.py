#!/usr/bin/env python3
"""Method 1: Rolling Median Predictor (with ESM Outlier Rejection Gate).

EE / Signal Processing Rationale:
---------------------------------
In Electronic Support Measures (ESM), a Rolling Median filter (order-statistic L-filter)
is the classic baseline for tracking constant or randomly jittered radar parameters
(e.g., Stable PRI, Jittered PRI, Constant Frequency, Pulse Width).
Unlike a linear Moving Average (FIR low-pass filter), the median is statistically
robust (breakdown point = 50%) against impulsive outliers caused by:
  - Missing pulses (POI < 1.0), which create 2x or 3x PRI spikes in Measured_Delta_TOA.
  - CFAR false alarms and multipath echoes, which split intervals into <0.5x PRI fragments.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

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


def rolling_median_forecast(
    context: np.ndarray,
    horizon_len: int = 32,
    target_param: str = "PRI",
    window_size: int = 32,
    use_gate: bool = True,
) -> np.ndarray:
    """Forecasts future PDW values using a gated rolling median over the context tail.

    Args:
        context: 1D array of observed past PDW values (e.g., 96 pulses).
        horizon_len: Number of future pulses to predict (default: 32).
        target_param: Target PDW parameter name.
        window_size: Sliding window length for the median estimator.
        use_gate: Whether to apply ESM missing/false pulse validation gating for PRI.

    Returns:
        1D array of length `horizon_len` containing predicted values.
    """
    x = np.asarray(context, dtype=np.float64)
    if len(x) == 0:
        return np.zeros(horizon_len, dtype=np.float64)

    if use_gate and target_param.upper() in ["PRI", "MEASURED_DELTA_TOA"]:
        x = clean_pri_context(x)

    tail = x[-window_size:] if len(x) >= window_size else x
    median_val = float(np.median(tail))
    return np.full(horizon_len, median_val, dtype=np.float64)


def main():
    parser = argparse.ArgumentParser(description="PULSAR Classic Baseline 1: Rolling Median Predictor")
    parser.add_argument("--profile-mode", choices=["fixed", "varying"], default="fixed")
    parser.add_argument("--target-param", choices=list(PARAM_SPECS.keys()), default="PRI")
    parser.add_argument("--radar-type", choices=RADAR_TYPES + ["all"], default="all")
    parser.add_argument("--error-level", choices=ERROR_LEVELS + ["all"], default="all")
    parser.add_argument("--window-size", type=int, default=32, help="Rolling median window size (pulses)")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    rtypes = RADAR_TYPES if args.radar_type == "all" else [args.radar_type]
    elevels = ERROR_LEVELS if args.error_level == "all" else [args.error_level]

    predict_fn = lambda ctx, h, p: rolling_median_forecast(
        ctx, horizon_len=h, target_param=p, window_size=args.window_size
    )

    evaluate_method_across_benchmarks(
        method_name=f"Rolling Median (W={args.window_size})",
        method_slug="rolling_median",
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

