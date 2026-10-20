# TimesFM 3.0 Zero-Shot Benchmark Results

**Evaluated on**: 2026-10-20 23:55:04

**Context Length**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (μs) | RMSE (μs) | Gate Hit Rate (±10μs) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.11** | 0.13 | 100.0% |
| `stable` | `error_lv1` | 180 | **5.88** | 28.11 | 99.2% |
| `stable` | `error_lv2` | 122 | **16.76** | 66.62 | 96.8% |
| `stable` | `error_lv3` | 63 | **34.09** | 130.87 | 88.4% |
| `jitter` | `clean` | 197 | **40.63** | 50.54 | 15.6% |
| `jitter` | `error_lv1` | 138 | **43.26** | 60.68 | 16.2% |
| `jitter` | `error_lv2` | 88 | **55.35** | 103.35 | 14.4% |
| `jitter` | `error_lv3` | 56 | **63.39** | 127.36 | 15.0% |
| `stagger` | `clean` | 200 | **2.45** | 2.90 | 100.0% |
| `stagger` | `error_lv1` | 116 | **16.29** | 21.70 | 86.4% |
| `stagger` | `error_lv2` | 59 | **72.41** | 104.51 | 38.0% |
| `stagger` | `error_lv3` | 38 | **117.35** | 180.40 | 23.7% |
| `dwell_and_switch` | `clean` | 200 | **12.97** | 16.07 | 50.0% |
| `dwell_and_switch` | `error_lv1` | 177 | **29.29** | 61.91 | 44.1% |
| `dwell_and_switch` | `error_lv2` | 119 | **54.81** | 109.91 | 34.3% |
| `dwell_and_switch` | `error_lv3` | 79 | **88.95** | 159.41 | 22.6% |
| `sliding` | `clean` | 200 | **17.42** | 21.83 | 37.5% |
| `sliding` | `error_lv1` | 179 | **28.95** | 46.80 | 31.2% |
| `sliding` | `error_lv2` | 122 | **58.06** | 111.10 | 22.8% |
| `sliding` | `error_lv3` | 60 | **85.84** | 161.29 | 16.1% |