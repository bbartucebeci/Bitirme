#!/usr/bin/env python3
"""Principled 1st-Order Discrete-State Optimized Hidden Markov Model (Gaussian HMM).

Fixes the implementation defects of the baseline HMM on discrete-state Markov and
semi-Markov radar laws (`dwell_and_switch`, `markov_agile`, `stable`, `jitter`)
while preserving the true 1st-order low-state-count (K <= 6) model boundary so that
comparisons against time-series foundation models remain honest and faithful:

1. Candidate state counts K in {1, 2, 3, 4, 5, 6} (restores K=5 for 5-level dwell-and-switch).
2. 1D K-Medians cluster refinement + local within-cluster variance initialization
   (`init_params="st"`) to avoid global-variance EM collapse on adjacent PRI levels.
3. White-noise ACF gate lowered from 0.22 to 0.15 so stochastic `markov_agile`
   (theoretical lag-1 ACF ~0.216) enters the K=4 HMM while `jitter` still bypasses EM.
4. Probabilistic forward state-distribution rollout (p_{T+h} = p_T A^h) for pulse-to-pulse
   stochastic Markov chains (majority state when max_j p >= 0.50, posterior expectation
   after mixing) instead of greedy deterministic cycle rollout.
5. Isolated 1-pulse Viterbi despiking + raised geometric dwell fallback cap (0.985 -> 67
   pulses) for multi-pulse burst-dwell semi-Markov laws (`dwell_and_switch`).
"""

from __future__ import annotations

import logging
from pathlib import Path
import sys
from typing import Tuple
import warnings

import numpy as np
from hmmlearn.hmm import GaussianHMM

warnings.filterwarnings("ignore")
logging.getLogger("hmmlearn").setLevel(logging.ERROR)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.common import clean_pri_context


def _kmeans_1d_init(x: np.ndarray, k: int, min_covar: float, n_iters: int = 15) -> Tuple[np.ndarray, np.ndarray]:
    """Refines quantile centers via 1D K-Medians and computes local cluster variances."""
    obs = x.reshape(-1, 1)
    quantiles = np.linspace(100.0 / (2 * k), 100.0 * (1.0 - 1.0 / (2 * k)), k)
    centers = np.percentile(x, quantiles)

    for _ in range(n_iters):
        labels = np.argmin(np.abs(obs - centers.reshape(1, k)), axis=1)
        new_centers = np.array(
            [float(np.median(x[labels == c])) if np.any(labels == c) else float(centers[c]) for c in range(k)],
            dtype=np.float64,
        )
        if np.allclose(new_centers, centers, atol=1e-4):
            centers = new_centers
            break
        centers = new_centers

    labels = np.argmin(np.abs(obs - centers.reshape(1, k)), axis=1)
    covars = np.array(
        [
            max(min_covar, float(np.var(x[labels == c])) if int(np.sum(labels == c)) > 1 else min_covar)
            for c in range(k)
        ],
        dtype=np.float64,
    )
    return centers.reshape(k, 1), covars.reshape(k, 1)


def _fit_optimized_gaussian_hmm_bic(
    x: np.ndarray,
    candidate_states: Tuple[int, ...] = (1, 2, 3, 4, 5, 6),
) -> Tuple[GaussianHMM, np.ndarray]:
    """Fits Gaussian HMMs with local-variance K-Medians init and selects K* via BIC."""
    n = len(x)
    obs = x.reshape(-1, 1)

    std_val = float(np.std(x))
    if std_val < 1e-2 or n < 12:
        model = GaussianHMM(n_components=1, covariance_type="diag", n_iter=10, random_state=42)
        obs_safe = obs + np.random.default_rng(42).normal(0, 1e-4, size=obs.shape)
        model.fit(obs_safe)
        model.means_[0, 0] = float(np.median(x))
        return model, np.zeros(n, dtype=int)

    min_covar = max(1e-3, (0.01 * std_val) ** 2)
    best_bic = float("inf")
    best_model = None
    best_states = np.zeros(n, dtype=int)

    for k in candidate_states:
        if n < 4 * k:
            continue
        try:
            if k == 1:
                model = GaussianHMM(
                    n_components=1,
                    covariance_type="diag",
                    n_iter=20,
                    tol=1e-3,
                    random_state=42,
                    init_params="stc",
                    min_covar=min_covar,
                )
                model.means_ = np.array([[float(np.median(x))]], dtype=np.float64)
            else:
                means_init, covars_init = _kmeans_1d_init(x, k, min_covar=min_covar)
                model = GaussianHMM(
                    n_components=k,
                    covariance_type="diag",
                    n_iter=40,
                    tol=1e-3,
                    random_state=42,
                    init_params="st",
                    min_covar=min_covar,
                )
                model.means_ = means_init
                model.covars_ = covars_init

            model.fit(obs)
            log_likelihood = float(model.score(obs))
            num_params = (k * k) + (2 * k) - 1
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


def _run_length_encode(states: np.ndarray) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    if len(states) == 0:
        return runs
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
    return runs


def _despike_isolated_glitches(states: np.ndarray) -> np.ndarray:
    """Removes isolated 1-pulse Viterbi state glitches inside multi-pulse dwells."""
    if len(states) < 3:
        return states
    cleaned = states.copy()
    for i in range(1, len(cleaned) - 1):
        if cleaned[i - 1] == cleaned[i + 1] and cleaned[i] != cleaned[i - 1]:
            cleaned[i] = cleaned[i - 1]
    return cleaned


