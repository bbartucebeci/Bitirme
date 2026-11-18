# `hmm_new_complex_pri`: Baseline & Optimized 1st-Order HMM Benchmark on `new_complex_pri` (`1000x1056`)

> **Read the full plain-English & technical walkthrough first:** [`00_HMM_EXPLAINED_FOR_EVERYONE.md`](00_HMM_EXPLAINED_FOR_EVERYONE.md)

This directory isolates all scripts, evaluations, and figures for benchmarking the **Hidden Markov Model (HMM)** on the `new_complex_pri` (`1000x1056`, `consecutive_future_v2`, `window_mode=boundary`, $C=1024, H=32$, $L \in \{96, 256, 512, 992\}$) dataset without modifying any original repository files.

## Quick Summary

- **Scale:** 2 profiles (`fixed`, `varying`) $\times$ 8 radar types $\times$ 8 error levels (`clean`..`error_lv7`) $\times$ 4 context lengths $\times$ 200 test sequences = **102,400 forecasts per model** (verified byte-identical against all 25,600 reference test CSV SHA256 hashes in `test_windows.json`).
- **Baseline HMM ([`results_baseline_hmm/`](results_baseline_hmm/)):** Evaluates the original `classic_methods/hidden_markov_model.py` (`K ∈ {1,2,3,4,6}`, `0.22` ACF gate, greedy mode rollout). Beats Chronos-2 Zero-Shot on **176 / 512 (34.4%)** conditions.
- **Optimized 1st-Order HMM ([`optimized_hmm.py`](optimized_hmm.py) & [`results_optimized_hmm/`](results_optimized_hmm/)):** Preserves the honest **1st-order $K \le 6$ HMM boundary** (without adding high-order/waveform hacks for `stagger`, `sinusoidal`, or `triangular_sliding`), fixing only the discrete-state Markov/semi-Markov defects:
  1. Adds $K=5$ (`K ∈ {1,2,3,4,5,6}`) + 1D K-Medians local-variance initialization (`init_params="st"`) for 5-level `dwell_and_switch` (**0.000 µs** clean MAE, **43 / 64** wins vs. Chronos-2).
  2. Lowers the ACF gate (`0.22 -> 0.15`) + uses probabilistic forward distribution rollout ($p_{T+h} = p_T A^h$) for `markov_agile` (**98.3–98.9 µs** Bayes floor, **60 / 64** wins vs. Chronos-2).
  3. Adds 1-pulse Viterbi despiking + `0.985` dwell cap for multi-pulse burst-dwell laws.
  - Beats Chronos-2 Zero-Shot on **268 / 512 (52.3%)** conditions while faithfully demonstrating why 1st-order $K \le 6$ HMMs still fail on 32-level `stagger` (`164–167 µs`), `sinusoidal` (`112–114 µs`), and `triangular_sliding` (`97 µs`)—establishing the motivation for Time-Series Foundation Models and FPGA Knowledge Distillation in `PULSAR.md`.

## Key Links

- **Plain-English & Technical Guide:** [`00_HMM_EXPLAINED_FOR_EVERYONE.md`](00_HMM_EXPLAINED_FOR_EVERYONE.md)
- **3-Way Benchmark Report (Baseline HMM vs. Optimized HMM vs. Chronos-2):** [`results_optimized_hmm/Baseline_vs_Optimized_HMM_vs_Chronos2.md`](results_optimized_hmm/Baseline_vs_Optimized_HMM_vs_Chronos2.md)
- **3-Way Visual Plots (`L=992`):**
  - [`results_optimized_hmm/plots/baseline_vs_optimized_vs_chronos2_fixed_L992.png`](results_optimized_hmm/plots/baseline_vs_optimized_vs_chronos2_fixed_L992.png)
  - [`results_optimized_hmm/plots/baseline_vs_optimized_vs_chronos2_varying_L992.png`](results_optimized_hmm/plots/baseline_vs_optimized_vs_chronos2_varying_L992.png)
- **Baseline HMM Tables & Paired Stats:** [`results_baseline_hmm/MAE_comparison.md`](results_baseline_hmm/MAE_comparison.md) · [`results_baseline_hmm/HMM_vs_Chronos2_PRI_comparison.md`](results_baseline_hmm/HMM_vs_Chronos2_PRI_comparison.md)
- **Optimized HMM Tables:** [`results_optimized_hmm/MAE_comparison.md`](results_optimized_hmm/MAE_comparison.md) · [`results_optimized_hmm/HitRate_and_RMSE_tables.md`](results_optimized_hmm/HitRate_and_RMSE_tables.md)
