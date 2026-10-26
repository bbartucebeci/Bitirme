# PULSAR: Univariate vs. Joint 5-Channel Multivariate Comparison [Varying Profile]

**Compiled on**: 2026-10-26 23:05:00

Direct side-by-side performance comparison between independent univariate LoRA adapters and unified 5-channel multivariate LoRA modeling.

---

## LoRA Fine-Tuned: Univariate vs. Joint Multivariate Performance (Varying)

| Radar Type | Error Level | UV PRI MAE (μs) | MV PRI MAE (μs) | PRI Δ | UV PRI Hit | MV PRI Hit | UV RF MAE (MHz) | MV RF MAE (MHz) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | 0.00 | 0.00 |
| `stable` | `error_lv1` | 0.14 | **0.13** | -8.1% | 100.0% | 100.0% | 0.18 | 0.29 |
| `stable` | `error_lv2` | 1.29 | **0.62** | -52.0% | 99.7% | 99.9% | 0.88 | 0.92 |
| `stable` | `error_lv3` | 1.24 | **1.12** | -9.9% | 99.8% | 99.8% | 1.23 | 1.47 |
| `jitter` | `clean` | 48.67 | **48.56** | -0.2% | 13.0% | 13.0% | 0.00 | 0.00 |
| `jitter` | `error_lv1` | 47.78 | **47.62** | -0.3% | 13.3% | 13.3% | 0.35 | 0.40 |
| `jitter` | `error_lv2` | 48.88 | **48.72** | -0.3% | 13.1% | 13.6% | 0.70 | 0.88 |
| `jitter` | `error_lv3` | 48.42 | **48.16** | -0.5% | 14.3% | 14.1% | 1.79 | 2.20 |
| `stagger` | `clean` | **0.35** | 2.08 | +491.4% | 100.0% | 100.0% | 0.00 | 0.00 |
| `stagger` | `error_lv1` | 25.12 | **25.08** | -0.2% | 74.9% | 75.4% | 0.19 | 0.22 |
| `stagger` | `error_lv2` | 61.20 | **59.92** | -2.1% | 37.7% | 37.7% | 0.68 | 0.87 |
| `stagger` | `error_lv3` | 95.00 | **93.84** | -1.2% | 16.0% | 17.0% | 2.23 | 1.67 |
| `dwell_and_switch` | `clean` | **0.46** | 10.17 | +2119.8% | 100.0% | 75.4% | 0.00 | 0.00 |
| `dwell_and_switch` | `error_lv1` | 10.70 | **10.56** | -1.3% | 84.1% | 84.5% | 0.17 | 0.21 |
| `dwell_and_switch` | `error_lv2` | 24.77 | **24.51** | -1.0% | 60.5% | 61.7% | 1.23 | 0.96 |
| `dwell_and_switch` | `error_lv3` | 42.70 | **42.33** | -0.9% | 38.7% | 39.1% | 1.77 | 1.54 |
| `sliding` | `clean` | **0.57** | 9.30 | +1534.0% | 100.0% | 72.6% | 0.00 | 0.00 |
| `sliding` | `error_lv1` | **9.81** | 10.29 | +5.0% | 77.0% | 76.9% | 0.14 | 0.20 |
| `sliding` | `error_lv2` | 26.19 | **25.68** | -2.0% | 43.8% | 44.6% | 0.65 | 0.81 |
| `sliding` | `error_lv3` | 38.39 | **36.43** | -5.1% | 27.9% | 29.4% | 1.67 | 2.03 |