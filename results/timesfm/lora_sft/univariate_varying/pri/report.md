# TimesFM 3.0 LoRA Fine-Tuned (SFT) Benchmark Report [PRI Varying]

**Evaluated on**: 2026-11-09 13:37:11

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.15** | 0.17 | 100.0% |
| `stable` | `error_lv2` | 200 | **1.36** | 2.58 | 99.7% |
| `stable` | `error_lv3` | 200 | **1.23** | 1.47 | 99.7% |
| `jitter` | `clean` | 200 | **48.66** | 60.13 | 13.1% |
| `jitter` | `error_lv1` | 200 | **47.78** | 59.42 | 13.3% |
| `jitter` | `error_lv2` | 200 | **48.88** | 60.72 | 13.2% |
| `jitter` | `error_lv3` | 200 | **48.45** | 60.25 | 14.3% |
| `stagger` | `clean` | 200 | **0.33** | 0.43 | 100.0% |
| `stagger` | `error_lv1` | 200 | **25.14** | 32.51 | 74.8% |
| `stagger` | `error_lv2` | 200 | **61.16** | 79.70 | 37.9% |
| `stagger` | `error_lv3` | 200 | **94.89** | 119.16 | 15.8% |
| `dwell_and_switch` | `clean` | 200 | **0.45** | 0.57 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **10.68** | 23.96 | 84.5% |
| `dwell_and_switch` | `error_lv2` | 200 | **24.70** | 51.39 | 60.3% |
| `dwell_and_switch` | `error_lv3` | 200 | **42.46** | 77.32 | 39.3% |
| `sliding` | `clean` | 200 | **0.52** | 0.66 | 100.0% |
| `sliding` | `error_lv1` | 200 | **9.80** | 19.69 | 77.0% |
| `sliding` | `error_lv2` | 200 | **26.10** | 44.57 | 44.0% |
| `sliding` | `error_lv3` | 200 | **38.10** | 59.79 | 28.1% |