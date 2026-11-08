# Toto 2.0 Zero-Shot Univariate Benchmark [PRI Varying]

**Evaluated on**: 2026-11-02 23:26:54

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.09** | 0.10 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.57** | 1.97 | 99.9% |
| `stable` | `error_lv3` | 200 | **1.33** | 4.05 | 99.8% |
| `jitter` | `clean` | 200 | **48.05** | 59.89 | 13.6% |
| `jitter` | `error_lv1` | 200 | **48.78** | 60.80 | 13.9% |
| `jitter` | `error_lv2` | 200 | **47.84** | 59.71 | 14.1% |
| `jitter` | `error_lv3` | 200 | **48.28** | 60.16 | 13.1% |
| `stagger` | `clean` | 200 | **0.68** | 0.86 | 100.0% |
| `stagger` | `error_lv1` | 200 | **29.97** | 40.72 | 76.4% |
| `stagger` | `error_lv2` | 200 | **76.54** | 100.54 | 39.4% |
| `stagger` | `error_lv3` | 200 | **92.72** | 119.55 | 18.4% |
| `dwell_and_switch` | `clean` | 200 | **3.60** | 4.48 | 97.1% |
| `dwell_and_switch` | `error_lv1` | 200 | **10.55** | 25.88 | 90.3% |
| `dwell_and_switch` | `error_lv2` | 200 | **22.99** | 53.73 | 77.5% |
| `dwell_and_switch` | `error_lv3` | 200 | **43.81** | 83.84 | 53.3% |
| `sliding` | `clean` | 200 | **4.91** | 6.65 | 88.4% |
| `sliding` | `error_lv1` | 200 | **14.55** | 25.13 | 69.0% |
| `sliding` | `error_lv2` | 200 | **28.57** | 48.16 | 43.6% |
| `sliding` | `error_lv3` | 200 | **49.84** | 73.27 | 22.4% |