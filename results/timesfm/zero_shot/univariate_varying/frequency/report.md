# TimesFM 3.0 Zero-Shot Benchmark Report [Carrier Frequency Varying]

**Evaluated on**: 2026-10-26 22:12:50

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (MHz) | RMSE (MHz) | Gate Hit Rate (+/-2MHz) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.18** | 0.21 | 98.2% |
| `stable` | `error_lv2` | 200 | **2.03** | 3.18 | 92.5% |
| `stable` | `error_lv3` | 200 | **1.59** | 2.19 | 81.5% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **18.29** | 29.90 | 96.6% |
| `jitter` | `error_lv2` | 200 | **0.85** | 0.99 | 92.4% |
| `jitter` | `error_lv3` | 200 | **10.00** | 16.25 | 75.0% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.20** | 0.24 | 98.6% |
| `stagger` | `error_lv2` | 200 | **0.75** | 0.89 | 93.0% |
| `stagger` | `error_lv3` | 200 | **2.63** | 4.92 | 79.1% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.20** | 0.23 | 97.7% |
| `dwell_and_switch` | `error_lv2` | 200 | **8.04** | 10.70 | 92.3% |
| `dwell_and_switch` | `error_lv3` | 200 | **7.03** | 11.16 | 76.7% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.16** | 0.19 | 99.0% |
| `sliding` | `error_lv2` | 200 | **0.70** | 0.83 | 93.5% |
| `sliding` | `error_lv3` | 200 | **8.62** | 12.37 | 79.7% |