#!/usr/bin/env python3
"""Method 3: Hidden Markov Model (Gaussian HMM with Baum-Welch EM & Viterbi Decoding).

EE / Signal Processing Rationale:
---------------------------------
Modern multifunction radars (e.g., Staggered MTI radars and Phased-Array Dwell-and-Switch
radars) operate as finite-state machines where the transmitter switches between discrete
waveform states s_t in {0, 1, ..., K-1}. Each hidden state k emits pulse parameters from
a Gaussian distribution N(mu_k, sigma_k^2) and evolves according to a Markov transition
matrix A_ij = P(s_t = j | s_{t-1} = i).

This script implements a Gaussian Hidden Markov Model (HMM) predictor:
1. Model Order Selection via BIC (Bayesian Information Criterion):
   Fits candidate Gaussian HMMs across K in {1, 2, 3, 4, 6} states using Baum-Welch
   Expectation-Maximization (EM) initialized with k-means/quantile clustering, and selects
   the optimal number of hidden states K* via BIC.
2. Viterbi State Decoding & Semi-Markov Run-Length Tracking:
   Applies the Viterbi algorithm to decode the optimal hidden state sequence s_{0..T-1}
   over the context window. From the Viterbi path, it extracts both the active terminal
   state s_{T-1}, the dominant state transition cycle, and the empirical state dwell
   duration (how many consecutive pulses the radar stays in state k before switching),
   projecting the discrete state trajectory forward over the 32-pulse horizon.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import logging
import sys
import warnings
from typing import Tuple

import numpy as np
from hmmlearn.hmm import GaussianHMM

warnings.filterwarnings("ignore")
logging.getLogger("hmmlearn").setLevel(logging.ERROR)

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


def _fit_gaussian_hmm_bic(
    x: np.ndarray,
    candidate_states: Tuple[int, ...] = (1, 2, 3, 4, 6),
) -> Tuple[GaussianHMM, np.ndarray]:
    """Fits Gaussian HMMs with Baum-Welch EM and selects K* minimizing BIC."""
    n = len(x)
    obs = x.reshape(-1, 1)

    # Check if signal has negligible variance (e.g., clean Stable PRI)
    std_val = float(np.std(x))
    if std_val < 1e-2 or n < 12:
        model = GaussianHMM(n_components=1, covariance_type="diag", n_iter=10, random_state=42)
        # Add tiny jitter if completely constant so covariance is positive-definite
        obs_safe = obs + np.random.default_rng(42).normal(0, 1e-4, size=obs.shape)
        model.fit(obs_safe)
        model.means_[0, 0] = float(np.median(x))
        return model, np.zeros(n, dtype=int)

    best_bic = float("inf")
    best_model = None
    best_states = np.zeros(n, dtype=int)

    for k in candidate_states:
        if n < 4 * k:
            continue
        try:
            model = GaussianHMM(
                n_components=k,
                covariance_type="diag",
                n_iter=40,
                tol=1e-3,
                random_state=42,
                init_params="stc",
                min_covar=max(1e-3, (0.01 * std_val) ** 2),
            )
            # Initialize means uniformly across empirical quantiles for fast, deterministic EM convergence
            quantiles = np.linspace(100.0 / (2 * k), 100.0 * (1.0 - 1.0 / (2 * k)), k)
            model.means_ = np.percentile(x, quantiles).reshape(k, 1)
            model.fit(obs)

            log_likelihood = float(model.score(obs))
            # Number of free parameters in a K-state 1D diagonal Gaussian HMM:
            # (K - 1) startprob + K*(K - 1) transmat + K means + K variances = K^2 + 2K - 1
            num_params = (k * k) + (2 * k) - 1
            # Penalize extra states so uncorrelated Gaussian jitter stays at K=1
            bic = -2.0 * log_likelihood + num_params * np.log(n) * 2.2

            if bic < best_bic:
                best_bic = bic
                best_model = model
                best_states = model.predict(obs)
        except Exception:
            continue

    if best_model is None:
        best_model = GaussianHMM(n_components=1, covariance_type="diag", n_iter=10, random_state=42)
        obs_safe = obs + np.random.default_rng(42).normal(0, 1e-4, size=obs.shape)
        best_model.fit(obs_safe)
        best_model.means_[0, 0] = float(np.median(x))
        best_states = np.zeros(n, dtype=int)

    return best_model, best_states


def _extrapolate_viterbi_states(
    states: np.ndarray,
    transmat: np.ndarray,
    means: np.ndarray,
    horizon_len: int,
) -> np.ndarray:
    """Projects decoded Viterbi states forward over `horizon_len` steps.

    Handles both:
    - Fast pulse-to-pulse switching (Staggered PRI, where dwell length = 1)
    - Burst dwell switching (Dwell-and-Switch PRI, where dwell length = K pulses per state)
    """
    k_num = len(means)
    if k_num == 1 or len(states) == 0:
        return np.full(horizon_len, float(means[0]), dtype=np.float64)

    # Extract run-length encoding of the Viterbi state sequence: [(state, run_len), ...]
    runs = []
    cur_s = int(states[0])
    cur_len = 1
    for s in states[1:]:
        s_int = int(s)
        if s_int == cur_s:
            cur_len += 1
        else:
            runs.append((cur_s, cur_len))
            cur_s = s_int
            cur_len = 1
    runs.append((cur_s, cur_len))

    # Estimate typical dwell duration per state (excluding the first and last potentially truncated runs)
    interior_runs = runs[1:-1] if len(runs) > 2 else runs
    dwell_per_state = {}
    for s_idx in range(k_num):
        s_lengths = [r_len for (r_s, r_len) in interior_runs if r_s == s_idx]
        if s_lengths:
            dwell_per_state[s_idx] = max(1, int(np.round(np.median(s_lengths))))
        else:
            # Fallback to expected geometric dwell 1 / (1 - A_ii)
            a_ii = float(np.clip(transmat[s_idx, s_idx], 0.0, 0.95))
            dwell_per_state[s_idx] = max(1, int(np.round(1.0 / (1.0 - a_ii))))

    # Build off-diagonal transition matrix (which state to jump to when a dwell finishes)
    next_state_map = {}
    for s_idx in range(k_num):
        row = transmat[s_idx].copy()
        if k_num > 1:
            row[s_idx] = -1.0  # Force transition to a distinct state at the end of a dwell
        next_s = int(np.argmax(row))
        # Also check empirical run transitions for higher robustness
        emp_next = [runs[i + 1][0] for i in range(len(runs) - 1) if runs[i][0] == s_idx]
        if emp_next:
            vals, counts = np.unique(emp_next, return_counts=True)
            next_s = int(vals[np.argmax(counts)])
        next_state_map[s_idx] = next_s

    # Current state and how many pulses it has already dwelled at the end of context
    active_state, active_elapsed = runs[-1]
    preds = np.zeros(horizon_len, dtype=np.float64)

    for h in range(horizon_len):
        target_dwell = dwell_per_state.get(active_state, 1)
        if active_elapsed >= target_dwell:
            active_state = next_state_map[active_state]
            active_elapsed = 0
        preds[h] = float(means[active_state])
        active_elapsed += 1

    return preds


def hmm_forecast(
    context: np.ndarray,
    horizon_len: int = 32,
    target_param: str = "PRI",
) -> np.ndarray:
    """Forecasts future PDW values using a Baum-Welch Gaussian HMM + Viterbi decoder."""
    raw = np.asarray(context, dtype=np.float64)
    if len(raw) == 0:
        return np.zeros(horizon_len, dtype=np.float64)

    if target_param.upper() in ["PRI", "MEASURED_DELTA_TOA"]:
        x = clean_pri_context(raw)
    else:
        x = raw.copy()

    # Check if uncorrelated Gaussian jitter around a constant mean before fitting multi-state HMM
    x_zero = x - np.mean(x)
    var = float(np.dot(x_zero, x_zero))
    max_acf = 0.0
    if var > 1e-6 and len(x) > 6:
        acfs = [abs(float(np.dot(x_zero[:-lag], x_zero[lag:]) / var)) for lag in range(1, min(17, len(x) // 2))]
        max_acf = max(acfs) if acfs else 0.0

    # If consecutive pulses have near-zero temporal structure (white noise / JitterRadar),
    # a 1-state stationary emission model is Bayes-optimal
    if max_acf < 0.22:
        return np.full(horizon_len, float(np.median(x)), dtype=np.float64)

    model, viterbi_states = _fit_gaussian_hmm_bic(x, candidate_states=(1, 2, 3, 4, 6))
    means = model.means_.squeeze(-1)

    # Refine each state's emission level with the robust median of pulses assigned to that state
    for k in range(model.n_components):
        mask_k = viterbi_states == k
        if np.any(mask_k):
            means[k] = float(np.median(x[mask_k]))

    return _extrapolate_viterbi_states(
        states=viterbi_states,
        transmat=model.transmat_,
        means=means,
        horizon_len=horizon_len,
    )


def main():
    parser = argparse.ArgumentParser(description="PULSAR Classic Baseline 3: Hidden Markov Model Predictor")
    parser.add_argument("--profile-mode", choices=["fixed", "varying"], default="fixed")
    parser.add_argument("--target-param", choices=list(PARAM_SPECS.keys()), default="PRI")
    parser.add_argument("--radar-type", choices=RADAR_TYPES + ["all"], default="all")
    parser.add_argument("--error-level", choices=ERROR_LEVELS + ["all"], default="all")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    rtypes = RADAR_TYPES if args.radar_type == "all" else [args.radar_type]
    elevels = ERROR_LEVELS if args.error_level == "all" else [args.error_level]

    predict_fn = lambda ctx, h, p: hmm_forecast(ctx, horizon_len=h, target_param=p)

    evaluate_method_across_benchmarks(
        method_name="Hidden Markov Model (Baum-Welch + Viterbi)",
        method_slug="hidden_markov_model",
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

