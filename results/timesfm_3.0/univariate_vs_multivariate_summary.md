# PULSAR: Univariate vs. Joint 5-Channel Multivariate Benchmark Summary

**Compiled on**: 2026-10-26 21:06:32

This report directly compares the predictive fidelity of **Independent Univariate Adapters** against **Joint 5-Channel Multivariate Modeling** across all 20 single-radar fixed datasets.
Both regimes evaluate with **ground-truth emitter pulse masking** (filtering out receiver false alarms and dropped pulse doublings).

---

## LoRA Fine-Tuned: Univariate vs. Joint Multivariate Performance

| Radar Type | Error Level | UV PRI MAE (μs) | MV PRI MAE (μs) | PRI Δ | UV PRI Hit | MV PRI Hit | UV RF MAE (MHz) | MV RF MAE (MHz) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | 0.00 | 0.00 |
| `stable` | `error_lv1` | 0.20 | **0.16** | -22.9% | 99.9% | 99.9% | 0.12 | 0.16 |
| `stable` | `error_lv2` | 0.67 | **0.60** | -9.5% | 99.4% | 99.8% | 0.80 | 0.90 |
| `stable` | `error_lv3` | 1.21 | **1.06** | -12.5% | 99.8% | 99.9% | 1.43 | 1.63 |
| `jitter` | `clean` | 39.89 | **39.80** | -0.2% | 15.6% | 15.8% | 0.00 | 0.00 |
| `jitter` | `error_lv1` | 40.44 | **40.27** | -0.4% | 15.6% | 15.7% | 0.14 | 0.14 |
| `jitter` | `error_lv2` | 40.61 | **40.49** | -0.3% | 14.5% | 14.9% | 0.78 | 0.91 |
| `jitter` | `error_lv3` | 40.60 | **40.23** | -0.9% | 15.2% | 15.5% | 1.56 | 2.07 |
| `stagger` | `clean` | **0.33** | 2.69 | +716.7% | 100.0% | 100.0% | 0.00 | 0.00 |
| `stagger` | `error_lv1` | 28.37 | **27.75** | -2.2% | 74.5% | 75.4% | 0.21 | 0.23 |
| `stagger` | `error_lv2` | 70.61 | **68.86** | -2.5% | 39.7% | 40.4% | 0.99 | 1.06 |
| `stagger` | `error_lv3` | 95.80 | **94.09** | -1.8% | 18.1% | 17.7% | 1.54 | 1.72 |
| `dwell_and_switch` | `clean` | **0.25** | 23.42 | +9195.2% | 100.0% | 59.4% | 0.00 | 0.00 |
| `dwell_and_switch` | `error_lv1` | 8.84 | **8.79** | -0.6% | 91.4% | 92.7% | 0.13 | 0.20 |
| `dwell_and_switch` | `error_lv2` | 23.01 | **21.52** | -6.5% | 70.6% | 73.6% | 1.06 | 1.09 |
| `dwell_and_switch` | `error_lv3` | 39.78 | **37.96** | -4.6% | 50.0% | 53.3% | 1.59 | 1.85 |
| `sliding` | `clean` | **0.39** | 20.58 | +5177.4% | 100.0% | 37.5% | 0.00 | 0.00 |
| `sliding` | `error_lv1` | **6.74** | 6.84 | +1.5% | 84.1% | 85.5% | 0.14 | 0.17 |
| `sliding` | `error_lv2` | 18.69 | **17.47** | -6.5% | 56.4% | 59.0% | 0.80 | 0.90 |
| `sliding` | `error_lv3` | 33.10 | **31.12** | -6.0% | 33.8% | 36.5% | 1.49 | 1.74 |