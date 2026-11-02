# t0-gamma Zero-Shot Univariate Benchmark [PRI Fixed]

**Evaluated on**: 2026-11-02 22:52:05

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **5.94** | 6.30 | 99.2% |
| `stable` | `error_lv2` | 200 | **1.08** | 1.50 | 98.8% |
| `stable` | `error_lv3` | 200 | **1.21** | 2.19 | 99.8% |
| `jitter` | `clean` | 200 | **40.79** | 50.66 | 14.9% |
| `jitter` | `error_lv1` | 200 | **43.36** | 53.44 | 15.5% |
| `jitter` | `error_lv2` | 200 | **41.63** | 51.69 | 15.1% |
| `jitter` | `error_lv3` | 200 | **41.57** | 52.01 | 15.5% |
| `stagger` | `clean` | 200 | **4.77** | 5.48 | 96.9% |
| `stagger` | `error_lv1` | 200 | **28.63** | 36.46 | 70.1% |
| `stagger` | `error_lv2` | 200 | **88.09** | 108.45 | 25.1% |
| `stagger` | `error_lv3` | 200 | **94.75** | 116.58 | 14.4% |
| `dwell_and_switch` | `clean` | 200 | **0.94** | 1.16 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **9.08** | 23.30 | 93.6% |
| `dwell_and_switch` | `error_lv2` | 200 | **29.57** | 65.07 | 73.3% |
| `dwell_and_switch` | `error_lv3` | 200 | **48.32** | 91.37 | 56.0% |
| `sliding` | `clean` | 200 | **2.74** | 3.18 | 100.0% |
| `sliding` | `error_lv1` | 200 | **13.86** | 27.05 | 75.7% |
| `sliding` | `error_lv2` | 200 | **27.77** | 53.09 | 45.3% |
| `sliding` | `error_lv3` | 200 | **39.65** | 64.41 | 29.8% |