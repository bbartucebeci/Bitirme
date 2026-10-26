# TimesFM 3.0 Zero-Shot Benchmark Report [Carrier Frequency Fixed]

**Evaluated on**: 2026-10-26 18:53:34

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (MHz) | RMSE (MHz) | Gate Hit Rate (+/-2MHz) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **2.67** | 14.24 | 99.3% |
| `stable` | `error_lv2` | 200 | **19.54** | 93.12 | 92.2% |
| `stable` | `error_lv3` | 200 | **38.30** | 192.06 | 78.2% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **4.57** | 23.88 | 99.0% |
| `jitter` | `error_lv2` | 200 | **19.19** | 99.46 | 91.1% |
| `jitter` | `error_lv3` | 200 | **50.08** | 257.97 | 75.0% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **2.21** | 11.29 | 97.0% |
| `stagger` | `error_lv2` | 200 | **44.47** | 158.77 | 89.1% |
| `stagger` | `error_lv3` | 200 | **49.72** | 253.71 | 76.6% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **4.11** | 22.59 | 98.9% |
| `dwell_and_switch` | `error_lv2` | 200 | **20.85** | 96.56 | 90.5% |
| `dwell_and_switch` | `error_lv3` | 200 | **45.33** | 218.19 | 76.5% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **3.27** | 17.79 | 98.5% |
| `sliding` | `error_lv2` | 200 | **13.18** | 66.87 | 91.5% |
| `sliding` | `error_lv3` | 200 | **44.68** | 232.76 | 78.4% |