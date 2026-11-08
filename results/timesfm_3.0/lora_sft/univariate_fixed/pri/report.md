# TimesFM 3.0 LoRA Fine-Tuned (SFT) Benchmark Report [PRI Fixed]

**Evaluated on**: 2026-10-26 20:02:52

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.20** | 0.49 | 99.9% |
| `stable` | `error_lv2` | 200 | **0.67** | 0.84 | 99.4% |
| `stable` | `error_lv3` | 200 | **1.21** | 1.59 | 99.8% |
| `jitter` | `clean` | 200 | **39.89** | 49.48 | 15.6% |
| `jitter` | `error_lv1` | 200 | **40.44** | 50.63 | 15.6% |
| `jitter` | `error_lv2` | 200 | **40.61** | 50.27 | 14.5% |
| `jitter` | `error_lv3` | 200 | **40.60** | 50.39 | 15.2% |
| `stagger` | `clean` | 200 | **0.33** | 0.42 | 100.0% |
| `stagger` | `error_lv1` | 200 | **28.37** | 37.48 | 74.5% |
| `stagger` | `error_lv2` | 200 | **70.61** | 88.25 | 39.7% |
| `stagger` | `error_lv3` | 200 | **95.80** | 116.88 | 18.1% |
| `dwell_and_switch` | `clean` | 200 | **0.25** | 0.34 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **8.84** | 22.89 | 91.4% |
| `dwell_and_switch` | `error_lv2` | 200 | **23.01** | 50.18 | 70.6% |
| `dwell_and_switch` | `error_lv3` | 200 | **39.78** | 78.63 | 50.0% |
| `sliding` | `clean` | 200 | **0.39** | 0.47 | 100.0% |
| `sliding` | `error_lv1` | 200 | **6.74** | 12.61 | 84.1% |
| `sliding` | `error_lv2` | 200 | **18.69** | 35.26 | 56.4% |
| `sliding` | `error_lv3` | 200 | **33.10** | 57.95 | 33.8% |