# Train: Varying | Test: Fixed [Univariate PRI]

**Evaluated on**: 2026-10-27 00:17:44

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.16** | 0.37 | 99.9% |
| `stable` | `error_lv2` | 200 | **0.71** | 0.87 | 98.9% |
| `stable` | `error_lv3` | 200 | **1.19** | 1.51 | 99.9% |
| `jitter` | `clean` | 200 | **39.87** | 49.47 | 15.5% |
| `jitter` | `error_lv1` | 200 | **40.40** | 50.58 | 15.5% |
| `jitter` | `error_lv2` | 200 | **40.62** | 50.32 | 14.8% |
| `jitter` | `error_lv3` | 200 | **40.58** | 50.39 | 15.3% |
| `stagger` | `clean` | 200 | **0.90** | 1.15 | 100.0% |
| `stagger` | `error_lv1` | 200 | **28.86** | 38.01 | 71.1% |
| `stagger` | `error_lv2` | 200 | **70.49** | 87.60 | 36.4% |
| `stagger` | `error_lv3` | 200 | **96.03** | 116.47 | 14.0% |
| `dwell_and_switch` | `clean` | 200 | **0.40** | 0.49 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **10.58** | 24.71 | 85.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **27.28** | 54.35 | 58.0% |
| `dwell_and_switch` | `error_lv3` | 200 | **45.03** | 82.62 | 40.0% |
| `sliding` | `clean` | 200 | **0.52** | 0.62 | 100.0% |
| `sliding` | `error_lv1` | 200 | **8.55** | 15.13 | 78.4% |
| `sliding` | `error_lv2` | 200 | **21.67** | 38.20 | 48.9% |
| `sliding` | `error_lv3` | 200 | **36.46** | 59.66 | 29.5% |