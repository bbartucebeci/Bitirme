# t0-gamma Zero-Shot Univariate Benchmark [Carrier Frequency Varying]

**Evaluated on**: 2026-11-02 22:58:17

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (MHz) | RMSE (MHz) | Gate Hit Rate (+/-2MHz) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.27** | 0.30 | 96.7% |
| `stable` | `error_lv2` | 200 | **1.00** | 1.13 | 88.4% |
| `stable` | `error_lv3` | 200 | **52.63** | 53.99 | 75.8% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.27** | 0.30 | 97.2% |
| `jitter` | `error_lv2` | 200 | **0.94** | 1.10 | 89.5% |
| `jitter` | `error_lv3` | 200 | **16.46** | 17.82 | 77.8% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.31** | 0.34 | 98.3% |
| `stagger` | `error_lv2` | 200 | **4.53** | 5.21 | 86.4% |
| `stagger` | `error_lv3` | 200 | **2.17** | 2.44 | 71.4% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.24** | 0.27 | 97.5% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.93** | 1.08 | 90.5% |
| `dwell_and_switch` | `error_lv3` | 200 | **17.50** | 17.95 | 73.0% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.82** | 1.13 | 96.5% |
| `sliding` | `error_lv2` | 200 | **4.04** | 4.75 | 88.5% |
| `sliding` | `error_lv3` | 200 | **5.41** | 9.67 | 74.4% |