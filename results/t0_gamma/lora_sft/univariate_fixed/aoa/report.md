# t0-gamma Zero-Shot Univariate Benchmark [aoa Fixed]

**Evaluated on**: 2026-11-08 17:59:41

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (units) | RMSE (units) | Gate Hit Rate (+/-1units) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.17** | 0.21 | 99.9% |
| `stable` | `error_lv3` | 200 | **1.19** | 1.33 | 92.8% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `jitter` | `error_lv2` | 200 | **0.21** | 0.30 | 99.0% |
| `jitter` | `error_lv3` | 200 | **0.48** | 0.58 | 94.3% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.04** | 0.06 | 100.0% |
| `stagger` | `error_lv2` | 200 | **0.17** | 0.21 | 100.0% |
| `stagger` | `error_lv3` | 200 | **0.81** | 0.93 | 94.1% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.21** | 0.25 | 99.5% |
| `dwell_and_switch` | `error_lv3` | 200 | **0.44** | 0.58 | 94.2% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.04** | 0.05 | 100.0% |
| `sliding` | `error_lv2` | 200 | **0.17** | 0.21 | 100.0% |
| `sliding` | `error_lv3` | 200 | **0.43** | 0.55 | 93.8% |