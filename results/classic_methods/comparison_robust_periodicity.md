# Robust-periodicity classic methods vs. existing classic baselines (PRI)

Protocol: 96-pulse context, 32-pulse horizon, errors on emitter pulses only (false pulses
masked with the ground-truth labels), target = source PRI, gate = +/-10 us. Test split,
200 sequences per dataset. Forecasts use the context only; hyperparameters were chosen on
the validation split (`results/classic_methods/robust_tuning_val/`).

All methods, old and new, were run on the same test sequences. The existing baselines were
re-run for this table (`robust_periodicity/baselines_rerun/`) because the dataset generator
does not seed the noise, so the committed `metrics.csv` files come from a different
realisation of the data. Best value per column in **bold**. New methods are below the line.

## 1. Summary: mean over error levels 1-3 and all five radar types

| Method | MAE fixed (us) | MAE varying (us) | Hit rate fixed (%) | Hit rate varying (%) | RMSE fixed (us) | RMSE varying (us) | Runtime (ms / sequence) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Rolling median | 74.03 | 80.23 | 33.7 | 36.4 | 86.37 | 98.41 | **0.3** |
| Period estimation | 24.48 | 25.68 | 71.7 | 71.4 | 40.46 | 41.35 | 11.3 |
| HMM | 35.67 | 38.29 | 57.9 | 56.9 | 50.96 | 53.84 | 45.8 |
| Kalman bank | 26.39 | 28.18 | 68.5 | 68.1 | 42.61 | 44.32 | 156.5 |
| Exp. smoothing | 30.09 | 33.67 | 64.5 | 63.2 | 45.89 | 48.71 | 54.8 |
| ARIMA | 29.18 | 32.23 | 68.1 | 66.3 | 44.56 | 47.01 | 984.2 |
| *new methods* | | | | | | | |
| CDIF | 22.24 | 23.42 | **72.8** | **72.4** | 36.97 | 37.23 | 35.1 |
| SDIF | 22.24 | 23.42 | **72.8** | **72.4** | 36.97 | 37.23 | 13.7 |
| PRI transform | 54.90 | 56.66 | 55.2 | 56.0 | 72.66 | 75.96 | 64.4 |
| Lomb-Scargle | 22.37 | 23.84 | 72.7 | 72.3 | 37.10 | 37.66 | 7.6 |
| TOA grid fit | **22.22** | **23.38** | **72.8** | **72.4** | **36.96** | **37.13** | 161.7 |
| Period est. + template gate | 22.26 | 23.40 | 72.8 | **72.4** | 37.01 | 37.15 | 163.3 |
| Kalman + template gate | 22.62 | 23.85 | 72.6 | 72.3 | 37.45 | 37.69 | 379.6 |
| IMM filter | 26.55 | 28.67 | 68.2 | 67.6 | 42.70 | 44.73 | 191.2 |
| Forecast combination | 24.61 | 26.02 | 70.6 | 70.3 | 39.76 | 40.97 | 1239.3 |

## 2. MAE (us) per radar type, mean over error levels 1-3 [fixed]

| Method | `stable` | `jitter` | `stagger` | `dwell_and_switch` | `sliding` |
|---|---:|---:|---:|---:|---:|
| Rolling median | 0.07 | 40.51 | 98.85 | 149.94 | 80.80 |
| Period estimation | 0.05 | 39.82 | 46.75 | 23.32 | 12.48 |
| HMM | 0.21 | 39.96 | 47.80 | 42.87 | 47.52 |
| Kalman bank | 0.28 | 41.47 | 47.94 | 29.24 | 13.02 |
| Exp. smoothing | 0.43 | 40.07 | 48.68 | 46.89 | 14.37 |
| ARIMA | 0.09 | 39.85 | 48.82 | 42.40 | 14.74 |
| CDIF | **0.00** | 39.82 | 45.49 | 13.77 | 12.12 |
| SDIF | **0.00** | 39.82 | 45.49 | 13.77 | 12.12 |
| PRI transform | 0.32 | 39.82 | 48.06 | 148.16 | 38.15 |
| Lomb-Scargle | 0.10 | 39.82 | 45.49 | 14.33 | 12.12 |
| TOA grid fit | **0.00** | 39.82 | **45.47** | **13.73** | **12.09** |
| Period est. + template gate | 0.05 | 39.82 | 45.49 | 13.77 | 12.18 |
| Kalman + template gate | 0.18 | 41.47 | 45.51 | 13.76 | 12.17 |
| IMM filter | 0.23 | 41.24 | 48.17 | 30.09 | 13.04 |
| Forecast combination | 0.04 | **39.79** | 46.97 | 23.65 | 12.60 |

