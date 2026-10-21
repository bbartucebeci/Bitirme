# TimesFM 3.0 Zero-Shot Benchmark Report

**Evaluated on**: 2026-10-21 11:47:12

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **5.74** | 27.15 | 99.1% |
| `stable` | `error_lv2` | 200 | **19.20** | 83.10 | 96.3% |
| `stable` | `error_lv3` | 200 | **41.17** | 156.51 | 94.9% |
| `jitter` | `clean` | 200 | **39.94** | 49.54 | 15.5% |
| `jitter` | `error_lv1` | 200 | **45.95** | 72.68 | 15.4% |
| `jitter` | `error_lv2` | 200 | **59.60** | 119.21 | 13.9% |
| `jitter` | `error_lv3` | 200 | **78.33** | 172.33 | 14.5% |
| `stagger` | `clean` | 200 | **2.69** | 3.23 | 100.0% |
| `stagger` | `error_lv1` | 200 | **46.06** | 67.12 | 61.7% |
| `stagger` | `error_lv2` | 200 | **98.50** | 152.13 | 26.9% |
| `stagger` | `error_lv3` | 200 | **132.91** | 211.77 | 14.8% |
| `dwell_and_switch` | `clean` | 200 | **25.34** | 35.14 | 37.5% |
| `dwell_and_switch` | `error_lv1` | 200 | **41.22** | 77.45 | 35.8% |
| `dwell_and_switch` | `error_lv2` | 200 | **68.86** | 126.66 | 25.1% |
| `dwell_and_switch` | `error_lv3` | 200 | **110.81** | 202.12 | 17.1% |
| `sliding` | `clean` | 200 | **71.04** | 87.51 | 15.6% |
| `sliding` | `error_lv1` | 200 | **61.11** | 85.70 | 22.1% |
| `sliding` | `error_lv2` | 200 | **69.33** | 121.26 | 19.4% |
| `sliding` | `error_lv3` | 200 | **101.50** | 202.89 | 12.9% |