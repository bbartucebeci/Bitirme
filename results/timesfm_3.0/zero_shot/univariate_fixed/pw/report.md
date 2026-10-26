# TimesFM 3.0 Zero-Shot Benchmark Report [Pulse Width Fixed]

**Evaluated on**: 2026-10-26 20:04:50

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-0.1us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.01** | 0.01 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.03** | 0.04 | 99.7% |
| `stable` | `error_lv3` | 200 | **0.04** | 0.06 | 94.8% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.01** | 0.01 | 100.0% |
| `jitter` | `error_lv2` | 200 | **0.03** | 0.03 | 99.7% |
| `jitter` | `error_lv3` | 200 | **0.04** | 0.05 | 95.0% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.01** | 0.01 | 100.0% |
| `stagger` | `error_lv2` | 200 | **0.04** | 0.06 | 98.8% |
| `stagger` | `error_lv3` | 200 | **0.04** | 0.06 | 93.9% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.01** | 0.01 | 100.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.03** | 0.03 | 99.9% |
| `dwell_and_switch` | `error_lv3` | 200 | **0.05** | 0.06 | 94.9% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.01** | 0.01 | 100.0% |
| `sliding` | `error_lv2` | 200 | **0.02** | 0.03 | 99.9% |
| `sliding` | `error_lv3` | 200 | **0.04** | 0.05 | 95.4% |