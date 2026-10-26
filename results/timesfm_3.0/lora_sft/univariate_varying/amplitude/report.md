# TimesFM 3.0 LoRA Fine-Tuned (SFT) Benchmark Report [Amplitude Varying]

**Evaluated on**: 2026-10-26 22:52:38

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (dBm) | RMSE (dBm) | Gate Hit Rate (+/-2dBm) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.16** | 0.20 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.40** | 0.50 | 100.0% |
| `stable` | `error_lv3` | 200 | **0.81** | 1.00 | 95.1% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.16** | 0.20 | 100.0% |
| `jitter` | `error_lv2` | 200 | **0.40** | 0.50 | 100.0% |
| `jitter` | `error_lv3` | 200 | **0.80** | 1.00 | 95.2% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.16** | 0.20 | 100.0% |
| `stagger` | `error_lv2` | 200 | **0.41** | 0.50 | 100.0% |
| `stagger` | `error_lv3` | 200 | **0.81** | 1.00 | 94.9% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.16** | 0.20 | 100.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.40** | 0.50 | 100.0% |
| `dwell_and_switch` | `error_lv3` | 200 | **0.80** | 0.99 | 95.5% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.16** | 0.20 | 100.0% |
| `sliding` | `error_lv2` | 200 | **0.40** | 0.50 | 100.0% |
| `sliding` | `error_lv3` | 200 | **0.81** | 1.01 | 95.2% |