# HMM vs Chronos-2 Zero-Shot (Univariate PRI) on `new_complex_pri`

Compares `classic_methods.hidden_markov_model.hmm_forecast` against Chronos-2 zero-shot (`run_20261118_151924`) across all 512 conditions (2 profiles x 8 radar types x 8 error levels x 4 context lengths, H=32, 200 test sequences each = 102,400 forecasts).

## Methodological & Protocol Notes
- **Boundary & Input Parity**: Both models are evaluated at `window_mode='boundary'` (`start = 1024 - L`, `H = 32`, `seq_0800..seq_0999`, `valid_pulses = 32` everywhere).
- **Front-End Asymmetry**: HMM includes a hand-tuned ESM front-end (`clean_pri_context` splitting 2×/3× missed-pulse intervals, `max_acf < 0.22` white-noise gate, `2.2×` BIC penalty), whereas Chronos-2 receives raw `Measured_Delta_TOA`.
- **Naive Floor Interpretation**: On severe loss (`error_lv6`/`lv7`) or random laws (`jitter`, `markov_agile`), a model winning while sitting at or above the context-median floor reflects floor saturation rather than superior forecasting skill.
- **Dataset Caveat**: Per `dataset_generator/CONSECUTIVE_FUTURE.md`, the production validator was previously noted as incomplete on the teammate's side; our local test split was verified byte-for-byte against the 25,600 SHA256 hashes in `test_windows.json`.

## Condition-Level Win Counts Across All 512 Conditions

- **HMM wins (condition mean MAE)**: 176 / 512
- **Chronos-2 wins (condition mean MAE)**: 336 / 512
- **Ties**: 0 / 512
- **Conditions where both models sit >= 98% of context-median floor**: 139 / 512

## ESM Cleaner & ACF Gate Audit Summary (L = 992)

| Error level | Mean Cleaner Count Ratio (`cleaned_len / true_source_pulses`) |
|---|---:|
| clean | 1.0000 |
| error_lv1 | 1.0000 |
| error_lv2 | 0.9999 |
| error_lv3 | 0.9997 |
| error_lv4 | 1.0000 |
| error_lv5 | 0.9990 |
| error_lv6 | 0.9870 |
| error_lv7 | 0.9485 |

## Fixed Profile at L = 992 (Longest Shared Context)

