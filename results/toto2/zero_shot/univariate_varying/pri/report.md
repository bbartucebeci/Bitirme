# Toto 2.0 Zero-Shot Univariate Benchmark [PRI Varying]

**Evaluated on**: 2026-11-09 01:20:38

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.10** | 0.10 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.85** | 1.92 | 99.7% |
| `stable` | `error_lv3` | 200 | **0.93** | 2.05 | 99.8% |
| `jitter` | `clean` | 200 | **48.63** | 60.11 | 13.3% |
| `jitter` | `error_lv1` | 200 | **47.69** | 59.25 | 13.3% |
| `jitter` | `error_lv2` | 200 | **48.94** | 61.30 | 13.7% |
| `jitter` | `error_lv3` | 200 | **48.30** | 60.04 | 13.9% |
| `stagger` | `clean` | 200 | **0.68** | 0.86 | 100.0% |
| `stagger` | `error_lv1` | 200 | **24.50** | 31.81 | 78.8% |
| `stagger` | `error_lv2` | 200 | **61.99** | 81.59 | 40.9% |
| `stagger` | `error_lv3` | 200 | **96.98** | 123.26 | 17.7% |
| `dwell_and_switch` | `clean` | 200 | **3.60** | 4.48 | 97.1% |
| `dwell_and_switch` | `error_lv1` | 200 | **13.09** | 27.79 | 89.9% |
| `dwell_and_switch` | `error_lv2` | 200 | **23.40** | 54.85 | 76.4% |
| `dwell_and_switch` | `error_lv3` | 200 | **44.87** | 87.95 | 54.0% |
| `sliding` | `clean` | 200 | **4.91** | 6.65 | 88.4% |
| `sliding` | `error_lv1` | 200 | **12.90** | 23.23 | 72.8% |
| `sliding` | `error_lv2` | 200 | **32.03** | 51.94 | 40.3% |
| `sliding` | `error_lv3` | 200 | **48.71** | 71.18 | 22.4% |