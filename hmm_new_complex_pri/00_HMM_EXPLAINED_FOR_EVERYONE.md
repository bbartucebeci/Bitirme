# Hidden Markov Model (HMM) on `new_complex_pri`: Complete Plain-English & Technical Guide

> **Start here before opening `results_baseline_hmm/` or `results_optimized_hmm/`!**
> This guide explains—in plain language first, then with exact mathematical details—what this folder is, how the **Old Baseline HMM** works, why we created an **Optimized 1st-Order HMM**, why certain radar types *still* fail on purpose, and how everything fits into the **PULSAR** FPGA project goal.

---

## 1. What Are We Predicting? (For Anyone New to the Project)

Imagine listening to a radar with an electronic sensor (an ESM receiver). Every time the radar emits a pulse, the sensor timestamps when it arrived (**TOA**). The gap between two consecutive pulses is called the **PRI (Pulse Repetition Interval)**—the radar's heartbeat, measured in microseconds ($\mu\text{s}$).

In this new dataset (`new_complex_pri`, `1000x1056`):
- We observe **1,024 intervals** from the past (we test giving the model the last $L \in \{96, 256, 512, 992\}$ pulses).
- Sometimes our receiver **misses pulses** (up to **~25.4% missing pulses** at `error_lv7`). When one pulse is missed, the observed gap looks twice as long ($2\times \text{PRI}$); when two are missed, it looks three times as long ($3\times \text{PRI}$).
- Our goal is to predict the **exact next 32 consecutive transmitted pulses** ($H = 32$) without missing pulses in the target.

There are **8 different radar heartbeat patterns** (under both **Fixed** settings and **Varying** randomized settings) and **8 noise/loss levels** (`clean` and `error_lv1` to `error_lv7`):

