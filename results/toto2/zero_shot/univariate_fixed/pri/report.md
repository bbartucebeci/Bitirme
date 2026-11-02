# Toto 2.0 Zero-Shot Univariate Benchmark [PRI Fixed]

**Evaluated on**: 2026-11-02 22:52:30

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.09** | 0.11 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.57** | 1.60 | 99.9% |
| `stable` | `error_lv3` | 200 | **0.92** | 1.57 | 99.8% |
| `jitter` | `clean` | 200 | **40.25** | 49.99 | 15.4% |
| `jitter` | `error_lv1` | 200 | **40.11** | 50.13 | 15.5% |
| `jitter` | `error_lv2` | 200 | **40.65** | 50.38 | 15.4% |
| `jitter` | `error_lv3` | 200 | **41.66** | 53.34 | 15.8% |
| `stagger` | `clean` | 200 | **0.60** | 0.67 | 100.0% |
| `stagger` | `error_lv1` | 200 | **19.82** | 26.09 | 83.8% |
| `stagger` | `error_lv2` | 200 | **83.53** | 102.58 | 36.0% |
| `stagger` | `error_lv3` | 200 | **88.52** | 109.50 | 23.3% |
| `dwell_and_switch` | `clean` | 200 | **3.81** | 4.91 | 93.8% |
| `dwell_and_switch` | `error_lv1` | 200 | **10.32** | 24.98 | 90.2% |
| `dwell_and_switch` | `error_lv2` | 200 | **30.73** | 63.95 | 75.1% |
| `dwell_and_switch` | `error_lv3` | 200 | **46.09** | 87.52 | 56.8% |
| `sliding` | `clean` | 200 | **8.18** | 11.36 | 71.9% |
| `sliding` | `error_lv1` | 200 | **15.28** | 26.28 | 61.5% |
| `sliding` | `error_lv2` | 200 | **30.27** | 51.89 | 40.5% |
| `sliding` | `error_lv3` | 200 | **43.73** | 66.03 | 26.2% |