# t0-gamma Zero-Shot Univariate Benchmark [Angle of Arrival Varying]

**Evaluated on**: 2026-11-02 23:32:55

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (deg) | RMSE (deg) | Gate Hit Rate (+/-2deg) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.17** | 0.21 | 100.0% |
| `stable` | `error_lv3` | 200 | **0.43** | 0.53 | 99.8% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `jitter` | `error_lv2` | 200 | **0.17** | 0.21 | 100.0% |
| `jitter` | `error_lv3` | 200 | **1.43** | 1.65 | 98.5% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.89** | 1.28 | 99.8% |
| `stagger` | `error_lv2` | 200 | **1.24** | 1.67 | 99.0% |
| `stagger` | `error_lv3` | 200 | **1.71** | 2.58 | 99.4% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.17** | 0.22 | 100.0% |
| `dwell_and_switch` | `error_lv3` | 200 | **0.43** | 0.55 | 99.9% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.29** | 0.30 | 99.5% |
| `sliding` | `error_lv2` | 200 | **0.17** | 0.21 | 100.0% |
| `sliding` | `error_lv3` | 200 | **0.44** | 0.57 | 99.7% |