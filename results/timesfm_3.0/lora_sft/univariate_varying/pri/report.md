# TimesFM 3.0 LoRA Fine-Tuned (SFT) Benchmark Report [PRI Varying]

**Evaluated on**: 2026-10-26 22:24:49

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.14** | 0.16 | 100.0% |
| `stable` | `error_lv2` | 200 | **1.29** | 2.49 | 99.7% |
| `stable` | `error_lv3` | 200 | **1.24** | 1.49 | 99.8% |
| `jitter` | `clean` | 200 | **48.67** | 60.14 | 13.0% |
| `jitter` | `error_lv1` | 200 | **47.78** | 59.41 | 13.3% |
| `jitter` | `error_lv2` | 200 | **48.88** | 60.71 | 13.1% |
| `jitter` | `error_lv3` | 200 | **48.42** | 60.22 | 14.3% |
| `stagger` | `clean` | 200 | **0.35** | 0.46 | 100.0% |
| `stagger` | `error_lv1` | 200 | **25.12** | 32.53 | 74.9% |
| `stagger` | `error_lv2` | 200 | **61.20** | 79.74 | 37.7% |
| `stagger` | `error_lv3` | 200 | **95.00** | 119.25 | 16.0% |
| `dwell_and_switch` | `clean` | 200 | **0.46** | 0.57 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **10.70** | 24.02 | 84.1% |
| `dwell_and_switch` | `error_lv2` | 200 | **24.77** | 51.49 | 60.5% |
| `dwell_and_switch` | `error_lv3` | 200 | **42.70** | 77.57 | 38.7% |
| `sliding` | `clean` | 200 | **0.57** | 0.72 | 100.0% |
| `sliding` | `error_lv1` | 200 | **9.81** | 19.62 | 77.0% |
| `sliding` | `error_lv2` | 200 | **26.19** | 44.60 | 43.8% |
| `sliding` | `error_lv3` | 200 | **38.39** | 60.02 | 27.9% |