def _extrapolate_optimized(
    model: GaussianHMM,
    obs: np.ndarray,
    states: np.ndarray,
    means: np.ndarray,
    horizon_len: int,
) -> np.ndarray:
    """Chooses probabilistic forward distribution rollout vs semi-Markov dwell rollout."""
    k_num = len(means)
    if k_num == 1 or len(states) == 0:
        return np.full(horizon_len, float(means[0]), dtype=np.float64)

    raw_runs = _run_length_encode(states)
    median_raw_run = float(np.median([r_len for _, r_len in raw_runs]))

    # Build smoothed transition matrix combining empirical Viterbi transitions & EM transmat.
    emp_counts = np.full((k_num, k_num), 1e-3, dtype=np.float64)
    for t in range(len(states) - 1):
        emp_counts[int(states[t]), int(states[t + 1])] += 1.0
    a_emp = emp_counts / emp_counts.sum(axis=1, keepdims=True)
    a_em = np.asarray(model.transmat_, dtype=np.float64)
    a_mix = 0.5 * a_emp + 0.5 * a_em
    a_mix /= np.maximum(a_mix.sum(axis=1, keepdims=True), 1e-12)

    # Pulse-to-pulse stochastic Markov chain (e.g., markov_agile): propagate p_{T+h} = p_T A^h.
    if median_raw_run <= 2.0 and float(np.max(a_mix)) < 0.90:
        try:
            post = np.asarray(model.predict_proba(obs)[-1], dtype=np.float64)
            if not np.isfinite(post).all() or post.sum() <= 0:
                raise ValueError("Invalid posterior")
            post /= post.sum()
        except Exception:
            post = np.zeros(k_num, dtype=np.float64)
            post[int(states[-1])] = 1.0

        preds = np.zeros(horizon_len, dtype=np.float64)
        for h in range(horizon_len):
            post = post @ a_mix
            post /= np.maximum(post.sum(), 1e-12)
            if float(np.max(post)) >= 0.50:
                preds[h] = float(means[int(np.argmax(post))])
            else:
                preds[h] = float(np.dot(post, means))
        return preds

    # Semi-Markov burst-dwell / deterministic FSM rollout (e.g., dwell_and_switch).
    dwell_states = _despike_isolated_glitches(states) if median_raw_run > 2.0 else states
    runs = _run_length_encode(dwell_states)
    interior_runs = runs[1:-1] if len(runs) > 2 else runs

    dwell_per_state: dict[int, int] = {}
    for s_idx in range(k_num):
        s_lengths = [r_len for (r_s, r_len) in interior_runs if r_s == s_idx]
        if s_lengths:
            dwell_per_state[s_idx] = max(1, int(np.round(np.median(s_lengths))))
        else:
            # Cap at 0.985 (~67 pulses) so 32/48/64-pulse dwells are not truncated at 20.
            a_ii = float(np.clip(a_em[s_idx, s_idx], 0.0, 0.985))
            dwell_per_state[s_idx] = max(1, int(np.round(1.0 / (1.0 - a_ii))))

    next_state_map: dict[int, int] = {}
    for s_idx in range(k_num):
        row = a_em[s_idx].copy()
        row[s_idx] = -1.0
        next_s = int(np.argmax(row))
        emp_next = [runs[i + 1][0] for i in range(len(runs) - 1) if runs[i][0] == s_idx]
        if emp_next:
            vals, counts = np.unique(emp_next, return_counts=True)
            next_s = int(vals[np.argmax(counts)])
        next_state_map[s_idx] = next_s

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


def optimized_hmm_forecast(
    context: np.ndarray,
    horizon_len: int = 32,
    target_param: str = "PRI",
) -> np.ndarray:
    """Forecasts future PDW values using the principled 1st-order optimized Gaussian HMM."""
    raw = np.asarray(context, dtype=np.float64)
    if len(raw) == 0:
        return np.zeros(horizon_len, dtype=np.float64)

    if target_param.upper() in ["PRI", "MEASURED_DELTA_TOA"]:
        x = clean_pri_context(raw)
    else:
        x = raw.copy()

    x_zero = x - np.mean(x)
    var = float(np.dot(x_zero, x_zero))
    max_acf = 0.0
    if var > 1e-6 and len(x) > 6:
        acfs = [abs(float(np.dot(x_zero[:-lag], x_zero[lag:]) / var)) for lag in range(1, min(17, len(x) // 2))]
        max_acf = max(acfs) if acfs else 0.0

    # Lowered from 0.22 to 0.15 so stochastic markov_agile (~0.216) enters the K=4 HMM.
    if max_acf < 0.15:
        return np.full(horizon_len, float(np.median(x)), dtype=np.float64)

    model, viterbi_states = _fit_optimized_gaussian_hmm_bic(x, candidate_states=(1, 2, 3, 4, 5, 6))
    means = np.asarray(model.means_, dtype=np.float64).reshape(-1).copy()

    for k in range(model.n_components):
        mask_k = viterbi_states == k
        if np.any(mask_k):
            means[k] = float(np.median(x[mask_k]))

    return _extrapolate_optimized(
        model=model,
        obs=x.reshape(-1, 1),
        states=viterbi_states,
        means=means,
        horizon_len=horizon_len,
    )