| Radar Type | Simple Real-World Analogy | Should a Simple 1st-Order HMM ($K \le 6$) Work Here? |
|---|---|---|
| **1. `stable`** | A metronome ticking at an exact steady beat (e.g., `1000 µs`). | **Yes** (1 state). |
| **2. `jitter`** | A metronome with random human timing wobble ($\pm 4\text{–}8\%$) around a center beat. | **Yes** (predicting the average/median is mathematically optimal). |
| **3. `dwell_and_switch`** | A drumbeat playing **32–64 beats at speed A**, then switching to **32–64 beats at speed B**, cycling through **5 discrete speeds**. | **Yes** (classic finite-state machine with 5 states). |
| **4. `markov_agile`** | A weighted roulette wheel with **4 speeds**: 70% chance of stepping to the next speed, 10% chance of jumping to any other speed. | **Yes — on average/expected error** (exact 4-state Markov chain!). |
| **5. `stagger`** | A secret **16-to-32 step repeating passcode** of wildly different intervals every single pulse. | **No** (a 6-state model literally doesn't have enough memory slots for 32 levels). |
| **6. `sliding`** | Steadily speeding up like a car revving from 1st gear to top gear (12–20 levels), then snapping back. | **Only coarsely** (a 6-state staircase approximates a 16-step ramp imperfectly). |
| **7. `triangular_sliding`** | Walking **up** a staircase (10 steps) and walking back **down** (10 steps). | **No** (1st-order "Elevator Problem"—see Section 3!). |
| **8. `sinusoidal`** | Smoothly swinging back and forth like a pendulum with a non-integer cycle ($T \approx 7.24$ pulses). | **No** (continuous values + up/down ambiguity). |

---

## 2. How the Old Baseline HMM (`results_baseline_hmm/`) Works

The original code (`classic_methods/hidden_markov_model.py`, left untouched in the repo) runs a 4-stage pipeline on each sequence individually (no training dataset used):

1. **Front-End Gap Cleaner (`clean_pri_context`):**
   Looks for sudden jumps around $2\times$ or $3\times$ the typical PRI (caused by missed pulses) and splits them evenly into 2 or 3 normal intervals. This restores missing pulse counts remarkably well (**99.9%** accurate up to `error_lv5` and **94.85%** even at `error_lv7`).
2. **White-Noise Shortcut (`max|ACF| < 0.22`):**
   Checks if the pulse sequence has almost zero correlation with its own recent past. If so, it assumes pure random `jitter` and returns the sequence median.
3. **Fitting a Gaussian HMM with $K \in \{1, 2, 3, 4, 6\}$ States:**
   Tries grouping the observed PRI values into $1, 2, 3, 4,$ or $6$ bell-curve buckets (states) using Baum-Welch Expectation-Maximization (EM), and picks the best $K$ using a strict BIC penalty ($2.2\times$).
4. **Greedy Mode-Path Extrapolation (`_extrapolate_viterbi_states`):**
   Decodes which state the radar was in at every past pulse (Viterbi), measures how many pulses the radar stays in each state, picks the **single most common next state**, and marches deterministically down that one path for 32 pulses.

---

## 3. Why the Baseline HMM Failed (Expected Limits vs. Real Bugs)

When we ran the Baseline HMM across all **512 conditions** ($102{,}400$ test forecasts), it won **176 / 512** conditions against Google/Amazon's **Chronos-2** foundation model, while Chronos-2 won **336 / 512**. Looking closely, there were **two completely different kinds of failure**:

### A. Theoretical Limits (Where an HMM *Should* Fail)
1. **Not Enough States for `stagger` (6 slots vs. 32 levels):**
   On the old `1000x128` dataset, `stagger` only had 3 levels—so a 6-state HMM got **0.00 µs** error. On the new dataset, `stagger` has **16–32 levels**. Squeezing 32 distinct pulses into 6 states completely scrambles the sequence (**163–165 µs** MAE vs. Chronos-2's **4.8–5.8 µs** clean).
2. **The "Elevator Problem" on `triangular_sliding` & `sinusoidal`:**
   A **1st-order** Markov model only looks at *where you are right now* ($s_t$) to guess *where you go next* ($s_{t+1}$). Imagine standing on **Floor 3** of a building with no memory of the previous floor: are you going **up to Floor 4** or **down to Floor 2**? Both happened 50% of the time in history! So the model ties and bounces back and forth (**78–87 µs** MAE vs. Chronos-2's **1.5–2.6 µs** clean).

### B. Unintended Implementation Bugs (Where an HMM *Should* Have Done Well!)
1. **`dwell_and_switch` (Expected ~0 µs, got 15.6–21.7 µs clean, won only 1/64 conditions):**
   - **Bug 1 ($K=5$ was missing!):** The old dataset's `dwell_and_switch` had 2 levels, so the author hardcoded `(1, 2, 3, 4, 6)` and skipped `5`. The new dataset has **5 levels**!
   - **Bug 2 (Bad EM starting variances):** Even if we added `5`, `hmmlearn` initialized every state's spread to the *entire* signal's variance (`init_params="stc"`), causing adjacent levels like `850 µs` and `925 µs` to melt into one blurry bucket.
   - **Bug 3 (Dwell length capped at 20 + single-pulse glitches):** Fallback dwell length was capped at `20` pulses even though dwells are `32/48/64` pulses, and a single noisy pulse inside a dwell could trick the model into resetting its counter.
2. **`markov_agile` (Literally generated by a 4-state Markov chain, yet lost to a flat constant line: ~106 µs vs. ~100 µs!):**
   - **Bug 4 (Blocked by the `0.22` gate):** A 4-state Markov chain with $70\%$ cyclic jump probability has a mathematical autocorrelation of **$0.216$**—just below the hardcoded `0.22` cutoff! Half the time, the HMM didn't even run.
   - **Bug 5 (Deterministic gambling on a weighted roulette wheel):** When it *did* run, it predicted a 100% rigid deterministic loop ($A \rightarrow B \rightarrow C \rightarrow D$). Because there is a $30\%$ chance of deviating at every step, the chance of still being on that deterministic loop after 5 pulses is only $0.70^5 \approx 16.8\%$, and after 10 pulses is $2.8\%$. Guessing extreme values (`850` or `1150`) when the future is already mixed produces **150 µs** expected error instead of **100 µs**!

---

## 4. How the Optimized 1st-Order HMM (`optimized_hmm.py` / `results_optimized_hmm/`) Works

Our goal is **not** to hack the classical HMM into beating foundation models on waves or 32-level codes—the goal of **PULSAR** is to build an **honest classical benchmark** so we can fairly evaluate Time-Series Foundation Models before distilling them onto an **FPGA**.

So in [`optimized_hmm.py`](optimized_hmm.py), we kept the exact same **1st-order $K \le 6$ HMM boundary** and fixed *only* the bugs on discrete-state Markov / semi-Markov laws:

1. **Restored $K=5$ + Smart 1D Clustering Initialization (`K ∈ {1,2,3,4,5,6}`, `init_params="st"`):**
   Runs 15 fast iterations of 1D K-Medians to find the sharp cluster centers *and* local within-cluster variances before starting EM, preventing adjacent levels (`850` vs. `925 µs`) from collapsing together.
2. **Lowered White-Noise Gate (`0.22` $\rightarrow$ `0.15`) + True Probabilistic Markov Rollout ($p_{T+h} = p_T A^h$):**
   Allows `markov_agile` ($\text{ACF} \approx 0.216$) into the $K=4$ HMM while still blocking pure white noise (`jitter`, $\text{ACF} \le 0.12$). For stochastic chains (run length $\le 2$, max transition probability $< 0.90$), instead of gambling on a single deterministic path, it propagates the full state probability vector $p_{T+h} = p_T A^h$ at each future step $h = 1 \dots 32$: predicting the dominant state when probability $\ge 50\%$ (step $h=1$, `~50 µs` error), and smoothly converging to the expected value $\sum_j p_{T+h,j}\mu_j$ (`~100 µs` Bayes floor) once uncertainty mixes!
3. **1-Pulse Despiking & Realistic Dwell Cap (`0.985` $\rightarrow$ 67 pulses):**
   Smooths out isolated 1-pulse Viterbi glitches inside long burst dwells and raises the fallback dwell cap from 20 to 67 pulses.

---

## 5. Before vs. After Results ($L = 992, H = 32$)

Fixing only those textbook discrete-state HMM bugs moved HMM's win count against **Chronos-2 Zero-Shot** from **176 / 512 (34.4%)** to **268 / 512 (52.3%)**—while leaving high-order/continuous waveforms faithfully unsolved by 1st-order HMM:

| Radar Law | Baseline HMM Mean MAE (`µs`, Fixed / Varying) | Optimized HMM Mean MAE (`µs`, Fixed / Varying) | Chronos-2 Zero-Shot (`µs`, Fixed / Varying) | Opt HMM Wins vs. Chronos-2 (All 64 Cells) | Takeaway |
|---|---:|---:|---:|---:|---|
| **`dwell_and_switch`** | `41.99` / `37.56` | **`20.40`** / **`21.10`** *(0.00 clean, 0.01–2.74 lv1–5)* | `20.21` / `17.11` | **43 / 64** *(was 1/64)* | **Fixed:** Clean error drops to **0.000 µs (100% hit rate)**; beats Chronos-2 from `clean` through `error_lv6`. |
| **`markov_agile`** | `105.92` / `105.88` | **`98.88`** / **`98.32`** | `99.88` / `99.34` | **60 / 64** *(was 7/64)* | **Fixed:** Proper $p_T A^h$ rollout reaches the theoretical Bayes floor and beats Chronos-2 across `clean..lv7`. |
| **`stable`** | `0.29` / `0.30` | **`0.28`** / **`0.27`** *(0.02 at lv7)* | `1.13` / `1.11` | **48 / 64** | **Strong:** `clean_pri_context` yields 100% gate hit rate even at 25.4% missing pulses (`lv7`). |
| **`jitter`** | `39.63` / `47.70` | `39.63` / `47.70` | `39.94` / `48.07` | **59 / 64** | **Optimal:** Gate triggers 100% and hits the exact Bayes median floor. |
| **`sliding`** *(untargeted side-gain)* | `60.37` / `69.70` | **`22.42`** / **`31.79`** | `33.90` / `32.52` | **29 / 64** | Local clustering improved the 6-step staircase; Chronos-2 still dominates `clean..lv4`. |
| **`stagger`** *(32 levels)* | `163.28` / `164.80` | `163.66` / `167.15` | **`82.82`** / **`80.97`** | **10 / 64** | **Honest Failure:** 6 states cannot represent 16–32 stagger levels (Chronos-2 gets `4.8–5.8 µs` clean). |
| **`sinusoidal`** | `79.06` / `77.90` | `111.63` / `113.55` | **`43.89`** / **`44.69`** | **11 / 64** | **Honest Failure:** Continuous wave + 1st-order up/down ambiguity (Chronos-2 gets `2.0–2.6 µs` clean). |
| **`triangular_sliding`** | `86.94` / `86.36` | `97.16` / `96.65` | **`26.62`** / **`26.32`** | **8 / 64** | **Honest Failure:** "Elevator Problem" up/down tie (Chronos-2 gets `1.5–1.6 µs` clean). |

### Why This Matters for the FPGA Project (`PULSAR.md`)
- **If an emitter is a simple discrete-state FSM or steady clock (`stable`, `jitter`, `dwell_and_switch`, `markov_agile`):** An honest, properly tuned 1st-order HMM + ESM gap cleaner is competitive with or better than zero-shot foundation models.
- **If an emitter uses 32-level `stagger` or continuous/higher-order PRI (`sinusoidal`, `triangular_sliding`, clean `sliding`):** Classical 1st-order HMMs fail fundamentally (`97–178 µs` error vs. Chronos-2's `1.5–5.8 µs`), proving quantitatively why we need **Time-Series Foundation Models** (and **Teacher–Student Knowledge Distillation** into a lightweight **FPGA Student Model**) in Stage 2 & Stage 3 of the project.

---

## 6. Folder Map (Where to Look)

- **This Guide:** [`00_HMM_EXPLAINED_FOR_EVERYONE.md`](00_HMM_EXPLAINED_FOR_EVERYONE.md) & [`README.md`](README.md)
- **Baseline HMM Results (`classic_methods/hidden_markov_model.py`):**
  - [`results_baseline_hmm/MAE_comparison.md`](results_baseline_hmm/MAE_comparison.md)
  - [`results_baseline_hmm/HMM_vs_Chronos2_PRI_comparison.md`](results_baseline_hmm/HMM_vs_Chronos2_PRI_comparison.md) (with paired 95% bootstrap CIs & cleaner audit)
  - [`results_baseline_hmm/plots/`](results_baseline_hmm/plots/)
- **Optimized 1st-Order HMM Code & Results (`optimized_hmm.py`):**
  - [`optimized_hmm.py`](optimized_hmm.py)
  - [`results_optimized_hmm/Baseline_vs_Optimized_HMM_vs_Chronos2.md`](results_optimized_hmm/Baseline_vs_Optimized_HMM_vs_Chronos2.md) (3-way comparison!)
  - [`results_optimized_hmm/MAE_comparison.md`](results_optimized_hmm/MAE_comparison.md)
  - [`results_optimized_hmm/plots/baseline_vs_optimized_vs_chronos2_fixed_L992.png`](results_optimized_hmm/plots/baseline_vs_optimized_vs_chronos2_fixed_L992.png)
  - [`results_optimized_hmm/plots/baseline_vs_optimized_vs_chronos2_varying_L992.png`](results_optimized_hmm/plots/baseline_vs_optimized_vs_chronos2_varying_L992.png)
- **Scripts (16-core parallel execution):**
  - [`parallel_generate_datasets.py`](parallel_generate_datasets.py) — 16-core generator for `new_complex_pri` (`1000x1056`) + SHA256 verifier
  - [`run_baseline_hmm_benchmark.py`](run_baseline_hmm_benchmark.py) / [`generate_baseline_hmm_reports.py`](generate_baseline_hmm_reports.py)
  - [`run_optimized_hmm_benchmark.py`](run_optimized_hmm_benchmark.py) / [`generate_optimized_hmm_reports.py`](generate_optimized_hmm_reports.py)
