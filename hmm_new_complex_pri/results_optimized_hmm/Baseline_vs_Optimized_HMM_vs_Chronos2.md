# 3-Way Benchmark: Baseline HMM vs Optimized 1st-Order HMM vs Chronos-2 Zero-Shot (`new_complex_pri`)

## Design Scope
The Optimized HMM strictly preserves the **1st-order discrete-state HMM boundary ($K \le 6$)** without adding ad-hoc hacks for high-order stagger (`K=16..32`) or continuous/up-down waveforms (`sinusoidal`, `triangular_sliding`, `sliding`). It fixes only the genuine HMM implementation flaws on discrete-state laws:
1. Restores $K=5$ in candidate set `(1, 2, 3, 4, 5, 6)` + 1D K-Medians local-variance init (`init_params='st'`) for `dwell_and_switch`.
2. Lowers the white-noise ACF gate (`0.22 -> 0.15`) + replaces greedy deterministic path rollout with probabilistic forward distribution propagation ($p_{T+h} = p_T A^h$) for `markov_agile`.
3. Adds isolated 1-pulse Viterbi despiking + `0.985` dwell cap for multi-pulse burst-dwell laws.

## Overall Wins Across All 512 Conditions (Opt HMM vs Chronos-2)

- **Optimized HMM beats Chronos-2**: 268 / 512 (was 176 / 512 for Baseline HMM)
- **Chronos-2 beats Optimized HMM**: 244 / 512

## Mean MAE (µs) Comparison at L = 992 by Radar Type (Averaged Across Clean..Lv7)

| Profile | Radar type | Baseline HMM | Optimized HMM | Δ (Opt − Base) | Chronos-2 Zero-Shot | Ctx Median Floor |
|---|---|---:|---:|---:|---:|---:|
| fixed | stable | 0.293 | 0.275 | -0.018 | 1.125 | 0.077 |
| fixed | jitter | 39.627 | 39.627 | +0.000 | 39.939 | 40.254 |
| fixed | stagger | 163.277 | 163.657 | +0.380 | 82.823 | 131.534 |
| fixed | dwell_and_switch | 41.986 | 20.404 | -21.582 | 20.207 | 92.744 |
| fixed | sliding | 60.372 | 22.422 | -37.950 | 33.901 | 81.426 |
| fixed | sinusoidal | 79.056 | 111.629 | +32.572 | 43.892 | 97.715 |
| fixed | triangular_sliding | 86.942 | 97.161 | +10.218 | 26.624 | 76.764 |
| fixed | markov_agile | 105.924 | 98.878 | -7.046 | 99.878 | 99.903 |
| varying | stable | 0.298 | 0.266 | -0.031 | 1.114 | 0.077 |
| varying | jitter | 47.696 | 47.699 | +0.003 | 48.071 | 48.461 |
| varying | stagger | 164.802 | 167.154 | +2.352 | 80.972 | 145.896 |
| varying | dwell_and_switch | 37.559 | 21.104 | -16.455 | 17.112 | 96.084 |
| varying | sliding | 69.704 | 31.793 | -37.911 | 32.518 | 82.974 |
| varying | sinusoidal | 77.904 | 113.553 | +35.649 | 44.685 | 97.937 |
| varying | triangular_sliding | 86.360 | 96.650 | +10.289 | 26.318 | 76.515 |
| varying | markov_agile | 105.881 | 98.322 | -7.560 | 99.338 | 99.769 |

## Fixed Profile Full Table at L = 992

