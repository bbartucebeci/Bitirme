# t0-gamma LoRA Fine-Tuned (SFT) Benchmark Report [PRI Varying]

**Evaluated on**: 2026-11-10 00:11:26

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **2.06** | 3.33 | 99.0% |
| `stable` | `error_lv2` | 200 | **1.68** | 2.60 | 99.2% |
| `stable` | `error_lv3` | 200 | **1.19** | 1.64 | 99.7% |
| `jitter` | `clean` | 200 | **47.83** | 59.62 | 14.2% |
| `jitter` | `error_lv1` | 200 | **49.27** | 61.30 | 13.3% |
| `jitter` | `error_lv2` | 200 | **49.55** | 61.94 | 13.8% |
| `jitter` | `error_lv3` | 200 | **50.60** | 63.13 | 13.3% |
| `stagger` | `clean` | 200 | **3.94** | 4.62 | 97.8% |
| `stagger` | `error_lv1` | 200 | **25.20** | 34.05 | 73.1% |
| `stagger` | `error_lv2` | 200 | **74.14** | 96.68 | 30.2% |
| `stagger` | `error_lv3` | 200 | **98.02** | 125.94 | 13.3% |
| `dwell_and_switch` | `clean` | 200 | **0.88** | 1.13 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **9.37** | 25.43 | 93.7% |
| `dwell_and_switch` | `error_lv2` | 200 | **21.42** | 51.62 | 80.1% |
| `dwell_and_switch` | `error_lv3` | 200 | **43.01** | 86.80 | 62.6% |
| `sliding` | `clean` | 200 | **3.03** | 3.75 | 97.5% |
| `sliding` | `error_lv1` | 200 | **10.73** | 21.50 | 78.6% |
| `sliding` | `error_lv2` | 200 | **28.53** | 49.81 | 46.7% |
| `sliding` | `error_lv3` | 200 | **40.99** | 66.59 | 30.5% |