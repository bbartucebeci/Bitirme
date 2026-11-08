# TimesFM 3.0 Zero-Shot Benchmark Report [Amplitude Varying]

**Evaluated on**: 2026-10-26 22:14:17

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (dBm) | RMSE (dBm) | Gate Hit Rate (+/-2dBm) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.16** | 0.20 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.41** | 0.51 | 100.0% |
| `stable` | `error_lv3` | 200 | **0.82** | 1.01 | 94.8% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.17** | 0.22 | 99.9% |
| `jitter` | `error_lv2` | 200 | **0.41** | 0.50 | 100.0% |
| `jitter` | `error_lv3` | 200 | **0.81** | 1.01 | 94.8% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.16** | 0.20 | 100.0% |
| `stagger` | `error_lv2` | 200 | **0.41** | 0.51 | 100.0% |
| `stagger` | `error_lv3` | 200 | **0.81** | 1.01 | 94.8% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.16** | 0.20 | 100.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.40** | 0.50 | 100.0% |
| `dwell_and_switch` | `error_lv3` | 200 | **0.82** | 1.03 | 94.8% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.16** | 0.20 | 100.0% |
| `sliding` | `error_lv2` | 200 | **0.41** | 0.51 | 100.0% |
| `sliding` | `error_lv3` | 200 | **0.82** | 1.02 | 95.0% |