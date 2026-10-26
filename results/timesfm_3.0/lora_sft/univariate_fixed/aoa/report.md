# TimesFM 3.0 LoRA Fine-Tuned (SFT) Benchmark Report [Angle of Arrival Fixed]

**Evaluated on**: 2026-10-26 20:25:07

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (deg) | RMSE (deg) | Gate Hit Rate (+/-2deg) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.17** | 0.21 | 100.0% |
| `stable` | `error_lv3` | 200 | **0.40** | 0.50 | 100.0% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `jitter` | `error_lv2` | 200 | **0.17** | 0.20 | 100.0% |
| `jitter` | `error_lv3` | 200 | **0.41** | 0.50 | 100.0% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `stagger` | `error_lv2` | 200 | **0.17** | 0.22 | 99.9% |
| `stagger` | `error_lv3` | 200 | **0.41** | 0.51 | 100.0% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.17** | 0.21 | 100.0% |
| `dwell_and_switch` | `error_lv3` | 200 | **0.41** | 0.51 | 100.0% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `sliding` | `error_lv2` | 200 | **0.17** | 0.21 | 100.0% |
| `sliding` | `error_lv3` | 200 | **0.43** | 0.57 | 99.9% |