| Radar type | Error level | Baseline HMM | Optimized HMM | Δ (Opt−Base) | Chronos-2 | Opt Hit% | Best Overall |
|---|---|---:|---:|---:|---:|---:|---|
| stable | clean | 0.000 | 0.000 | -0.000 | 0.000 | 100.0% | **Chronos-2** |
| stable | error_lv1 | 0.091 | 0.089 | -0.002 | 0.060 | 100.0% | **Chronos-2** |
| stable | error_lv2 | 0.438 | 0.434 | -0.005 | 0.150 | 100.0% | **Chronos-2** |
| stable | error_lv3 | 0.835 | 0.821 | -0.014 | 0.214 | 100.0% | **Chronos-2** |
| stable | error_lv4 | 0.459 | 0.454 | -0.005 | 0.120 | 100.0% | **Chronos-2** |
| stable | error_lv5 | 0.353 | 0.331 | -0.022 | 0.502 | 100.0% | **Optimized HMM** |
| stable | error_lv6 | 0.088 | 0.047 | -0.042 | 2.404 | 100.0% | **Optimized HMM** |
| stable | error_lv7 | 0.077 | 0.020 | -0.056 | 5.551 | 100.0% | **Optimized HMM** |
| jitter | clean | 38.814 | 38.814 | +0.000 | 38.774 | 16.1% | **Chronos-2** |
| jitter | error_lv1 | 40.421 | 40.421 | +0.000 | 40.446 | 15.6% | **Optimized HMM** |
| jitter | error_lv2 | 39.769 | 39.769 | +0.000 | 39.937 | 15.9% | **Optimized HMM** |
| jitter | error_lv3 | 39.258 | 39.258 | +0.000 | 39.518 | 16.0% | **Optimized HMM** |
| jitter | error_lv4 | 39.984 | 39.984 | +0.000 | 40.106 | 16.3% | **Baseline HMM** |
| jitter | error_lv5 | 39.428 | 39.428 | +0.000 | 39.471 | 16.1% | **Optimized HMM** |
| jitter | error_lv6 | 39.610 | 39.610 | +0.000 | 40.048 | 16.0% | **Optimized HMM** |
| jitter | error_lv7 | 39.735 | 39.735 | +0.000 | 41.209 | 15.9% | **Optimized HMM** |
| stagger | clean | 170.698 | 173.256 | +2.558 | 5.818 | 6.5% | **Chronos-2** |
| stagger | error_lv1 | 166.233 | 169.453 | +3.221 | 45.010 | 4.1% | **Chronos-2** |
| stagger | error_lv2 | 165.933 | 167.738 | +1.805 | 72.945 | 3.6% | **Chronos-2** |
| stagger | error_lv3 | 166.682 | 166.821 | +0.139 | 103.161 | 3.4% | **Chronos-2** |
| stagger | error_lv4 | 167.890 | 169.675 | +1.786 | 46.752 | 3.9% | **Chronos-2** |
| stagger | error_lv5 | 165.265 | 164.218 | -1.046 | 118.747 | 3.5% | **Chronos-2** |
| stagger | error_lv6 | 156.604 | 159.751 | +3.147 | 129.422 | 3.7% | **Chronos-2** |
| stagger | error_lv7 | 146.911 | 138.341 | -8.570 | 140.728 | 3.7% | **Optimized HMM** |
| dwell_and_switch | clean | 21.691 | 0.000 | -21.691 | 1.298 | 100.0% | **Optimized HMM** |
| dwell_and_switch | error_lv1 | 20.261 | 0.428 | -19.833 | 11.130 | 99.7% | **Optimized HMM** |
| dwell_and_switch | error_lv2 | 31.030 | 0.651 | -30.379 | 10.661 | 99.6% | **Optimized HMM** |
| dwell_and_switch | error_lv3 | 23.800 | 1.560 | -22.240 | 13.700 | 98.3% | **Optimized HMM** |
| dwell_and_switch | error_lv4 | 23.956 | 0.053 | -23.903 | 5.999 | 100.0% | **Optimized HMM** |
| dwell_and_switch | error_lv5 | 35.271 | 1.390 | -33.881 | 18.201 | 99.1% | **Optimized HMM** |
| dwell_and_switch | error_lv6 | 57.477 | 31.039 | -26.437 | 39.629 | 86.2% | **Optimized HMM** |
| dwell_and_switch | error_lv7 | 122.402 | 128.111 | +5.709 | 61.043 | 49.1% | **Chronos-2** |
| sliding | clean | 53.967 | 18.900 | -35.067 | 1.827 | 49.1% | **Chronos-2** |
| sliding | error_lv1 | 65.148 | 18.158 | -46.990 | 8.279 | 31.5% | **Chronos-2** |
| sliding | error_lv2 | 55.350 | 22.365 | -32.985 | 17.334 | 30.0% | **Chronos-2** |
| sliding | error_lv3 | 50.543 | 19.948 | -30.595 | 27.864 | 30.8% | **Optimized HMM** |
| sliding | error_lv4 | 64.758 | 18.461 | -46.297 | 7.720 | 31.2% | **Chronos-2** |
| sliding | error_lv5 | 46.830 | 19.844 | -26.986 | 44.807 | 30.9% | **Optimized HMM** |
| sliding | error_lv6 | 69.626 | 25.508 | -44.117 | 80.670 | 29.7% | **Optimized HMM** |
| sliding | error_lv7 | 76.754 | 36.192 | -40.562 | 82.706 | 23.1% | **Optimized HMM** |
| sinusoidal | clean | 81.178 | 127.858 | +46.681 | 2.563 | 7.1% | **Chronos-2** |
| sinusoidal | error_lv1 | 77.677 | 122.483 | +44.806 | 21.539 | 5.9% | **Chronos-2** |
| sinusoidal | error_lv2 | 80.925 | 116.556 | +35.630 | 27.193 | 6.3% | **Chronos-2** |
| sinusoidal | error_lv3 | 74.241 | 117.344 | +43.104 | 36.450 | 5.9% | **Chronos-2** |
| sinusoidal | error_lv4 | 76.100 | 122.030 | +45.929 | 21.042 | 6.5% | **Chronos-2** |
| sinusoidal | error_lv5 | 69.365 | 113.996 | +44.631 | 53.068 | 5.9% | **Chronos-2** |
| sinusoidal | error_lv6 | 78.960 | 77.341 | -1.620 | 90.506 | 12.7% | **Optimized HMM** |
| sinusoidal | error_lv7 | 94.006 | 95.423 | +1.417 | 98.773 | 6.4% | **Baseline HMM** |
| triangular_sliding | clean | 98.850 | 103.773 | +4.923 | 1.548 | 9.3% | **Chronos-2** |
| triangular_sliding | error_lv1 | 91.312 | 96.275 | +4.964 | 7.711 | 14.0% | **Chronos-2** |
| triangular_sliding | error_lv2 | 87.558 | 99.531 | +11.973 | 13.576 | 13.9% | **Chronos-2** |
| triangular_sliding | error_lv3 | 86.220 | 97.860 | +11.640 | 18.251 | 16.0% | **Chronos-2** |
| triangular_sliding | error_lv4 | 90.903 | 98.768 | +7.864 | 8.039 | 13.3% | **Chronos-2** |
| triangular_sliding | error_lv5 | 87.929 | 97.724 | +9.794 | 27.116 | 15.2% | **Chronos-2** |
| triangular_sliding | error_lv6 | 75.322 | 94.983 | +19.662 | 56.745 | 11.9% | **Chronos-2** |
| triangular_sliding | error_lv7 | 77.445 | 88.370 | +10.926 | 80.010 | 8.6% | **Baseline HMM** |
| markov_agile | clean | 107.188 | 97.993 | -9.194 | 99.854 | 3.5% | **Optimized HMM** |
| markov_agile | error_lv1 | 111.111 | 99.018 | -12.092 | 100.286 | 5.1% | **Optimized HMM** |
| markov_agile | error_lv2 | 106.091 | 96.846 | -9.245 | 98.296 | 5.1% | **Optimized HMM** |
| markov_agile | error_lv3 | 107.086 | 99.609 | -7.476 | 99.840 | 3.5% | **Optimized HMM** |
| markov_agile | error_lv4 | 108.902 | 97.796 | -11.106 | 99.611 | 4.6% | **Optimized HMM** |
| markov_agile | error_lv5 | 105.811 | 100.931 | -4.880 | 100.909 | 3.7% | **Chronos-2** |
| markov_agile | error_lv6 | 100.857 | 98.614 | -2.243 | 99.089 | 1.3% | **Optimized HMM** |
| markov_agile | error_lv7 | 100.343 | 100.214 | -0.129 | 101.144 | 1.1% | **Optimized HMM** |

