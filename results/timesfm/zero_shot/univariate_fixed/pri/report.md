# TimesFM 3.0 Zero-Shot Benchmark Report [PRI Fixed]

**Evaluated on**: 2026-10-26 19:55:23

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.29** | 0.60 | 99.8% |
| `stable` | `error_lv2` | 200 | **1.65** | 2.55 | 98.3% |
| `stable` | `error_lv3` | 200 | **1.44** | 2.18 | 99.6% |
| `jitter` | `clean` | 200 | **39.94** | 49.54 | 15.5% |
| `jitter` | `error_lv1` | 200 | **40.66** | 50.85 | 15.5% |
| `jitter` | `error_lv2` | 200 | **41.58** | 51.41 | 14.5% |
| `jitter` | `error_lv3` | 200 | **41.06** | 51.02 | 15.5% |
| `stagger` | `clean` | 200 | **2.69** | 3.23 | 100.0% |
| `stagger` | `error_lv1` | 200 | **41.04** | 50.88 | 61.7% |
| `stagger` | `error_lv2` | 200 | **80.01** | 97.32 | 27.2% |
| `stagger` | `error_lv3` | 200 | **98.25** | 117.67 | 15.4% |
| `dwell_and_switch` | `clean` | 200 | **25.34** | 35.14 | 37.5% |
| `dwell_and_switch` | `error_lv1` | 200 | **34.01** | 50.77 | 36.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **53.20** | 75.04 | 25.8% |
| `dwell_and_switch` | `error_lv3` | 200 | **76.11** | 101.42 | 17.8% |
| `sliding` | `clean` | 200 | **71.04** | 87.51 | 15.6% |
| `sliding` | `error_lv1` | 200 | **57.23** | 72.81 | 22.2% |
| `sliding` | `error_lv2` | 200 | **55.11** | 72.18 | 19.8% |
| `sliding` | `error_lv3` | 200 | **60.90** | 77.75 | 13.7% |