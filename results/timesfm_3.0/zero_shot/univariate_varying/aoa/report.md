# TimesFM 3.0 Zero-Shot Benchmark Report [Angle of Arrival Varying]

**Evaluated on**: 2026-10-26 22:13:46

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (deg) | RMSE (deg) | Gate Hit Rate (+/-2deg) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.17** | 0.21 | 100.0% |
| `stable` | `error_lv3` | 200 | **0.47** | 0.62 | 99.7% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.24** | 0.39 | 99.4% |
| `jitter` | `error_lv2` | 200 | **0.17** | 0.21 | 100.0% |
| `jitter` | `error_lv3` | 200 | **0.42** | 0.53 | 100.0% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.45** | 0.89 | 99.5% |
| `stagger` | `error_lv2` | 200 | **0.97** | 1.38 | 99.5% |
| `stagger` | `error_lv3` | 200 | **1.76** | 2.62 | 99.4% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.21** | 0.30 | 99.8% |
| `dwell_and_switch` | `error_lv3` | 200 | **0.55** | 0.76 | 99.7% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `sliding` | `error_lv2` | 200 | **0.16** | 0.20 | 100.0% |
| `sliding` | `error_lv3` | 200 | **0.86** | 1.23 | 99.5% |