## Varying Profile Full Table at L = 992

| Radar type | Error level | Baseline HMM | Optimized HMM | Δ (Opt−Base) | Chronos-2 | Opt Hit% | Best Overall |
|---|---|---:|---:|---:|---:|---:|---|
| stable | clean | 0.000 | 0.000 | -0.000 | 0.000 | 100.0% | **Chronos-2** |
| stable | error_lv1 | 0.090 | 0.089 | -0.001 | 0.052 | 100.0% | **Chronos-2** |
| stable | error_lv2 | 0.436 | 0.412 | -0.024 | 0.139 | 100.0% | **Chronos-2** |
| stable | error_lv3 | 0.849 | 0.788 | -0.061 | 0.226 | 100.0% | **Chronos-2** |
| stable | error_lv4 | 0.459 | 0.448 | -0.011 | 0.275 | 100.0% | **Chronos-2** |
| stable | error_lv5 | 0.357 | 0.320 | -0.038 | 0.496 | 100.0% | **Optimized HMM** |
| stable | error_lv6 | 0.112 | 0.048 | -0.064 | 2.324 | 100.0% | **Optimized HMM** |
| stable | error_lv7 | 0.077 | 0.024 | -0.054 | 5.401 | 100.0% | **Optimized HMM** |
| jitter | clean | 47.902 | 47.902 | +0.000 | 47.876 | 14.3% | **Chronos-2** |
| jitter | error_lv1 | 48.288 | 48.288 | +0.000 | 48.415 | 14.0% | **Optimized HMM** |
| jitter | error_lv2 | 48.313 | 48.313 | +0.000 | 48.423 | 13.7% | **Optimized HMM** |
| jitter | error_lv3 | 48.046 | 48.046 | +0.000 | 48.460 | 13.8% | **Optimized HMM** |
| jitter | error_lv4 | 47.419 | 47.419 | +0.000 | 47.510 | 14.8% | **Optimized HMM** |
| jitter | error_lv5 | 47.435 | 47.435 | +0.000 | 47.718 | 13.5% | **Optimized HMM** |
| jitter | error_lv6 | 47.305 | 47.305 | +0.000 | 47.635 | 13.9% | **Optimized HMM** |
| jitter | error_lv7 | 46.862 | 46.883 | +0.021 | 48.533 | 14.7% | **Baseline HMM** |
| stagger | clean | 173.146 | 178.047 | +4.901 | 4.812 | 4.0% | **Chronos-2** |
| stagger | error_lv1 | 170.601 | 174.150 | +3.549 | 33.868 | 4.4% | **Chronos-2** |
| stagger | error_lv2 | 169.952 | 176.004 | +6.052 | 63.328 | 4.4% | **Chronos-2** |
| stagger | error_lv3 | 169.253 | 166.122 | -3.131 | 91.851 | 4.9% | **Chronos-2** |
| stagger | error_lv4 | 169.762 | 171.072 | +1.310 | 34.542 | 5.0% | **Chronos-2** |
| stagger | error_lv5 | 168.170 | 170.766 | +2.596 | 120.408 | 4.5% | **Chronos-2** |
| stagger | error_lv6 | 152.753 | 154.885 | +2.131 | 143.204 | 4.1% | **Chronos-2** |
| stagger | error_lv7 | 144.781 | 146.189 | +1.408 | 155.758 | 4.0% | **Baseline HMM** |
| dwell_and_switch | clean | 15.552 | 0.000 | -15.552 | 1.597 | 100.0% | **Optimized HMM** |
| dwell_and_switch | error_lv1 | 13.622 | 0.006 | -13.616 | 5.264 | 100.0% | **Optimized HMM** |
| dwell_and_switch | error_lv2 | 15.558 | 0.167 | -15.391 | 9.565 | 99.9% | **Optimized HMM** |
| dwell_and_switch | error_lv3 | 20.274 | 0.333 | -19.941 | 12.461 | 99.9% | **Optimized HMM** |
| dwell_and_switch | error_lv4 | 13.596 | 0.072 | -13.525 | 5.046 | 100.0% | **Optimized HMM** |
| dwell_and_switch | error_lv5 | 29.617 | 2.743 | -26.874 | 16.809 | 98.1% | **Optimized HMM** |
| dwell_and_switch | error_lv6 | 68.183 | 29.774 | -38.409 | 33.287 | 85.6% | **Optimized HMM** |
| dwell_and_switch | error_lv7 | 124.070 | 135.734 | +11.665 | 52.868 | 47.8% | **Chronos-2** |
| sliding | clean | 81.888 | 30.148 | -51.740 | 1.538 | 25.8% | **Chronos-2** |
| sliding | error_lv1 | 78.557 | 26.987 | -51.570 | 7.988 | 28.2% | **Chronos-2** |
| sliding | error_lv2 | 65.950 | 31.709 | -34.241 | 15.539 | 25.9% | **Chronos-2** |
| sliding | error_lv3 | 63.456 | 33.638 | -29.818 | 25.588 | 26.0% | **Chronos-2** |
| sliding | error_lv4 | 71.563 | 28.631 | -42.932 | 6.437 | 26.5% | **Chronos-2** |
| sliding | error_lv5 | 53.353 | 28.448 | -24.905 | 41.831 | 27.7% | **Optimized HMM** |
| sliding | error_lv6 | 69.780 | 27.896 | -41.884 | 76.973 | 29.4% | **Optimized HMM** |
| sliding | error_lv7 | 73.086 | 46.889 | -26.197 | 84.254 | 21.8% | **Optimized HMM** |
| sinusoidal | clean | 75.443 | 128.188 | +52.745 | 1.983 | 10.3% | **Chronos-2** |
| sinusoidal | error_lv1 | 72.558 | 122.660 | +50.102 | 21.203 | 8.0% | **Chronos-2** |
| sinusoidal | error_lv2 | 69.771 | 118.603 | +48.832 | 27.666 | 8.9% | **Chronos-2** |
| sinusoidal | error_lv3 | 71.449 | 114.190 | +42.741 | 38.932 | 8.5% | **Chronos-2** |
| sinusoidal | error_lv4 | 68.985 | 122.002 | +53.017 | 22.945 | 9.2% | **Chronos-2** |
| sinusoidal | error_lv5 | 74.976 | 109.661 | +34.684 | 53.546 | 9.0% | **Chronos-2** |
| sinusoidal | error_lv6 | 90.968 | 97.749 | +6.781 | 92.707 | 10.7% | **Baseline HMM** |
| sinusoidal | error_lv7 | 99.085 | 95.374 | -3.711 | 98.497 | 7.7% | **Optimized HMM** |
| triangular_sliding | clean | 98.153 | 102.445 | +4.292 | 1.557 | 11.8% | **Chronos-2** |
| triangular_sliding | error_lv1 | 91.814 | 99.242 | +7.428 | 8.012 | 13.7% | **Chronos-2** |
| triangular_sliding | error_lv2 | 85.337 | 97.541 | +12.204 | 13.632 | 15.0% | **Chronos-2** |
| triangular_sliding | error_lv3 | 90.465 | 100.139 | +9.674 | 18.330 | 14.4% | **Chronos-2** |
| triangular_sliding | error_lv4 | 89.320 | 96.078 | +6.759 | 7.387 | 14.5% | **Chronos-2** |
| triangular_sliding | error_lv5 | 85.402 | 96.741 | +11.339 | 27.317 | 15.0% | **Chronos-2** |
| triangular_sliding | error_lv6 | 76.027 | 93.844 | +17.817 | 55.339 | 12.1% | **Chronos-2** |
| triangular_sliding | error_lv7 | 74.364 | 87.167 | +12.803 | 78.969 | 7.9% | **Baseline HMM** |
| markov_agile | clean | 107.007 | 97.442 | -9.566 | 98.435 | 3.3% | **Optimized HMM** |
| markov_agile | error_lv1 | 108.192 | 97.547 | -10.646 | 99.024 | 3.8% | **Optimized HMM** |
| markov_agile | error_lv2 | 109.957 | 97.939 | -12.019 | 99.323 | 3.5% | **Optimized HMM** |
| markov_agile | error_lv3 | 106.453 | 97.645 | -8.808 | 99.089 | 3.6% | **Optimized HMM** |
| markov_agile | error_lv4 | 108.145 | 97.995 | -10.149 | 99.161 | 4.3% | **Optimized HMM** |
| markov_agile | error_lv5 | 105.406 | 100.161 | -5.245 | 99.516 | 4.3% | **Chronos-2** |
| markov_agile | error_lv6 | 102.284 | 98.513 | -3.771 | 99.717 | 1.5% | **Optimized HMM** |
| markov_agile | error_lv7 | 99.605 | 99.333 | -0.272 | 100.437 | 0.9% | **Optimized HMM** |

