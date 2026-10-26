# TimesFM 3.0 Zero-Shot Benchmark Report [Pulse Width Fixed]

**Evaluated on**: 2026-10-26 18:54:29

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-0.1us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.01** | 0.04 | 99.9% |
| `stable` | `error_lv2` | 200 | **0.04** | 0.12 | 99.3% |
| `stable` | `error_lv3` | 200 | **0.07** | 0.21 | 94.0% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.01** | 0.04 | 99.9% |
| `jitter` | `error_lv2` | 200 | **0.04** | 0.11 | 99.2% |
| `jitter` | `error_lv3` | 200 | **0.08** | 0.27 | 93.9% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.01** | 0.03 | 100.0% |
| `stagger` | `error_lv2` | 200 | **0.06** | 0.16 | 98.3% |
| `stagger` | `error_lv3` | 200 | **0.08** | 0.23 | 93.0% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.01** | 0.03 | 99.9% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.04** | 0.10 | 99.5% |
| `dwell_and_switch` | `error_lv3` | 200 | **0.08** | 0.23 | 93.9% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.01** | 0.02 | 99.9% |
| `sliding` | `error_lv2` | 200 | **0.04** | 0.10 | 99.6% |
| `sliding` | `error_lv3` | 200 | **0.08** | 0.25 | 94.3% |