# Train: Fixed | Test: Varying [Univariate PRI]

**Evaluated on**: 2026-10-27 00:15:27

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.16** | 0.18 | 100.0% |
| `stable` | `error_lv2` | 200 | **1.15** | 2.20 | 99.8% |
| `stable` | `error_lv3` | 200 | **1.24** | 1.48 | 99.6% |
| `jitter` | `clean` | 200 | **48.67** | 60.15 | 13.1% |
| `jitter` | `error_lv1` | 200 | **47.85** | 59.48 | 13.4% |
| `jitter` | `error_lv2` | 200 | **48.92** | 60.76 | 13.4% |
| `jitter` | `error_lv3` | 200 | **48.39** | 60.22 | 14.1% |
| `stagger` | `clean` | 200 | **0.72** | 0.94 | 100.0% |
| `stagger` | `error_lv1` | 200 | **25.77** | 33.22 | 74.2% |
| `stagger` | `error_lv2` | 200 | **62.46** | 80.23 | 36.1% |
| `stagger` | `error_lv3` | 200 | **96.68** | 118.91 | 15.3% |
| `dwell_and_switch` | `clean` | 200 | **6.88** | 10.35 | 76.9% |
| `dwell_and_switch` | `error_lv1` | 200 | **16.66** | 32.29 | 67.1% |
| `dwell_and_switch` | `error_lv2` | 200 | **32.69** | 60.53 | 49.0% |
| `dwell_and_switch` | `error_lv3` | 200 | **53.77** | 88.02 | 32.1% |
| `sliding` | `clean` | 200 | **6.66** | 9.65 | 84.1% |
| `sliding` | `error_lv1` | 200 | **15.37** | 26.29 | 64.7% |
| `sliding` | `error_lv2` | 200 | **33.72** | 51.78 | 35.1% |
| `sliding` | `error_lv3` | 200 | **46.78** | 67.44 | 23.5% |