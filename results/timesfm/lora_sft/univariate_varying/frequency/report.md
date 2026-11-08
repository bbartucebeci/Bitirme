# TimesFM 3.0 LoRA Fine-Tuned (SFT) Benchmark Report [Carrier Frequency Varying]

**Evaluated on**: 2026-10-26 22:31:45

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (MHz) | RMSE (MHz) | Gate Hit Rate (+/-2MHz) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.18** | 0.21 | 97.9% |
| `stable` | `error_lv2` | 200 | **0.88** | 1.01 | 93.1% |
| `stable` | `error_lv3` | 200 | **1.23** | 1.47 | 83.8% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.35** | 0.51 | 97.6% |
| `jitter` | `error_lv2` | 200 | **0.70** | 0.82 | 94.2% |
| `jitter` | `error_lv3` | 200 | **1.79** | 2.17 | 77.7% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.19** | 0.22 | 98.2% |
| `stagger` | `error_lv2` | 200 | **0.68** | 0.81 | 94.1% |
| `stagger` | `error_lv3` | 200 | **2.23** | 4.00 | 79.7% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.17** | 0.20 | 98.1% |
| `dwell_and_switch` | `error_lv2` | 200 | **1.23** | 1.76 | 94.5% |
| `dwell_and_switch` | `error_lv3` | 200 | **1.77** | 2.12 | 78.1% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.14** | 0.17 | 99.2% |
| `sliding` | `error_lv2` | 200 | **0.65** | 0.77 | 95.3% |
| `sliding` | `error_lv3` | 200 | **1.67** | 1.99 | 82.7% |