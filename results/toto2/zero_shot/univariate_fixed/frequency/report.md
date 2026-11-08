# Toto 2.0 Zero-Shot Univariate Benchmark [Carrier Frequency Fixed]

**Evaluated on**: 2026-11-02 23:00:09

**Context History**: 96 pulses | **Forecast Horizon**: 32 pulses


| Radar Type | Error Level | Seqs | MAE (MHz) | RMSE (MHz) | Gate Hit Rate (+/-2MHz) |
|---|---|---:|---:|---:|---:|
| `stable` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stable` | `error_lv1` | 200 | **0.11** | 0.13 | 100.0% |
| `stable` | `error_lv2` | 200 | **0.56** | 0.66 | 96.5% |
| `stable` | `error_lv3` | 200 | **1.05** | 1.26 | 88.4% |
| `jitter` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `jitter` | `error_lv1` | 200 | **0.10** | 0.12 | 100.0% |
| `jitter` | `error_lv2` | 200 | **0.62** | 0.72 | 94.9% |
| `jitter` | `error_lv3` | 200 | **1.47** | 2.77 | 83.1% |
| `stagger` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `stagger` | `error_lv1` | 200 | **0.12** | 0.14 | 99.6% |
| `stagger` | `error_lv2` | 200 | **0.58** | 0.68 | 95.5% |
| `stagger` | `error_lv3` | 200 | **1.29** | 1.54 | 84.4% |
| `dwell_and_switch` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `dwell_and_switch` | `error_lv1` | 200 | **0.11** | 0.13 | 99.5% |
| `dwell_and_switch` | `error_lv2` | 200 | **0.61** | 0.70 | 94.8% |
| `dwell_and_switch` | `error_lv3` | 200 | **1.31** | 1.54 | 84.0% |
| `sliding` | `clean` | 200 | **0.00** | 0.00 | 100.0% |
| `sliding` | `error_lv1` | 200 | **0.14** | 0.16 | 98.7% |
| `sliding` | `error_lv2` | 200 | **0.49** | 0.59 | 98.3% |
| `sliding` | `error_lv3` | 200 | **1.22** | 1.56 | 86.0% |