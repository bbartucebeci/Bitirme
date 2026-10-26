# TimesFM 3.0 LoRA Fine-Tuned (SFT) Benchmark Report [Carrier Frequency Fixed]

**Evaluated on**: 2026-10-26 20:12:30

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (MHz) | RMSE (MHz) | Gate Hit Rate (+/-2MHz) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.12** | 0.15 | 99.4% |
| `stable` | `error_lv2` | 200 | **0.80** | 1.02 | 93.7% |
| `stable` | `error_lv3` | 200 | **1.43** | 1.67 | 80.3% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.14** | 0.17 | 99.4% |
| `jitter` | `error_lv2` | 200 | **0.78** | 0.91 | 92.4% |
| `jitter` | `error_lv3` | 200 | **1.56** | 1.82 | 76.4% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.21** | 0.24 | 98.0% |
| `stagger` | `error_lv2` | 200 | **0.99** | 1.27 | 91.0% |
| `stagger` | `error_lv3` | 200 | **1.54** | 1.78 | 79.3% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.13** | 0.15 | 99.7% |
| `dwell_and_switch` | `error_lv2` | 200 | **1.06** | 1.20 | 90.8% |
| `dwell_and_switch` | `error_lv3` | 200 | **1.59** | 1.86 | 80.2% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.14** | 0.17 | 98.8% |
| `sliding` | `error_lv2` | 200 | **0.80** | 0.92 | 93.6% |
| `sliding` | `error_lv3` | 200 | **1.49** | 1.74 | 81.0% |