| Radar type | Error level | HMM MAE | Chronos-2 MAE | Ctx Med Floor | Δ (HMM−Chr) [95% CI] | Seq Wins (H/C/T) | ACF Gate% | Winner |
|---|---|---:|---:|---:|---:|---:|---:|---|
| stable | clean | 0.000 | 0.000 | 0.000 | +0.000 [+0.00, +0.00] | 0/200/0 | 100.0% | **Chronos-2** |
| stable | error_lv1 | 0.091 | 0.060 | 0.003 | +0.031 [+0.01, +0.05] | 19/181/0 | 0.0% | **Chronos-2** |
| stable | error_lv2 | 0.438 | 0.150 | 0.019 | +0.288 [+0.27, +0.30] | 6/194/0 | 0.0% | **Chronos-2** |
| stable | error_lv3 | 0.835 | 0.214 | 0.055 | +0.621 [+0.59, +0.65] | 8/192/0 | 0.0% | **Chronos-2** |
| stable | error_lv4 | 0.459 | 0.120 | 0.014 | +0.339 [+0.28, +0.37] | 4/196/0 | 0.0% | **Chronos-2** |
| stable | error_lv5 | 0.353 | 0.502 | 0.050 | -0.148 [-0.20, -0.10] | 126/74/0 | 0.0% | **HMM** |
| stable | error_lv6 | 0.088 | 2.404 | 0.166 | -2.316 [-2.43, -2.21] | 200/0/0 | 0.0% | **HMM** |
| stable | error_lv7 | 0.077 | 5.551 | 0.310 | -5.475 [-5.82, -5.21] | 200/0/0 | 0.0% | **HMM** |
| jitter | clean | 38.814 | 38.774 | 38.814 | +0.040 [+0.00, +0.08] | 93/107/0 | 100.0% | **Chronos-2** |
| jitter | error_lv1 | 40.421 | 40.446 | 40.422 | -0.025 [-0.10, +0.05] | 94/106/0 | 100.0% | **HMM** |
| jitter | error_lv2 | 39.769 | 39.937 | 39.780 | -0.168 [-0.28, -0.07] | 124/76/0 | 100.0% | **HMM** |
| jitter | error_lv3 | 39.258 | 39.518 | 39.318 | -0.261 [-0.40, -0.13] | 123/77/0 | 100.0% | **HMM** |
| jitter | error_lv4 | 39.984 | 40.106 | 39.994 | -0.121 [-0.24, -0.02] | 108/92/0 | 100.0% | **HMM** |
| jitter | error_lv5 | 39.428 | 39.471 | 39.436 | -0.043 [-0.18, +0.08] | 109/91/0 | 100.0% | **HMM** |
| jitter | error_lv6 | 39.610 | 40.048 | 40.707 | -0.438 [-0.60, -0.26] | 124/76/0 | 100.0% | **HMM** |
| jitter | error_lv7 | 39.735 | 41.209 | 43.558 | -1.474 [-1.81, -1.16] | 144/56/0 | 100.0% | **HMM** |
| stagger | clean | 170.698 | 5.818 | 129.032 | +164.880 [+162.66, +167.10] | 0/200/0 | 0.0% | **Chronos-2** |
| stagger | error_lv1 | 166.233 | 45.010 | 129.032 | +121.223 [+114.76, +127.83] | 5/195/0 | 0.0% | **Chronos-2** |
| stagger | error_lv2 | 165.933 | 72.945 | 129.032 | +92.987 [+87.72, +98.27] | 3/197/0 | 0.0% | **Chronos-2** |
| stagger | error_lv3 | 166.682 | 103.161 | 129.045 | +63.521 [+59.58, +67.18] | 0/200/0 | 0.0% | **Chronos-2** |
| stagger | error_lv4 | 167.890 | 46.752 | 129.032 | +121.138 [+114.39, +127.69] | 3/197/0 | 0.0% | **Chronos-2** |
| stagger | error_lv5 | 165.265 | 118.747 | 129.380 | +46.518 [+43.79, +49.27] | 4/196/0 | 0.0% | **Chronos-2** |
| stagger | error_lv6 | 156.604 | 129.422 | 133.482 | +27.182 [+24.91, +29.46] | 10/190/0 | 0.0% | **Chronos-2** |
| stagger | error_lv7 | 146.911 | 140.728 | 144.235 | +6.183 [+3.67, +8.60] | 77/123/0 | 11.5% | **Chronos-2** |
| dwell_and_switch | clean | 21.691 | 1.298 | 91.582 | +20.393 [+17.41, +23.25] | 68/132/0 | 0.0% | **Chronos-2** |
| dwell_and_switch | error_lv1 | 20.261 | 11.130 | 88.347 | +9.131 [-3.36, +17.42] | 97/103/0 | 0.0% | **Chronos-2** |
| dwell_and_switch | error_lv2 | 31.030 | 10.661 | 92.416 | +20.369 [+14.10, +27.28] | 104/96/0 | 0.0% | **Chronos-2** |
| dwell_and_switch | error_lv3 | 23.800 | 13.700 | 88.484 | +10.100 [+4.90, +16.19] | 125/75/0 | 0.0% | **Chronos-2** |
| dwell_and_switch | error_lv4 | 23.956 | 5.999 | 88.588 | +17.958 [+13.15, +23.27] | 97/103/0 | 0.0% | **Chronos-2** |
| dwell_and_switch | error_lv5 | 35.271 | 18.201 | 90.727 | +17.070 [+11.22, +22.50] | 90/110/0 | 0.0% | **Chronos-2** |
| dwell_and_switch | error_lv6 | 57.477 | 39.629 | 98.231 | +17.848 [+9.52, +26.33] | 95/105/0 | 0.5% | **Chronos-2** |
| dwell_and_switch | error_lv7 | 122.402 | 61.043 | 103.575 | +61.359 [+49.27, +73.86] | 50/150/0 | 14.5% | **Chronos-2** |
| sliding | clean | 53.967 | 1.827 | 80.000 | +52.140 [+47.33, +56.79] | 0/200/0 | 0.0% | **Chronos-2** |
| sliding | error_lv1 | 65.148 | 8.279 | 80.000 | +56.870 [+51.64, +62.41] | 8/192/0 | 0.0% | **Chronos-2** |
| sliding | error_lv2 | 55.350 | 17.334 | 80.000 | +38.016 [+32.56, +42.95] | 26/174/0 | 0.0% | **Chronos-2** |
| sliding | error_lv3 | 50.543 | 27.864 | 80.000 | +22.679 [+17.41, +27.55] | 68/132/0 | 0.0% | **Chronos-2** |
| sliding | error_lv4 | 64.758 | 7.720 | 80.000 | +57.039 [+51.78, +62.38] | 10/190/0 | 0.0% | **Chronos-2** |
| sliding | error_lv5 | 46.830 | 44.807 | 80.012 | +2.023 [-2.73, +6.61] | 124/76/0 | 0.0% | **Chronos-2** |
| sliding | error_lv6 | 69.626 | 80.670 | 82.536 | -11.044 [-17.40, -5.38] | 109/91/0 | 0.0% | **HMM** |
| sliding | error_lv7 | 76.754 | 82.706 | 88.864 | -5.952 [-9.81, -2.21] | 111/89/0 | 11.5% | **HMM** |
| sinusoidal | clean | 81.178 | 2.563 | 95.533 | +78.615 [+73.84, +83.10] | 0/200/0 | 0.0% | **Chronos-2** |
| sinusoidal | error_lv1 | 77.677 | 21.539 | 95.532 | +56.138 [+50.85, +61.10] | 4/196/0 | 0.0% | **Chronos-2** |
| sinusoidal | error_lv2 | 80.925 | 27.193 | 95.576 | +53.732 [+48.13, +58.93] | 13/187/0 | 0.0% | **Chronos-2** |
| sinusoidal | error_lv3 | 74.241 | 36.450 | 95.568 | +37.791 [+32.63, +43.52] | 36/164/0 | 0.0% | **Chronos-2** |
| sinusoidal | error_lv4 | 76.100 | 21.042 | 95.513 | +55.058 [+50.29, +59.62] | 7/193/0 | 0.0% | **Chronos-2** |
| sinusoidal | error_lv5 | 69.365 | 53.068 | 96.097 | +16.297 [+10.95, +21.96] | 79/121/0 | 0.0% | **Chronos-2** |
| sinusoidal | error_lv6 | 78.960 | 90.506 | 99.205 | -11.545 [-17.57, -6.26] | 110/90/0 | 0.0% | **HMM** |
| sinusoidal | error_lv7 | 94.006 | 98.773 | 108.695 | -4.767 [-6.95, -2.73] | 125/75/0 | 89.5% | **HMM** |
| triangular_sliding | clean | 98.850 | 1.548 | 75.169 | +97.302 [+95.07, +99.48] | 0/200/0 | 0.0% | **Chronos-2** |
| triangular_sliding | error_lv1 | 91.312 | 7.711 | 75.030 | +83.600 [+80.55, +86.71] | 0/200/0 | 0.0% | **Chronos-2** |
| triangular_sliding | error_lv2 | 87.558 | 13.576 | 75.049 | +73.983 [+70.92, +77.05] | 0/200/0 | 0.0% | **Chronos-2** |
| triangular_sliding | error_lv3 | 86.220 | 18.251 | 75.117 | +67.969 [+64.83, +70.91] | 0/200/0 | 0.0% | **Chronos-2** |
| triangular_sliding | error_lv4 | 90.903 | 8.039 | 74.794 | +82.865 [+79.53, +86.46] | 0/200/0 | 0.0% | **Chronos-2** |
| triangular_sliding | error_lv5 | 87.929 | 27.116 | 75.016 | +60.813 [+57.56, +64.22] | 2/198/0 | 0.0% | **Chronos-2** |
| triangular_sliding | error_lv6 | 75.322 | 56.745 | 78.091 | +18.576 [+13.61, +23.52] | 63/137/0 | 0.0% | **Chronos-2** |
| triangular_sliding | error_lv7 | 77.445 | 80.010 | 85.847 | -2.566 [-5.61, +0.36] | 104/96/0 | 26.5% | **HMM** |
| markov_agile | clean | 107.188 | 99.854 | 99.594 | +7.334 [+4.42, +10.21] | 80/120/0 | 54.5% | **Chronos-2** |
| markov_agile | error_lv1 | 111.111 | 100.286 | 100.392 | +10.825 [+7.91, +13.53] | 64/136/0 | 54.0% | **Chronos-2** |
| markov_agile | error_lv2 | 106.091 | 98.296 | 99.396 | +7.795 [+4.62, +10.77] | 71/129/0 | 58.5% | **Chronos-2** |
| markov_agile | error_lv3 | 107.086 | 99.840 | 99.823 | +7.246 [+4.75, +9.82] | 80/120/0 | 63.0% | **Chronos-2** |
| markov_agile | error_lv4 | 108.902 | 99.611 | 100.194 | +9.291 [+6.47, +12.15] | 70/130/0 | 56.5% | **Chronos-2** |
| markov_agile | error_lv5 | 105.811 | 100.909 | 101.504 | +4.902 [+2.64, +7.41] | 90/110/0 | 71.5% | **Chronos-2** |
| markov_agile | error_lv6 | 100.857 | 99.089 | 98.549 | +1.769 [+0.63, +3.06] | 90/110/0 | 93.5% | **Chronos-2** |
| markov_agile | error_lv7 | 100.343 | 101.144 | 99.770 | -0.801 [-1.70, +0.11] | 117/83/0 | 98.0% | **HMM** |

