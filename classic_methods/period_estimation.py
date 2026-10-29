#!/usr/bin/env python3
"""Method 2: Period Estimation & Phase-Locked Template Predictor.

EE / Signal Processing Rationale:
---------------------------------
Periodic and patterned radar PRI modulations (Staggered PRI, Dwell-and-Switch,
Sliding PRI, and Frequency Hopping) exhibit discrete cyclostationary periodicity
in pulse index n:
    y[n] = y[n + P] + w[n]

This script implements a two-stage classic ESM period estimator:
1. Autocorrelation & Phase-Dispersion Analysis (Epoch Folding):
   Evaluates candidate fundamental periods P in [2, P_max]. For each P, folds the
   cleaned context sequence modulo P to extract a robust phase-median waveform
   template mu[0 .. P-1] and computes the unexplained residual dispersion.
   To prevent locking onto integer harmonics (2P, 3P), a parsimony penalty favors
   the smallest fundamental period P* that explains the periodic variance.
2. Tail Phase-Locked Loop (Matched Phase Alignment):
   In noisy ESM channels (error_lv1..3), missing or false pulses early in the
   96-pulse context window can cause cycle slips (phase shifts). By correlating the
   estimated period-P* template against the final 2*P* pulses at the end of the
   context window, the predictor locks onto the instantaneous transmitter phase
   just prior to forecasting the next 32 pulses.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Tuple

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


def estimate_period_and_template(
    x: np.ndarray,
    max_period: int = 24,
) -> Tuple[int, np.ndarray]:
    """Estimates the fundamental discrete period P and phase template from 1D sequence x."""
    n = len(x)
    med_global = float(np.median(x))
    mad_global = float(np.mean(np.abs(x - med_global)))

    # If the signal is nearly flat (e.g., Stable PRI or Constant Frequency), P = 1
    if mad_global < 1e-3 or n < 8:
        return 1, np.array([med_global], dtype=np.float64)

    # Normalized Autocorrelation Function (ACF) for spectral/lag weighting
    x_zero = x - np.mean(x)
    var = float(np.dot(x_zero, x_zero))
    max_p = min(max_period, n // 3)

    best_p = 1
    best_template = np.array([med_global], dtype=np.float64)
    best_score = mad_global  # Baseline L1 residual for P=1 (stationary)

    scores = {}
    templates = {}

    for p in range(2, max_p + 1):
        # Fold sequence modulo p and compute robust median per phase slot
        template = np.zeros(p, dtype=np.float64)
        for phase in range(p):
            template[phase] = np.median(x[phase::p])

        # Reconstruct periodic signal and compute L1 residual + complexity penalty
        tiled = np.tile(template, (n // p) + 1)[:n]
        residual_mae = float(np.mean(np.abs(x - tiled)))

        # Normalized autocorrelation at lag p
        acf_p = float(np.dot(x_zero[:-p], x_zero[p:]) / var) if var > 0 else 0.0

        # Penalize high period numbers slightly to avoid harmonic over-fitting on Gaussian jitter
        dof_penalty = 1.0 + 0.025 * p
        effective_score = residual_mae * dof_penalty

        scores[p] = (effective_score, residual_mae, acf_p)
        templates[p] = template

    # Find candidate period with lowest penalized residual
    cand_p = min(scores.keys(), key=lambda p: scores[p][0])
    cand_eff_score, cand_raw_mae, cand_acf = scores[cand_p]

    # Require substantial variance/MAD reduction (>35%) AND positive autocorrelation
    # so random Gaussian jitter (JitterRadar) is not falsely fitted as periodic!
    if cand_eff_score < 0.65 * mad_global and cand_acf > 0.20:
        # Fundamental divisor check: if a sub-harmonic d | cand_p achieves nearly the same fit,
        # select the fundamental period d instead of its harmonic multiple!
        chosen_p = cand_p
        for d in range(2, cand_p):
            if cand_p % d == 0 and d in scores:
                _, d_raw_mae, d_acf = scores[d]
                if d_raw_mae <= 1.15 * cand_raw_mae and d_acf > 0.25:
                    chosen_p = d
                    break
        best_p = chosen_p
        best_template = templates[best_p]

    return best_p, best_template


def period_estimation_forecast(
    context: np.ndarray,
    horizon_len: int = 32,
    target_param: str = "PRI",
    max_period: int = 24,
) -> np.ndarray:
    """Forecasts future PDW values via Period Estimation + Tail Phase-Locking."""
    raw = np.asarray(context, dtype=np.float64)
    if len(raw) == 0:
        return np.zeros(horizon_len, dtype=np.float64)

    if target_param.upper() in ["PRI", "MEASURED_DELTA_TOA"]:
        x = clean_pri_context(raw)
    else:
        x = raw.copy()

    period, template = estimate_period_and_template(x, max_period=max_period)

    if period == 1:
        return np.full(horizon_len, template[0], dtype=np.float64)

    # Tail Phase-Locked Loop (PLL): align template phase to the end of the context window
    # to recover from any earlier missing/false pulse phase slip.
    tail_len = min(len(x), max(2 * period, 12))
    tail = x[-tail_len:]

    best_shift = 0
    best_tail_err = float("inf")
    for shift in range(period):
        # Under shift, the next sample after tail[-1] has phase `shift`
        idx = (np.arange(-tail_len, 0) + shift) % period
        aligned_template = template[idx]
        err = float(np.mean(np.abs(tail - aligned_template)))
        if err < best_tail_err:
            best_tail_err = err
            best_shift = shift

    future_phases = (np.arange(horizon_len) + best_shift) % period
    return template[future_phases]


def main():
    parser = argparse.ArgumentParser(description="PULSAR Classic Baseline 2: Period Estimation Predictor")
    parser.add_argument("--profile-mode", choices=["fixed", "varying"], default="fixed")
    parser.add_argument("--target-param", choices=list(PARAM_SPECS.keys()), default="PRI")
    parser.add_argument("--radar-type", choices=RADAR_TYPES + ["all"], default="all")
    parser.add_argument("--error-level", choices=ERROR_LEVELS + ["all"], default="all")
    parser.add_argument("--max-period", type=int, default=24, help="Maximum candidate period length (pulses)")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    rtypes = RADAR_TYPES if args.radar_type == "all" else [args.radar_type]
    elevels = ERROR_LEVELS if args.error_level == "all" else [args.error_level]

    predict_fn = lambda ctx, h, p: period_estimation_forecast(
        ctx, horizon_len=h, target_param=p, max_period=args.max_period
    )

    evaluate_method_across_benchmarks(
        method_name=f"Period Estimation (P_max={args.max_period})",
        method_slug="period_estimation",
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

