# Context-length sweep - classical methods on 1000x1024 datasets

Horizon H = 32, random context start from `results/windows_1024.json` (seed 20261116), 200 test sequences per dataset, emitter-only targets, gate +/-10 us.

## Mean noisy MAE (us), mean over 5 laws x lv1-3

### fixed profile

| Method | L=96 | L=256 | L=512 | L=992 |
|---|---:|---:|---:|---:|
| Kalman bank | 26.85 | 24.75 | 25.03 | 23.88 |
| Exp. smoothing | 29.60 | 27.79 | 27.00 | 25.78 |
| ARIMA | 28.90 | 26.89 | 26.68 | 25.30 |

### varying profile

| Method | L=96 | L=256 | L=512 | L=992 |
|---|---:|---:|---:|---:|
| Kalman bank | 28.94 | 26.48 | 26.18 | 26.65 |
| Exp. smoothing | 32.51 | 30.08 | 28.69 | 28.52 |
| ARIMA | 32.39 | 28.53 | 27.60 | 28.38 |

## Sanity check vs CM1 (varying profile, L = 96, mean noisy MAE)

| Method | CM1 (128-pulse, s=0) | This run (1024-pulse, random s) | Deviation |
|---|---:|---:|---:|
| Kalman bank | 29.3 | 28.9 | -1.2% |
| ARIMA | 33.3 | 32.4 | -2.7% |
| Exp. smoothing | 33.3 | 32.5 | -2.4% |

## Mean noisy MAE (us) per law

### fixed profile

| Method | Law | L=96 | L=256 | L=512 | L=992 |
|---|---|---:|---:|---:|---:|
| Kalman bank | stable | 0.32 | 0.11 | 0.05 | 0.04 |
| Kalman bank | jitter | 42.10 | 40.38 | 40.34 | 40.09 |
| Kalman bank | stagger | 50.95 | 50.98 | 52.51 | 47.38 |
| Kalman bank | dwell_and_switch | 27.40 | 20.70 | 21.24 | 20.74 |
| Kalman bank | sliding | 13.49 | 11.58 | 11.04 | 11.14 |
| Exp. smoothing | stable | 0.14 | 0.18 | 0.09 | 0.62 |
| Exp. smoothing | jitter | 40.44 | 40.10 | 40.14 | 40.04 |
| Exp. smoothing | stagger | 51.71 | 51.80 | 53.19 | 48.06 |
| Exp. smoothing | dwell_and_switch | 41.43 | 34.63 | 29.96 | 28.28 |
| Exp. smoothing | sliding | 14.29 | 12.24 | 11.60 | 11.88 |
| ARIMA | stable | 0.15 | 0.30 | 0.10 | 0.13 |
| ARIMA | jitter | 40.32 | 40.14 | 40.16 | 40.04 |
| ARIMA | stagger | 51.52 | 52.60 | 54.83 | 49.35 |
| ARIMA | dwell_and_switch | 38.02 | 28.25 | 26.11 | 24.14 |
| ARIMA | sliding | 14.49 | 13.16 | 12.17 | 12.87 |

### varying profile

| Method | Law | L=96 | L=256 | L=512 | L=992 |
|---|---|---:|---:|---:|---:|
| Kalman bank | stable | 0.34 | 0.11 | 0.05 | 0.04 |
| Kalman bank | jitter | 49.78 | 47.87 | 47.96 | 47.63 |
| Kalman bank | stagger | 52.39 | 52.94 | 51.30 | 53.72 |
| Kalman bank | dwell_and_switch | 27.74 | 19.76 | 18.27 | 18.48 |
| Kalman bank | sliding | 14.44 | 11.69 | 13.33 | 13.36 |
| Exp. smoothing | stable | 0.80 | 0.12 | 0.05 | 0.05 |
| Exp. smoothing | jitter | 48.27 | 47.57 | 47.80 | 47.50 |
| Exp. smoothing | stagger | 52.93 | 53.72 | 52.00 | 54.35 |
| Exp. smoothing | dwell_and_switch | 44.84 | 36.50 | 29.40 | 26.76 |
| Exp. smoothing | sliding | 15.73 | 12.51 | 14.18 | 13.93 |
| ARIMA | stable | 0.25 | 0.10 | 0.10 | 0.11 |
| ARIMA | jitter | 48.17 | 47.56 | 47.79 | 47.50 |
| ARIMA | stagger | 52.45 | 55.14 | 52.90 | 56.24 |
| ARIMA | dwell_and_switch | 43.93 | 26.22 | 22.22 | 23.24 |
| ARIMA | sliding | 17.14 | 13.63 | 15.00 | 14.81 |

## Run time (sum of per-sequence fit+forecast CPU time, all 20 datasets x 200 seqs)

| Method | Profile | L=96 | L=256 | L=512 | L=992 |
|---|---|---:|---:|---:|---:|
| Kalman bank | fixed | 9.8 min | 15.5 min | 29.3 min | 53.6 min |
| Kalman bank | varying | 9.1 min | 15.5 min | 28.5 min | 52.5 min |
| Exp. smoothing | fixed | 6.5 min | 7.1 min | 7.8 min | 8.3 min |
| Exp. smoothing | varying | 5.9 min | 7.5 min | 8.3 min | 8.8 min |
| ARIMA | fixed | 46.5 min | 73.8 min | 116.6 min | 198.7 min |
| ARIMA | varying | 54.3 min | 78.4 min | 121.2 min | 201.7 min |

Fallback windows (sequence shorter than L + H, context shortened to n - H, s = 0), summed over methods x datasets: L=96: 0, L=256: 0, L=512: 0, L=992: 0
