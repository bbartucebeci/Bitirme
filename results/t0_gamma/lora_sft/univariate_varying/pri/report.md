# t0-gamma Zero-Shot Univariate Benchmark [pri Varying]

**Evaluated on**: 2026-11-08 18:02:02

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (units) | RMSE (units) | Gate Hit Rate (+/-1units) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **2.07** | 3.33 | 93.1% |
| `stable` | `error_lv2` | 200 | **1.62** | 2.52 | 86.3% |
| `stable` | `error_lv3` | 200 | **1.11** | 1.56 | 67.7% |
| `jitter` | `clean` | 200 | **47.83** | 59.62 | 1.4% |
| `jitter` | `error_lv1` | 200 | **49.28** | 61.31 | 1.4% |
| `jitter` | `error_lv2` | 200 | **49.57** | 61.97 | 1.3% |
| `jitter` | `error_lv3` | 200 | **50.59** | 63.11 | 1.4% |
| `stagger` | `clean` | 200 | **4.06** | 4.78 | 7.1% |
| `stagger` | `error_lv1` | 200 | **25.60** | 34.58 | 6.5% |
| `stagger` | `error_lv2` | 200 | **74.22** | 96.86 | 3.1% |
| `stagger` | `error_lv3` | 200 | **97.89** | 125.95 | 1.1% |
| `dwell_and_switch` | `clean` | 200 | **0.88** | 1.17 | 66.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **9.52** | 25.56 | 38.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **21.57** | 51.66 | 23.7% |
| `dwell_and_switch` | `error_lv3` | 200 | **43.29** | 86.78 | 12.9% |
| `sliding` | `clean` | 200 | **3.54** | 4.23 | 16.8% |
| `sliding` | `error_lv1` | 200 | **11.21** | 21.93 | 12.4% |
| `sliding` | `error_lv2` | 200 | **29.23** | 50.43 | 5.5% |
| `sliding` | `error_lv3` | 200 | **41.45** | 66.96 | 3.7% |