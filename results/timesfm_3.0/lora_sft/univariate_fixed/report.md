# TimesFM 3.0 LoRA Fine-Tuned (SFT) Benchmark Report [Univariate Fixed]

**Evaluated on**: 2026-10-21 12:37:04

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **5.62** | 26.95 | 99.3% |
| `stable` | `error_lv2` | 200 | **18.27** | 81.61 | 97.2% |
| `stable` | `error_lv3` | 200 | **40.95** | 156.37 | 95.2% |
| `jitter` | `clean` | 200 | **39.87** | 49.47 | 15.7% |
| `jitter` | `error_lv1` | 200 | **45.65** | 72.47 | 15.8% |
| `jitter` | `error_lv2` | 200 | **58.54** | 117.92 | 14.4% |
| `jitter` | `error_lv3` | 200 | **77.86** | 172.25 | 14.2% |
| `stagger` | `clean` | 200 | **0.33** | 0.42 | 100.0% |
| `stagger` | `error_lv1` | 200 | **32.17** | 52.04 | 75.8% |
| `stagger` | `error_lv2` | 200 | **87.07** | 140.39 | 41.3% |
| `stagger` | `error_lv3` | 200 | **128.59** | 207.07 | 18.4% |
| `dwell_and_switch` | `clean` | 200 | **0.58** | 0.96 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **16.05** | 49.65 | 91.7% |
| `dwell_and_switch` | `error_lv2` | 200 | **38.35** | 101.29 | 71.3% |
| `dwell_and_switch` | `error_lv3` | 200 | **75.65** | 185.45 | 49.3% |
| `sliding` | `clean` | 200 | **0.29** | 0.36 | 100.0% |
| `sliding` | `error_lv1` | 200 | **10.36** | 26.21 | 85.7% |
| `sliding` | `error_lv2` | 200 | **32.63** | 87.43 | 57.5% |
| `sliding` | `error_lv3` | 200 | **74.25** | 190.34 | 34.6% |