## 2. MAE (us) per radar type, mean over error levels 1-3 [varying]

| Method | `stable` | `jitter` | `stagger` | `dwell_and_switch` | `sliding` |
|---|---:|---:|---:|---:|---:|
| Rolling median | 0.07 | 48.46 | 100.17 | 169.52 | 82.95 |
| Period estimation | 0.05 | 47.84 | 48.31 | 19.89 | 12.29 |
| HMM | 0.13 | 47.91 | 50.15 | 45.30 | 47.98 |
| Kalman bank | 0.44 | 49.94 | 49.22 | 27.36 | 13.95 |
| Exp. smoothing | 0.08 | 48.10 | 50.28 | 54.75 | 15.16 |
| ARIMA | 0.10 | 47.84 | 51.18 | 46.82 | 15.23 |
| CDIF | **0.00** | 47.84 | 48.22 | 9.26 | 11.78 |
| SDIF | **0.00** | 47.84 | 48.22 | 9.26 | 11.78 |
| PRI transform | **0.00** | 47.84 | 51.15 | 150.87 | 33.44 |
| Lomb-Scargle | 0.10 | 47.84 | 48.22 | 11.16 | 11.89 |
| TOA grid fit | **0.00** | 47.84 | **48.20** | **9.09** | **11.75** |
| Period est. + template gate | 0.05 | 47.84 | 48.22 | 9.12 | 11.78 |
| Kalman + template gate | 0.18 | 49.94 | 48.25 | 9.11 | 11.78 |
| IMM filter | 0.21 | 49.68 | 49.54 | 30.12 | 13.80 |
| Forecast combination | 0.04 | **47.82** | 48.43 | 21.42 | 12.38 |

## 3. Gate hit rate (%) per radar type, mean over error levels 1-3 [fixed]

| Method | `stable` | `jitter` | `stagger` | `dwell_and_switch` | `sliding` |
|---|---:|---:|---:|---:|---:|
| Rolling median | **100.0** | 15.4 | 34.2 | 13.0 | 6.2 |
| Period estimation | **100.0** | **16.0** | 76.4 | 91.5 | 74.5 |
| HMM | 99.8 | **16.0** | 76.0 | 85.7 | 11.9 |
| Kalman bank | 99.8 | 15.1 | 72.2 | 81.7 | 73.6 |
| Exp. smoothing | 99.8 | 15.8 | 69.5 | 65.2 | 72.4 |
| ARIMA | 100.0 | 15.9 | 74.0 | 77.9 | 72.6 |
| CDIF | **100.0** | 16.0 | **77.2** | **95.5** | **75.2** |
| SDIF | **100.0** | 16.0 | **77.2** | **95.5** | **75.2** |
| PRI transform | 100.0 | 16.0 | 76.4 | 34.9 | 48.7 |
| Lomb-Scargle | **100.0** | 16.0 | **77.2** | 95.3 | **75.2** |
| TOA grid fit | **100.0** | 16.0 | **77.2** | **95.5** | **75.2** |
| Period est. + template gate | **100.0** | **16.0** | **77.2** | **95.5** | 75.1 |
| Kalman + template gate | **100.0** | 15.1 | **77.2** | **95.5** | 75.1 |
| IMM filter | 100.0 | 15.2 | 71.7 | 80.6 | 73.6 |
| Forecast combination | **100.0** | 15.8 | 75.6 | 87.2 | 74.4 |

## 3. Gate hit rate (%) per radar type, mean over error levels 1-3 [varying]

