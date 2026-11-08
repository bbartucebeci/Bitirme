# t0-gamma Zero-Shot Univariate Benchmark [aoa Varying]

**Evaluated on**: 2026-11-08 18:04:45

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (units) | RMSE (units) | Gate Hit Rate (+/-1units) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.17** | 0.23 | 100.0% |
| `stable` | `error_lv3` | 200 | **0.44** | 0.55 | 93.2% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `jitter` | `error_lv2` | 200 | **0.17** | 0.21 | 100.0% |
| `jitter` | `error_lv3` | 200 | **0.48** | 0.79 | 94.5% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.66** | 1.11 | 99.8% |
| `stagger` | `error_lv2` | 200 | **1.01** | 1.42 | 99.1% |
| `stagger` | `error_lv3` | 200 | **1.58** | 2.87 | 92.1% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.04** | 0.06 | 100.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.17** | 0.21 | 100.0% |
| `dwell_and_switch` | `error_lv3` | 200 | **0.44** | 0.60 | 93.6% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `sliding` | `error_lv2` | 200 | **0.18** | 0.22 | 99.9% |
| `sliding` | `error_lv3` | 200 | **0.42** | 0.53 | 94.0% |