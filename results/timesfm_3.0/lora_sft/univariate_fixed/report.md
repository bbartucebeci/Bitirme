# TimesFM 3.0 LoRA Fine-Tuned (SFT) Benchmark Report [PRI Fixed]

**Evaluated on**: 2026-10-26 18:52:18

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **5.64** | 26.98 | 99.2% |
| `stable` | `error_lv2` | 200 | **18.27** | 81.69 | 97.3% |
| `stable` | `error_lv3` | 200 | **41.00** | 156.40 | 95.1% |
| `jitter` | `clean` | 200 | **39.90** | 49.49 | 15.6% |
| `jitter` | `error_lv1` | 200 | **45.72** | 72.50 | 15.4% |
| `jitter` | `error_lv2` | 200 | **58.63** | 118.05 | 14.2% |
| `jitter` | `error_lv3` | 200 | **77.96** | 172.22 | 14.2% |
| `stagger` | `clean` | 200 | **0.30** | 0.37 | 100.0% |
| `stagger` | `error_lv1` | 200 | **33.20** | 53.17 | 74.6% |
| `stagger` | `error_lv2` | 200 | **88.69** | 141.95 | 39.5% |
| `stagger` | `error_lv3` | 200 | **129.92** | 208.19 | 16.7% |
| `dwell_and_switch` | `clean` | 200 | **0.28** | 0.37 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **16.27** | 49.81 | 90.7% |
| `dwell_and_switch` | `error_lv2` | 200 | **39.25** | 102.34 | 69.9% |
| `dwell_and_switch` | `error_lv3` | 200 | **76.72** | 185.99 | 46.9% |
| `sliding` | `clean` | 200 | **0.34** | 0.42 | 100.0% |
| `sliding` | `error_lv1` | 200 | **10.86** | 26.82 | 83.7% |
| `sliding` | `error_lv2` | 200 | **33.26** | 88.01 | 56.1% |
| `sliding` | `error_lv3` | 200 | **74.93** | 190.74 | 33.1% |