| Method | `stable` | `jitter` | `stagger` | `dwell_and_switch` | `sliding` |
|---|---:|---:|---:|---:|---:|
| Rolling median | **100.0** | 13.8 | 33.1 | 28.2 | 6.7 |
| Period estimation | **100.0** | 13.9 | 76.1 | 92.9 | 73.9 |
| HMM | 99.9 | 13.9 | 75.1 | 85.0 | 10.5 |
| Kalman bank | 99.7 | 13.4 | 71.8 | 83.1 | 72.5 |
| Exp. smoothing | **100.0** | 13.9 | 68.0 | 63.0 | 70.9 |
| ARIMA | 99.9 | **14.1** | 73.1 | 73.2 | 71.2 |
| CDIF | **100.0** | 13.9 | **76.2** | 97.1 | **74.9** |
| SDIF | **100.0** | 13.9 | **76.2** | 97.1 | **74.9** |
| PRI transform | **100.0** | 13.9 | 75.5 | 39.0 | 51.5 |
| Lomb-Scargle | **100.0** | 13.9 | **76.2** | 96.5 | 74.8 |
| TOA grid fit | **100.0** | 13.9 | **76.2** | **97.1** | **74.9** |
| Period est. + template gate | **100.0** | 13.9 | **76.2** | **97.1** | **74.9** |
| Kalman + template gate | **100.0** | 13.4 | **76.2** | **97.1** | 74.8 |
| IMM filter | 99.9 | 13.4 | 70.7 | 81.8 | 72.2 |
| Forecast combination | **100.0** | 14.0 | 75.1 | 88.5 | 73.7 |

## 4. Stagger and dwell-and-switch at error levels 2-3: MAE in us (hit rate in %) [fixed]

| Method | `stagger` lv2 | `stagger` lv3 | `dwell_and_switch` lv2 | `dwell_and_switch` lv3 |
|---|---:|---:|---:|---:|
| Rolling median | 99.0 (34) | 98.9 (34) | 150.2 (13) | 149.6 (22) |
| Period estimation | 46.7 (76) | 80.2 (59) | 22.9 (92) | 39.1 (86) |
| HMM | 48.0 (76) | 81.3 (59) | 46.8 (84) | 69.0 (77) |
| Kalman bank | 47.6 (73) | 82.3 (53) | 30.2 (81) | 47.6 (71) |
| Exp. smoothing | 48.2 (71) | 83.2 (45) | 47.1 (63) | 76.4 (47) |
| ARIMA | 47.4 (75) | 84.7 (55) | 38.8 (81) | 77.0 (58) |
| CDIF | **45.8 (77)** | **77.3 (61)** | **14.0 (95)** | 21.4 (93) |
| SDIF | **45.8 (77)** | **77.3 (61)** | **14.0 (95)** | 21.4 (93) |
| PRI transform | 47.2 (77) | 83.6 (59) | 150.0 (40) | 144.7 (43) |
| Lomb-Scargle | **45.8 (77)** | **77.3 (61)** | 14.6 (95) | 22.5 (93) |
| TOA grid fit | **45.7 (77)** | **77.3 (61)** | **13.9 (95)** | **21.4 (93)** |
| Period est. + template gate | **45.8 (77)** | **77.3 (61)** | **14.0 (95)** | 21.4 (93) |
| Kalman + template gate | **45.8 (77)** | 77.4 (61) | **14.0 (95)** | **21.4 (93)** |
| IMM filter | 48.2 (72) | 82.0 (52) | 31.5 (79) | 48.4 (69) |
| Forecast combination | 46.3 (76) | 81.2 (57) | 23.5 (87) | 40.1 (78) |

## 4. Stagger and dwell-and-switch at error levels 2-3: MAE in us (hit rate in %) [varying]

| Method | `stagger` lv2 | `stagger` lv3 | `dwell_and_switch` lv2 | `dwell_and_switch` lv3 |
|---|---:|---:|---:|---:|
| Rolling median | 100.5 (33) | 100.1 (33) | 169.6 (28) | 165.7 (32) |
| Period estimation | 50.4 (75) | **79.9 (61)** | 17.6 (94) | 37.9 (87) |
| HMM | 51.8 (74) | 82.1 (59) | 47.5 (84) | 78.9 (74) |
| Kalman bank | 51.4 (71) | 81.1 (53) | 27.2 (83) | 48.4 (71) |
| Exp. smoothing | 52.2 (68) | 82.3 (45) | 55.1 (61) | 93.1 (43) |
| ARIMA | 53.3 (73) | 83.9 (55) | 45.9 (75) | 84.0 (51) |
| CDIF | **49.8 (75)** | 80.2 (60) | **8.5 (97)** | 17.1 (95) |
| SDIF | **49.8 (75)** | 80.2 (60) | **8.5 (97)** | 17.1 (95) |
| PRI transform | 54.1 (74) | 84.6 (60) | 153.7 (41) | 154.2 (43) |
| Lomb-Scargle | **49.8 (75)** | 80.2 (60) | 10.7 (96) | 20.7 (94) |
| TOA grid fit | **49.7 (75)** | 80.2 (60) | **8.5 (97)** | **16.6 (95)** |
| Period est. + template gate | **49.8 (75)** | 80.2 (60) | **8.5 (97)** | 16.7 (95) |
| Kalman + template gate | 49.8 (75) | 80.3 (60) | **8.5 (97)** | **16.7 (95)** |
| IMM filter | 51.6 (70) | 81.3 (52) | 32.5 (81) | 51.2 (69) |
| Forecast combination | 50.3 (74) | 80.1 (58) | 20.6 (89) | 39.4 (79) |

