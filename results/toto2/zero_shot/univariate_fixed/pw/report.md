# Toto 2.0 Zero-Shot Univariate Benchmark [Pulse Width Fixed]

**Evaluated on**: 2026-11-02 23:00:25

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-0.1us) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.01** | 0.01 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.02** | 0.03 | 100.0% |
| `stable` | `error_lv3` | 200 | **0.04** | 0.06 | 95.0% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.01** | 0.01 | 100.0% |
| `jitter` | `error_lv2` | 200 | **0.03** | 0.03 | 99.9% |
| `jitter` | `error_lv3` | 200 | **0.04** | 0.05 | 95.4% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.01** | 0.01 | 100.0% |
| `stagger` | `error_lv2` | 200 | **0.02** | 0.03 | 99.9% |
| `stagger` | `error_lv3` | 200 | **0.04** | 0.05 | 95.2% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.01** | 0.01 | 100.0% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.02** | 0.03 | 99.9% |
| `dwell_and_switch` | `error_lv3` | 200 | **0.04** | 0.05 | 95.4% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.01** | 0.01 | 100.0% |
| `sliding` | `error_lv2` | 200 | **0.03** | 0.03 | 99.9% |
| `sliding` | `error_lv3` | 200 | **0.04** | 0.05 | 95.5% |