## Varying Profile at L = 992 (Longest Shared Context)

| Radar type | Error level | HMM MAE | Chronos-2 MAE | Ctx Med Floor | Δ (HMM−Chr) [95% CI] | Seq Wins (H/C/T) | ACF Gate% | Winner |
|---|---|---:|---:|---:|---:|---:|---:|---|
| stable | clean | 0.000 | 0.000 | 0.000 | +0.000 [+0.00, +0.00] | 0/200/0 | 100.0% | **Chronos-2** |
| stable | error_lv1 | 0.090 | 0.052 | 0.003 | +0.038 [+0.02, +0.05] | 17/183/0 | 0.0% | **Chronos-2** |
| stable | error_lv2 | 0.436 | 0.139 | 0.017 | +0.297 [+0.28, +0.31] | 5/195/0 | 0.0% | **Chronos-2** |
| stable | error_lv3 | 0.849 | 0.226 | 0.055 | +0.623 [+0.59, +0.66] | 8/192/0 | 0.0% | **Chronos-2** |
| stable | error_lv4 | 0.459 | 0.275 | 0.015 | +0.184 [-0.11, +0.37] | 5/195/0 | 0.0% | **Chronos-2** |
| stable | error_lv5 | 0.357 | 0.496 | 0.050 | -0.139 [-0.18, -0.09] | 126/74/0 | 0.0% | **HMM** |
| stable | error_lv6 | 0.112 | 2.324 | 0.164 | -2.212 [-2.31, -2.11] | 200/0/0 | 0.0% | **HMM** |
| stable | error_lv7 | 0.077 | 5.401 | 0.313 | -5.323 [-5.55, -5.11] | 200/0/0 | 0.0% | **HMM** |
| jitter | clean | 47.902 | 47.876 | 47.902 | +0.026 [-0.03, +0.07] | 81/119/0 | 100.0% | **Chronos-2** |
| jitter | error_lv1 | 48.288 | 48.415 | 48.292 | -0.127 [-0.27, -0.01] | 106/94/0 | 100.0% | **HMM** |
| jitter | error_lv2 | 48.313 | 48.423 | 48.310 | -0.109 [-0.24, +0.01] | 106/94/0 | 100.0% | **HMM** |
| jitter | error_lv3 | 48.046 | 48.460 | 48.154 | -0.414 [-0.61, -0.25] | 130/70/0 | 100.0% | **HMM** |
| jitter | error_lv4 | 47.419 | 47.510 | 47.434 | -0.091 [-0.17, -0.01] | 109/91/0 | 100.0% | **HMM** |
| jitter | error_lv5 | 47.435 | 47.718 | 47.654 | -0.283 [-0.42, -0.14] | 122/78/0 | 100.0% | **HMM** |
| jitter | error_lv6 | 47.305 | 47.635 | 48.632 | -0.330 [-0.49, -0.17] | 120/80/0 | 100.0% | **HMM** |
| jitter | error_lv7 | 46.862 | 48.533 | 51.308 | -1.671 [-2.08, -1.27] | 135/65/0 | 100.0% | **HMM** |
| stagger | clean | 173.146 | 4.812 | 143.764 | +168.334 [+163.12, +173.81] | 0/200/0 | 1.0% | **Chronos-2** |
| stagger | error_lv1 | 170.601 | 33.868 | 143.005 | +136.732 [+129.48, +144.03] | 4/196/0 | 1.5% | **Chronos-2** |
| stagger | error_lv2 | 169.952 | 63.328 | 143.072 | +106.624 [+98.51, +114.63] | 13/187/0 | 1.0% | **Chronos-2** |
| stagger | error_lv3 | 169.253 | 91.851 | 143.244 | +77.402 [+70.63, +84.50] | 11/189/0 | 3.0% | **Chronos-2** |
| stagger | error_lv4 | 169.762 | 34.542 | 142.608 | +135.220 [+127.54, +142.15] | 4/196/0 | 0.5% | **Chronos-2** |
| stagger | error_lv5 | 168.170 | 120.408 | 143.636 | +47.762 [+42.24, +52.69] | 21/179/0 | 4.5% | **Chronos-2** |
| stagger | error_lv6 | 152.753 | 143.204 | 147.851 | +9.549 [+6.47, +12.67] | 75/125/0 | 52.0% | **Chronos-2** |
| stagger | error_lv7 | 144.781 | 155.758 | 159.988 | -10.977 [-12.17, -9.80] | 192/8/0 | 98.5% | **HMM** |
| dwell_and_switch | clean | 15.552 | 1.597 | 92.541 | +13.955 [+11.37, +16.74] | 87/113/0 | 0.0% | **Chronos-2** |
| dwell_and_switch | error_lv1 | 13.622 | 5.264 | 89.562 | +8.358 [+5.73, +11.22] | 119/81/0 | 0.0% | **Chronos-2** |
| dwell_and_switch | error_lv2 | 15.558 | 9.565 | 93.121 | +5.993 [+2.83, +9.41] | 119/81/0 | 0.0% | **Chronos-2** |
| dwell_and_switch | error_lv3 | 20.274 | 12.461 | 89.695 | +7.813 [+3.34, +12.60] | 117/83/0 | 0.0% | **Chronos-2** |
| dwell_and_switch | error_lv4 | 13.596 | 5.046 | 94.806 | +8.550 [+4.73, +12.87] | 120/80/0 | 0.0% | **Chronos-2** |
| dwell_and_switch | error_lv5 | 29.617 | 16.809 | 90.553 | +12.807 [+7.52, +18.54] | 108/92/0 | 0.0% | **Chronos-2** |
| dwell_and_switch | error_lv6 | 68.183 | 33.287 | 106.112 | +34.896 [+26.16, +44.08] | 75/125/0 | 0.5% | **Chronos-2** |
| dwell_and_switch | error_lv7 | 124.070 | 52.868 | 112.281 | +71.202 [+59.62, +83.38] | 39/161/0 | 10.0% | **Chronos-2** |
| sliding | clean | 81.888 | 1.538 | 81.814 | +80.350 [+75.68, +85.13] | 0/200/0 | 0.0% | **Chronos-2** |
| sliding | error_lv1 | 78.557 | 7.988 | 81.805 | +70.570 [+64.95, +75.54] | 3/197/0 | 0.0% | **Chronos-2** |
| sliding | error_lv2 | 65.950 | 15.539 | 81.693 | +50.411 [+45.03, +55.65] | 20/180/0 | 0.0% | **Chronos-2** |
| sliding | error_lv3 | 63.456 | 25.588 | 80.434 | +37.868 [+31.85, +43.93] | 45/155/0 | 0.0% | **Chronos-2** |
| sliding | error_lv4 | 71.563 | 6.437 | 82.170 | +65.127 [+59.96, +70.45] | 1/199/0 | 0.0% | **Chronos-2** |
| sliding | error_lv5 | 53.353 | 41.831 | 81.666 | +11.522 [+6.28, +16.94] | 96/104/0 | 0.0% | **Chronos-2** |
| sliding | error_lv6 | 69.780 | 76.973 | 83.658 | -7.192 [-12.45, -2.03] | 110/90/0 | 0.0% | **HMM** |
| sliding | error_lv7 | 73.086 | 84.254 | 90.552 | -11.168 [-15.88, -6.59] | 115/85/0 | 10.5% | **HMM** |
| sinusoidal | clean | 75.443 | 1.983 | 96.012 | +73.460 [+68.62, +78.54] | 0/200/0 | 0.0% | **Chronos-2** |
| sinusoidal | error_lv1 | 72.558 | 21.203 | 95.775 | +51.355 [+45.84, +57.19] | 16/184/0 | 0.0% | **Chronos-2** |
| sinusoidal | error_lv2 | 69.771 | 27.666 | 95.667 | +42.105 [+35.90, +47.60] | 35/165/0 | 0.0% | **Chronos-2** |
| sinusoidal | error_lv3 | 71.449 | 38.932 | 95.842 | +32.518 [+26.48, +39.25] | 50/150/0 | 0.0% | **Chronos-2** |
| sinusoidal | error_lv4 | 68.985 | 22.945 | 95.671 | +46.040 [+40.32, +51.49] | 21/179/0 | 0.0% | **Chronos-2** |
| sinusoidal | error_lv5 | 74.976 | 53.546 | 96.430 | +21.430 [+16.13, +27.61] | 67/133/0 | 0.0% | **Chronos-2** |
| sinusoidal | error_lv6 | 90.968 | 92.707 | 99.529 | -1.739 [-7.11, +3.93] | 92/108/0 | 0.0% | **HMM** |
| sinusoidal | error_lv7 | 99.085 | 98.497 | 108.571 | +0.588 [-2.21, +3.27] | 94/106/0 | 67.0% | **Chronos-2** |
| triangular_sliding | clean | 98.153 | 1.557 | 74.525 | +96.595 [+93.21, +99.76] | 0/200/0 | 0.0% | **Chronos-2** |
| triangular_sliding | error_lv1 | 91.814 | 8.012 | 74.494 | +83.802 [+79.93, +87.50] | 0/200/0 | 0.0% | **Chronos-2** |
| triangular_sliding | error_lv2 | 85.337 | 13.632 | 74.864 | +71.705 [+68.18, +75.00] | 0/200/0 | 0.0% | **Chronos-2** |
| triangular_sliding | error_lv3 | 90.465 | 18.330 | 74.811 | +72.134 [+68.20, +76.10] | 0/200/0 | 0.0% | **Chronos-2** |
| triangular_sliding | error_lv4 | 89.320 | 7.387 | 74.621 | +81.933 [+78.18, +86.02] | 0/200/0 | 0.0% | **Chronos-2** |
| triangular_sliding | error_lv5 | 85.402 | 27.317 | 74.931 | +58.085 [+54.09, +62.14] | 3/197/0 | 0.0% | **Chronos-2** |
| triangular_sliding | error_lv6 | 76.027 | 55.339 | 78.201 | +20.688 [+16.10, +25.80] | 55/145/0 | 0.0% | **Chronos-2** |
| triangular_sliding | error_lv7 | 74.364 | 78.969 | 85.670 | -4.606 [-8.25, -0.54] | 108/92/0 | 19.5% | **HMM** |
| markov_agile | clean | 107.007 | 98.435 | 99.495 | +8.573 [+5.83, +11.48] | 76/124/0 | 55.5% | **Chronos-2** |
| markov_agile | error_lv1 | 108.192 | 99.024 | 99.369 | +9.169 [+6.15, +12.12] | 67/133/0 | 44.0% | **Chronos-2** |
| markov_agile | error_lv2 | 109.957 | 99.323 | 100.251 | +10.634 [+8.00, +13.17] | 52/148/0 | 57.5% | **Chronos-2** |
| markov_agile | error_lv3 | 106.453 | 99.089 | 99.217 | +7.363 [+4.41, +10.26] | 76/124/0 | 62.5% | **Chronos-2** |
| markov_agile | error_lv4 | 108.145 | 99.161 | 100.116 | +8.984 [+6.20, +11.76] | 66/134/0 | 59.0% | **Chronos-2** |
| markov_agile | error_lv5 | 105.406 | 99.516 | 100.064 | +5.890 [+3.43, +8.62] | 82/118/0 | 70.5% | **Chronos-2** |
| markov_agile | error_lv6 | 102.284 | 99.717 | 100.027 | +2.567 [+0.95, +4.36] | 95/105/0 | 85.5% | **Chronos-2** |
| markov_agile | error_lv7 | 99.605 | 100.437 | 99.611 | -0.831 [-1.60, -0.04] | 102/98/0 | 99.0% | **HMM** |

