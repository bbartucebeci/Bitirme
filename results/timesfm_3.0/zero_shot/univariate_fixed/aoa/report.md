# TimesFM 3.0 Zero-Shot Benchmark Report [Angle of Arrival Fixed]

**Evaluated on**: 2026-10-26 20:05:35

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (deg) | RMSE (deg) | Gate Hit Rate (+/-2deg) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.18** | 0.26 | 99.9% |
| `stable` | `error_lv3` | 200 | **0.40** | 0.50 | 100.0% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `jitter` | `error_lv2` | 200 | **0.32** | 0.46 | 99.7% |
| `jitter` | `error_lv3` | 200 | **0.41** | 0.51 | 99.9% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `stagger` | `error_lv2` | 200 | **0.83** | 1.34 | 98.6% |
| `stagger` | `error_lv3` | 200 | **0.55** | 0.71 | 99.6% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.30** | 0.45 | 99.5% |
| `dwell_and_switch` | `error_lv3` | 200 | **0.53** | 0.73 | 99.7% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `sliding` | `error_lv2` | 200 | **0.32** | 0.45 | 99.6% |
| `sliding` | `error_lv3` | 200 | **0.45** | 0.61 | 99.9% |