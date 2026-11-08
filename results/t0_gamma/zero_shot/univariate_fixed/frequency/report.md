# t0-gamma Zero-Shot Univariate Benchmark [Carrier Frequency Fixed]

**Evaluated on**: 2026-11-02 22:55:33

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (MHz) | RMSE (MHz) | Gate Hit Rate (+/-2MHz) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.20** | 0.23 | 97.4% |
| `stable` | `error_lv2` | 200 | **2.29** | 2.63 | 86.1% |
| `stable` | `error_lv3` | 200 | **24.23** | 25.68 | 73.0% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.14** | 0.16 | 99.2% |
| `jitter` | `error_lv2` | 200 | **2.86** | 5.39 | 85.3% |
| `jitter` | `error_lv3` | 200 | **3.29** | 4.46 | 71.5% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.16** | 0.19 | 98.7% |
| `stagger` | `error_lv2` | 200 | **1.83** | 3.06 | 89.8% |
| `stagger` | `error_lv3` | 200 | **11.04** | 13.17 | 71.9% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.14** | 0.17 | 99.4% |
| `dwell_and_switch` | `error_lv2` | 200 | **3.66** | 5.10 | 89.3% |
| `dwell_and_switch` | `error_lv3` | 200 | **39.20** | 40.28 | 74.2% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.18** | 0.21 | 97.9% |
| `sliding` | `error_lv2` | 200 | **0.91** | 1.04 | 89.5% |
| `sliding` | `error_lv3` | 200 | **3.41** | 4.34 | 72.4% |