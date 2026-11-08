# TimesFM 3.0 Zero-Shot Benchmark Report [Pulse Width Varying]

**Evaluated on**: 2026-10-26 22:13:18

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-0.1us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.01** | 0.01 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.03** | 0.03 | 100.0% |
| `stable` | `error_lv3` | 200 | **0.04** | 0.05 | 95.1% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.01** | 0.02 | 99.5% |
| `jitter` | `error_lv2` | 200 | **0.02** | 0.03 | 99.9% |
| `jitter` | `error_lv3` | 200 | **0.04** | 0.05 | 94.5% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.01** | 0.01 | 100.0% |
| `stagger` | `error_lv2` | 200 | **0.02** | 0.03 | 99.9% |
| `stagger` | `error_lv3` | 200 | **0.04** | 0.05 | 95.1% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.01** | 0.01 | 100.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.02** | 0.03 | 100.0% |
| `dwell_and_switch` | `error_lv3` | 200 | **0.04** | 0.05 | 94.6% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.01** | 0.01 | 100.0% |
| `sliding` | `error_lv2` | 200 | **0.02** | 0.03 | 99.9% |
| `sliding` | `error_lv3` | 200 | **0.04** | 0.05 | 94.6% |