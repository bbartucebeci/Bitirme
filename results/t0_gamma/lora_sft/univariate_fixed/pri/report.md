# t0-gamma LoRA Fine-Tuned (SFT) Benchmark Report [PRI Fixed]

**Evaluated on**: 2026-11-10 00:08:22

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.67** | 1.61 | 99.6% |
| `stable` | `error_lv2` | 200 | **1.34** | 2.23 | 98.8% |
| `stable` | `error_lv3` | 200 | **1.07** | 1.61 | 99.5% |
| `jitter` | `clean` | 200 | **41.22** | 51.05 | 15.0% |
| `jitter` | `error_lv1` | 200 | **40.33** | 50.17 | 15.7% |
| `jitter` | `error_lv2` | 200 | **41.10** | 51.22 | 15.7% |
| `jitter` | `error_lv3` | 200 | **41.75** | 52.34 | 15.8% |
| `stagger` | `clean` | 200 | **3.56** | 4.21 | 100.0% |
| `stagger` | `error_lv1` | 200 | **25.90** | 34.54 | 71.0% |
| `stagger` | `error_lv2` | 200 | **70.66** | 90.24 | 33.9% |
| `stagger` | `error_lv3` | 200 | **98.57** | 121.95 | 15.9% |
| `dwell_and_switch` | `clean` | 200 | **0.88** | 1.08 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **11.28** | 28.65 | 92.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **27.11** | 59.22 | 76.7% |
| `dwell_and_switch` | `error_lv3` | 200 | **49.54** | 92.90 | 57.4% |
| `sliding` | `clean` | 200 | **2.77** | 3.21 | 100.0% |
| `sliding` | `error_lv1` | 200 | **14.69** | 26.69 | 76.1% |
| `sliding` | `error_lv2` | 200 | **26.96** | 49.32 | 48.2% |
| `sliding` | `error_lv3` | 200 | **38.84** | 65.27 | 30.6% |