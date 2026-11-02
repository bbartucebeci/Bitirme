# t0-gamma Zero-Shot Univariate Benchmark [PRI Varying]

**Evaluated on**: 2026-11-02 22:54:31

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.17** | 0.18 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.53** | 0.73 | 100.0% |
| `stable` | `error_lv3` | 200 | **1.69** | 3.53 | 99.4% |
| `jitter` | `clean` | 200 | **48.95** | 60.88 | 13.5% |
| `jitter` | `error_lv1` | 200 | **49.37** | 61.51 | 14.3% |
| `jitter` | `error_lv2` | 200 | **48.69** | 60.70 | 13.4% |
| `jitter` | `error_lv3` | 200 | **50.13** | 62.30 | 13.3% |
| `stagger` | `clean` | 200 | **4.06** | 4.78 | 96.2% |
| `stagger` | `error_lv1` | 200 | **36.80** | 49.02 | 63.5% |
| `stagger` | `error_lv2` | 200 | **80.22** | 105.47 | 26.6% |
| `stagger` | `error_lv3` | 200 | **94.60** | 123.09 | 13.4% |
| `dwell_and_switch` | `clean` | 200 | **0.88** | 1.17 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **10.22** | 27.75 | 93.3% |
| `dwell_and_switch` | `error_lv2` | 200 | **23.95** | 58.61 | 80.8% |
| `dwell_and_switch` | `error_lv3` | 200 | **41.97** | 85.35 | 59.6% |
| `sliding` | `clean` | 200 | **3.54** | 4.23 | 96.1% |
| `sliding` | `error_lv1` | 200 | **14.62** | 26.91 | 73.4% |
| `sliding` | `error_lv2` | 200 | **27.89** | 49.36 | 46.4% |
| `sliding` | `error_lv3` | 200 | **48.83** | 76.68 | 28.0% |