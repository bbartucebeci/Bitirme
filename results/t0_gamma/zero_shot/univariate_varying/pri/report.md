# t0-gamma Zero-Shot Univariate Benchmark [PRI Varying]

**Evaluated on**: 2026-11-09 03:07:54

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.16** | 0.17 | 100.0% |
| `stable` | `error_lv2` | 200 | **4.80** | 5.21 | 98.9% |
| `stable` | `error_lv3` | 200 | **1.10** | 1.45 | 99.6% |
| `jitter` | `clean` | 200 | **49.22** | 60.82 | 12.9% |
| `jitter` | `error_lv1` | 200 | **48.42** | 60.24 | 13.3% |
| `jitter` | `error_lv2` | 200 | **49.15** | 61.14 | 13.5% |
| `jitter` | `error_lv3` | 200 | **54.91** | 67.49 | 13.9% |
| `stagger` | `clean` | 200 | **4.06** | 4.78 | 96.2% |
| `stagger` | `error_lv1` | 200 | **32.38** | 42.37 | 65.4% |
| `stagger` | `error_lv2` | 200 | **70.85** | 92.21 | 27.7% |
| `stagger` | `error_lv3` | 200 | **99.34** | 126.86 | 12.7% |
| `dwell_and_switch` | `clean` | 200 | **0.88** | 1.17 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **10.46** | 25.57 | 92.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **23.52** | 58.00 | 80.8% |
| `dwell_and_switch` | `error_lv3` | 200 | **44.05** | 90.29 | 60.3% |
| `sliding` | `clean` | 200 | **3.54** | 4.23 | 96.1% |
| `sliding` | `error_lv1` | 200 | **13.10** | 25.44 | 76.1% |
| `sliding` | `error_lv2` | 200 | **32.25** | 55.24 | 43.0% |
| `sliding` | `error_lv3` | 200 | **45.57** | 71.75 | 29.5% |