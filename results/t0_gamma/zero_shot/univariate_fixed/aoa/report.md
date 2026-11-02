# t0-gamma Zero-Shot Univariate Benchmark [Angle of Arrival Fixed]

**Evaluated on**: 2026-11-02 22:57:12

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (deg) | RMSE (deg) | Gate Hit Rate (+/-2deg) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.20** | 0.26 | 99.6% |
| `stable` | `error_lv3` | 200 | **1.43** | 1.61 | 99.0% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `jitter` | `error_lv2` | 200 | **0.50** | 0.57 | 99.5% |
| `jitter` | `error_lv3` | 200 | **1.24** | 1.39 | 99.0% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.04** | 0.06 | 100.0% |
| `stagger` | `error_lv2` | 200 | **0.95** | 1.05 | 99.4% |
| `stagger` | `error_lv3` | 200 | **0.47** | 0.67 | 99.8% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.17** | 0.22 | 100.0% |
| `dwell_and_switch` | `error_lv3` | 200 | **0.45** | 0.62 | 99.7% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `sliding` | `error_lv2` | 200 | **0.17** | 0.21 | 100.0% |
| `sliding` | `error_lv3` | 200 | **0.41** | 0.51 | 100.0% |