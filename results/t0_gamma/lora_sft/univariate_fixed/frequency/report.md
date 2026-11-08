# t0-gamma Zero-Shot Univariate Benchmark [frequency Fixed]

**Evaluated on**: 2026-11-08 18:00:19

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (units) | RMSE (units) | Gate Hit Rate (+/-1units) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.19** | 0.22 | 96.7% |
| `stable` | `error_lv2` | 200 | **2.23** | 6.56 | 77.3% |
| `stable` | `error_lv3` | 200 | **55.45** | 59.94 | 48.4% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.20** | 0.23 | 96.0% |
| `jitter` | `error_lv2` | 200 | **3.90** | 4.73 | 75.5% |
| `jitter` | `error_lv3` | 200 | **2.10** | 2.52 | 47.5% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.18** | 0.20 | 97.0% |
| `stagger` | `error_lv2` | 200 | **1.18** | 1.33 | 75.2% |
| `stagger` | `error_lv3` | 200 | **30.70** | 31.02 | 48.0% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.23** | 0.27 | 96.4% |
| `dwell_and_switch` | `error_lv2` | 200 | **7.49** | 7.62 | 80.8% |
| `dwell_and_switch` | `error_lv3` | 200 | **3.37** | 5.64 | 50.5% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.18** | 0.21 | 95.7% |
| `sliding` | `error_lv2` | 200 | **1.17** | 1.32 | 74.8% |
| `sliding` | `error_lv3` | 200 | **24.12** | 24.42 | 43.4% |