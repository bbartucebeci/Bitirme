# TimesFM 3.0 Zero-Shot Benchmark Report [PRI Varying]

**Evaluated on**: 2026-10-26 22:12:22

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.12** | 0.15 | 100.0% |
| `stable` | `error_lv2` | 200 | **2.10** | 3.39 | 99.6% |
| `stable` | `error_lv3` | 200 | **1.34** | 1.71 | 98.6% |
| `jitter` | `clean` | 200 | **48.70** | 60.20 | 13.2% |
| `jitter` | `error_lv1` | 200 | **48.07** | 59.78 | 13.6% |
| `jitter` | `error_lv2` | 200 | **49.13** | 61.08 | 13.4% |
| `jitter` | `error_lv3` | 200 | **49.30** | 61.33 | 13.4% |
| `stagger` | `clean` | 200 | **2.56** | 3.11 | 99.9% |
| `stagger` | `error_lv1` | 200 | **40.86** | 50.84 | 61.5% |
| `stagger` | `error_lv2` | 200 | **79.23** | 96.66 | 21.4% |
| `stagger` | `error_lv3` | 200 | **101.62** | 120.98 | 8.8% |
| `dwell_and_switch` | `clean` | 200 | **14.26** | 19.75 | 58.2% |
| `dwell_and_switch` | `error_lv1` | 200 | **24.89** | 39.01 | 51.7% |
| `dwell_and_switch` | `error_lv2` | 200 | **40.76** | 66.43 | 38.0% |
| `dwell_and_switch` | `error_lv3` | 200 | **63.17** | 91.64 | 22.4% |
| `sliding` | `clean` | 200 | **30.16** | 38.09 | 56.2% |
| `sliding` | `error_lv1` | 200 | **33.70** | 47.08 | 44.6% |
| `sliding` | `error_lv2` | 200 | **46.92** | 64.31 | 25.2% |
| `sliding` | `error_lv3` | 200 | **62.71** | 82.02 | 15.7% |