## 5. Clean datasets (no receiver errors): mean MAE in us over the five radar types

| Method | fixed | varying |
|---|---:|---:|
| Rolling median | 73.88 | 80.85 |
| Period estimation | 8.05 | 9.59 |
| HMM | 16.05 | 16.73 |
| Kalman bank | 8.34 | 10.02 |
| Exp. smoothing | 8.08 | 9.68 |
| ARIMA | 8.05 | 9.60 |
| CDIF | 8.05 | 9.59 |
| SDIF | 8.05 | 9.59 |
| PRI transform | 54.05 | 41.80 |
| Lomb-Scargle | 8.05 | 9.59 |
| TOA grid fit | 8.05 | 9.59 |
| Period est. + template gate | 8.05 | 9.59 |
| Kalman + template gate | 8.34 | 10.02 |
| IMM filter | 8.29 | 9.97 |
| Forecast combination | 8.05 | 9.59 |

## 6. Where the remaining error comes from

The benchmark scores horizon row h against the PRI of the h-th *received* pulse. When a
pulse is missed (or a false pulse is received) inside the 32-pulse horizon, every later row
moves one step along the pattern. That event lies in the future, so no forecast that uses
only the context can follow it. The table splits the test sequences by whether the horizon
itself is undisturbed (all 32 rows are emitter pulses whose measured interval equals the
source PRI). Ground truth is used for this split only, not for forecasting.

| Profile | Radar type | Level | Undisturbed horizons (%) | Period estimation: MAE undisturbed / disturbed (us) | TOA grid fit: MAE undisturbed / disturbed (us) |
|---|---|---|---:|---:|---:|
| fixed | `stagger` | `error_lv1` | 86 | 0.03 / 92.0 | 0.02 / 92.0 |
| fixed | `stagger` | `error_lv2` | 59 | 2.64 / 110.1 | 0.11 / 111.4 |
| fixed | `stagger` | `error_lv3` | 18 | 0.23 / 97.7 | 0.18 / 94.2 |
| fixed | `dwell_and_switch` | `error_lv1` | 78 | 2.02 / 29.6 | 0.05 / 27.2 |
| fixed | `dwell_and_switch` | `error_lv2` | 49 | 10.55 / 34.8 | 0.23 / 27.1 |
| fixed | `dwell_and_switch` | `error_lv3` | 28 | 19.96 / 46.7 | 0.46 / 29.7 |
| fixed | `sliding` | `error_lv1` | 82 | 0.05 / 24.3 | 0.05 / 24.3 |
| fixed | `sliding` | `error_lv2` | 52 | 0.69 / 23.7 | 0.23 / 23.3 |
| fixed | `sliding` | `error_lv3` | 25 | 0.57 / 28.5 | 0.48 / 27.6 |
| varying | `stagger` | `error_lv1` | 84 | 0.03 / 94.7 | 0.02 / 94.7 |
| varying | `stagger` | `error_lv2` | 54 | 1.23 / 108.0 | 0.11 / 108.0 |
| varying | `stagger` | `error_lv3` | 26 | 0.31 / 107.1 | 0.20 / 107.5 |
| varying | `dwell_and_switch` | `error_lv1` | 86 | 2.37 / 15.8 | 0.05 / 15.4 |
| varying | `dwell_and_switch` | `error_lv2` | 50 | 13.51 / 21.6 | 0.26 / 16.6 |
| varying | `dwell_and_switch` | `error_lv3` | 21 | 29.13 / 40.3 | 0.52 / 20.9 |
| varying | `sliding` | `error_lv1` | 82 | 0.05 / 20.5 | 0.04 / 19.6 |
| varying | `sliding` | `error_lv2` | 52 | 1.82 / 24.4 | 0.24 / 23.0 |
| varying | `sliding` | `error_lv3` | 24 | 0.57 / 26.3 | 0.43 / 26.4 |
