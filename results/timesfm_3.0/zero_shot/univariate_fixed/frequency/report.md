# TimesFM 3.0 Zero-Shot Benchmark Report [Carrier Frequency Fixed]

**Evaluated on**: 2026-10-26 20:04:06

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (MHz) | RMSE (MHz) | Gate Hit Rate (+/-2MHz) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.13** | 0.16 | 99.5% |
| `stable` | `error_lv2` | 200 | **4.55** | 8.40 | 92.5% |
| `stable` | `error_lv3` | 200 | **1.52** | 1.78 | 79.0% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.16** | 0.19 | 99.2% |
| `jitter` | `error_lv2` | 200 | **2.04** | 3.57 | 91.5% |
| `jitter` | `error_lv3` | 200 | **1.61** | 1.89 | 75.9% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.27** | 0.31 | 97.0% |
| `stagger` | `error_lv2` | 200 | **23.23** | 42.78 | 89.6% |
| `stagger` | `error_lv3` | 200 | **2.00** | 2.85 | 77.4% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.14** | 0.17 | 99.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **3.04** | 4.61 | 90.8% |
| `dwell_and_switch` | `error_lv3` | 200 | **6.18** | 10.30 | 77.4% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.16** | 0.18 | 98.6% |
| `sliding` | `error_lv2` | 200 | **1.79** | 2.56 | 91.8% |
| `sliding` | `error_lv3` | 200 | **1.65** | 1.91 | 79.3% |