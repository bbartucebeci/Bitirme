# PULSAR: Unified Benchmark Summary [Varying Profile]

**Compiled on**: 2026-10-27 00:19:35

Comprehensive performance report evaluating Google TimesFM 3.0 across all single-radar varying profile datasets.
Outliers and non-emitter pulses are masked out ($\text{Radar\_ID} == \text{'R\_SINGLE'}$); all metrics evaluate true emitter pulse tracking.

---

## 1. Univariate PDW Parameter Benchmarks (Varying)

Evaluates Zero-Shot vs. Dedicated LoRA Fine-Tuning across all 5 parameters on 4,000 test sequences:


### Pulse Repetition Interval (PRI) (Gate Tolerance: ±10 μs)

| Radar Type | Error Level | Zero-Shot MAE (us) | LoRA SFT MAE (us) | MAE Δ (%) | Zero-Shot Hit Rate | LoRA Hit Rate | Hit Rate Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv1` | 0.12 | 0.14 | +22.2% | 100.0% | **100.0%** | +0.0% |
| `stable` | `error_lv2` | 2.10 | **1.29** | -38.5% | 99.6% | **99.7%** | +0.2% |
| `stable` | `error_lv3` | 1.34 | **1.24** | -7.8% | 98.6% | **99.8%** | +1.1% |
| `jitter` | `clean` | 48.70 | **48.67** | -0.1% | 13.2% | 13.0% | -0.2% |
| `jitter` | `error_lv1` | 48.07 | **47.78** | -0.6% | 13.6% | 13.3% | -0.3% |
| `jitter` | `error_lv2` | 49.13 | **48.88** | -0.5% | 13.4% | 13.1% | -0.3% |
| `jitter` | `error_lv3` | 49.30 | **48.42** | -1.8% | 13.4% | **14.3%** | +0.9% |
| `stagger` | `clean` | 2.56 | **0.35** | -86.3% | 99.9% | **100.0%** | +0.1% |
| `stagger` | `error_lv1` | 40.86 | **25.12** | -38.5% | 61.5% | **74.9%** | +13.4% |
| `stagger` | `error_lv2` | 79.23 | **61.20** | -22.8% | 21.4% | **37.7%** | +16.3% |
| `stagger` | `error_lv3` | 101.62 | **95.00** | -6.5% | 8.8% | **16.0%** | +7.2% |
| `dwell_and_switch` | `clean` | 14.26 | **0.46** | -96.8% | 58.2% | **100.0%** | +41.8% |
| `dwell_and_switch` | `error_lv1` | 24.89 | **10.70** | -57.0% | 51.7% | **84.1%** | +32.4% |
| `dwell_and_switch` | `error_lv2` | 40.76 | **24.77** | -39.2% | 38.0% | **60.5%** | +22.5% |
| `dwell_and_switch` | `error_lv3` | 63.17 | **42.70** | -32.4% | 22.4% | **38.7%** | +16.2% |
| `sliding` | `clean` | 30.16 | **0.57** | -98.1% | 56.2% | **100.0%** | +43.8% |
| `sliding` | `error_lv1` | 33.70 | **9.81** | -70.9% | 44.6% | **77.0%** | +32.4% |
| `sliding` | `error_lv2` | 46.92 | **26.19** | -44.2% | 25.2% | **43.8%** | +18.5% |
| `sliding` | `error_lv3` | 62.71 | **38.39** | -38.8% | 15.7% | **27.9%** | +12.2% |

### Carrier Frequency (RF) (Gate Tolerance: ±2 MHz)

| Radar Type | Error Level | Zero-Shot MAE (MHz) | LoRA SFT MAE (MHz) | MAE Δ (%) | Zero-Shot Hit Rate | LoRA Hit Rate | Hit Rate Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv1` | 0.18 | 0.18 | +1.1% | 98.2% | 97.9% | -0.4% |
| `stable` | `error_lv2` | 2.03 | **0.88** | -56.8% | 92.5% | **93.1%** | +0.6% |
| `stable` | `error_lv3` | 1.59 | **1.23** | -22.3% | 81.5% | **83.8%** | +2.2% |
| `jitter` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `jitter` | `error_lv1` | 18.29 | **0.35** | -98.1% | 96.6% | **97.6%** | +1.0% |
| `jitter` | `error_lv2` | 0.85 | **0.70** | -18.3% | 92.4% | **94.2%** | +1.8% |
| `jitter` | `error_lv3` | 10.00 | **1.79** | -82.1% | 75.0% | **77.7%** | +2.7% |
| `stagger` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv1` | 0.20 | **0.19** | -5.9% | 98.6% | 98.2% | -0.4% |
| `stagger` | `error_lv2` | 0.75 | **0.68** | -9.3% | 93.0% | **94.1%** | +1.1% |
| `stagger` | `error_lv3` | 2.63 | **2.23** | -15.2% | 79.1% | **79.7%** | +0.6% |
| `dwell_and_switch` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `dwell_and_switch` | `error_lv1` | 0.20 | **0.17** | -15.7% | 97.7% | **98.1%** | +0.4% |
| `dwell_and_switch` | `error_lv2` | 8.04 | **1.23** | -84.7% | 92.3% | **94.5%** | +2.3% |
| `dwell_and_switch` | `error_lv3` | 7.03 | **1.77** | -74.9% | 76.7% | **78.1%** | +1.4% |
| `sliding` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv1` | 0.16 | **0.14** | -10.7% | 99.0% | **99.2%** | +0.2% |
| `sliding` | `error_lv2` | 0.70 | **0.65** | -7.8% | 93.5% | **95.3%** | +1.8% |
| `sliding` | `error_lv3` | 8.62 | **1.67** | -80.6% | 79.7% | **82.7%** | +3.0% |

### Pulse Width (PW) (Gate Tolerance: ±0.1 μs)

| Radar Type | Error Level | Zero-Shot MAE (us) | LoRA SFT MAE (us) | MAE Δ (%) | Zero-Shot Hit Rate | LoRA Hit Rate | Hit Rate Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv1` | 0.01 | 0.01 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv2` | 0.03 | **0.02** | -4.0% | 100.0% | 99.9% | -0.0% |
| `stable` | `error_lv3` | 0.04 | 0.04 | +0.0% | 95.1% | **95.3%** | +0.2% |
| `jitter` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `jitter` | `error_lv1` | 0.01 | **0.01** | -42.9% | 99.5% | **100.0%** | +0.5% |
| `jitter` | `error_lv2` | 0.02 | 0.02 | +0.0% | 99.9% | **100.0%** | +0.0% |
| `jitter` | `error_lv3` | 0.04 | **0.04** | -2.4% | 94.5% | **94.7%** | +0.2% |
| `stagger` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv1` | 0.01 | 0.01 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv2` | 0.02 | 0.02 | +0.0% | 99.9% | **99.9%** | +0.0% |
| `stagger` | `error_lv3` | 0.04 | 0.04 | +0.0% | 95.1% | **95.3%** | +0.2% |
| `dwell_and_switch` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `dwell_and_switch` | `error_lv1` | 0.01 | 0.01 | +0.0% | 100.0% | 100.0% | +0.0% |
| `dwell_and_switch` | `error_lv2` | 0.02 | 0.02 | +0.0% | 100.0% | 99.9% | -0.0% |
| `dwell_and_switch` | `error_lv3` | 0.04 | **0.04** | -2.4% | 94.6% | **94.9%** | +0.2% |
| `sliding` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv1` | 0.01 | 0.01 | +0.0% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv2` | 0.02 | 0.02 | +0.0% | 99.9% | **100.0%** | +0.0% |
| `sliding` | `error_lv3` | 0.04 | **0.04** | -2.4% | 94.6% | **94.9%** | +0.3% |

### Angle of Arrival (AOA) (Gate Tolerance: ±2°)

| Radar Type | Error Level | Zero-Shot MAE (deg) | LoRA SFT MAE (deg) | MAE Δ (%) | Zero-Shot Hit Rate | LoRA Hit Rate | Hit Rate Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv1` | 0.04 | 0.04 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv2` | 0.17 | 0.17 | +0.0% | 100.0% | **100.0%** | +0.0% |
| `stable` | `error_lv3` | 0.47 | **0.41** | -12.7% | 99.7% | **99.9%** | +0.2% |
| `jitter` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `jitter` | `error_lv1` | 0.24 | **0.05** | -80.8% | 99.4% | **100.0%** | +0.5% |
| `jitter` | `error_lv2` | 0.17 | 0.17 | +0.0% | 100.0% | 100.0% | +0.0% |
| `jitter` | `error_lv3` | 0.42 | **0.41** | -1.2% | 100.0% | **100.0%** | +0.0% |
| `stagger` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv1` | 0.45 | **0.45** | -0.2% | 99.5% | **99.5%** | +0.0% |
| `stagger` | `error_lv2` | 0.97 | 1.03 | +6.2% | 99.5% | **99.5%** | +0.0% |
| `stagger` | `error_lv3` | 1.76 | **1.75** | -0.2% | 99.4% | **99.5%** | +0.0% |
| `dwell_and_switch` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `dwell_and_switch` | `error_lv1` | 0.04 | 0.04 | +0.0% | 100.0% | 100.0% | +0.0% |
| `dwell_and_switch` | `error_lv2` | 0.21 | **0.17** | -20.6% | 99.8% | **100.0%** | +0.2% |
| `dwell_and_switch` | `error_lv3` | 0.55 | **0.41** | -25.7% | 99.7% | **100.0%** | +0.3% |
| `sliding` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv1` | 0.04 | 0.04 | +0.0% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv2` | 0.16 | **0.16** | -0.6% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv3` | 0.86 | **0.43** | -49.5% | 99.5% | **99.8%** | +0.3% |

### Received Peak Power (Amplitude) (Gate Tolerance: ±2 dBm)

| Radar Type | Error Level | Zero-Shot MAE (dBm) | LoRA SFT MAE (dBm) | MAE Δ (%) | Zero-Shot Hit Rate | LoRA Hit Rate | Hit Rate Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv1` | 0.16 | 0.16 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv2` | 0.41 | **0.40** | -0.7% | 100.0% | 100.0% | -0.0% |
| `stable` | `error_lv3` | 0.82 | **0.81** | -1.0% | 94.8% | **95.1%** | +0.3% |
| `jitter` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `jitter` | `error_lv1` | 0.17 | **0.16** | -4.1% | 99.9% | **100.0%** | +0.1% |
| `jitter` | `error_lv2` | 0.41 | **0.40** | -0.7% | 100.0% | 100.0% | +0.0% |
| `jitter` | `error_lv3` | 0.81 | **0.80** | -1.0% | 94.8% | **95.2%** | +0.4% |
| `stagger` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv1` | 0.16 | **0.16** | -0.6% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv2` | 0.41 | **0.41** | -0.5% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv3` | 0.81 | **0.81** | -0.7% | 94.8% | **94.9%** | +0.2% |
| `dwell_and_switch` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `dwell_and_switch` | `error_lv1` | 0.16 | **0.16** | -0.6% | 100.0% | 100.0% | +0.0% |
| `dwell_and_switch` | `error_lv2` | 0.40 | **0.40** | -1.0% | 100.0% | **100.0%** | +0.0% |
| `dwell_and_switch` | `error_lv3` | 0.82 | **0.80** | -3.3% | 94.8% | **95.5%** | +0.7% |
| `sliding` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv1` | 0.16 | **0.16** | -0.6% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv2` | 0.41 | **0.40** | -0.7% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv3` | 0.82 | **0.81** | -0.5% | 95.0% | **95.2%** | +0.1% |

---

## 2. Joint 5-Channel Multivariate Benchmarks (Varying)

Predicts all 5 PDW channels simultaneously across the 32-pulse horizon using tactical priority weighted Huber loss.

| Radar Type | Error Level | PRI ZS (μs) | PRI LoRA (μs) | PRI Δ | RF ZS (MHz) | RF LoRA (MHz) | PW LoRA (μs) | AOA LoRA (°) | Amp LoRA (dBm) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | +0.0% | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `stable` | `error_lv1` | 0.12 | 0.13 | +6.1% | 0.21 | 0.29 | 0.01 | 0.04 | 0.16 |
| `stable` | `error_lv2` | 0.84 | **0.62** | -26.4% | 0.79 | 0.92 | 0.02 | 0.17 | 0.40 |
| `stable` | `error_lv3` | 1.05 | 1.12 | +6.2% | 1.37 | 1.47 | 0.04 | 0.41 | 0.81 |
| `jitter` | `clean` | 48.58 | **48.56** | -0.0% | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `jitter` | `error_lv1` | 49.06 | **47.62** | -2.9% | 1.67 | 0.40 | 0.01 | 0.05 | 0.16 |
| `jitter` | `error_lv2` | 48.79 | **48.72** | -0.1% | 0.77 | 0.88 | 0.02 | 0.17 | 0.40 |
| `jitter` | `error_lv3` | 48.16 | **48.16** | -0.0% | 1.80 | 2.20 | 0.04 | 0.41 | 0.81 |
| `stagger` | `clean` | 3.30 | **2.08** | -37.0% | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `stagger` | `error_lv1` | 36.29 | **25.08** | -30.9% | 0.20 | 0.22 | 0.01 | 0.44 | 0.16 |
| `stagger` | `error_lv2` | 77.08 | **59.92** | -22.3% | 0.73 | 0.87 | 0.02 | 0.87 | 0.41 |
| `stagger` | `error_lv3` | 101.33 | **93.84** | -7.4% | 1.66 | 1.67 | 0.04 | 1.75 | 0.81 |
| `dwell_and_switch` | `clean` | 12.01 | **10.17** | -15.3% | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `dwell_and_switch` | `error_lv1` | 18.49 | **10.56** | -42.9% | 0.20 | 0.21 | 0.01 | 0.04 | 0.16 |
| `dwell_and_switch` | `error_lv2` | 36.34 | **24.51** | -32.5% | 0.83 | 0.96 | 0.02 | 0.17 | 0.40 |
| `dwell_and_switch` | `error_lv3` | 57.97 | **42.33** | -27.0% | 1.77 | 1.54 | 0.04 | 0.41 | 0.80 |
| `sliding` | `clean` | 36.47 | **9.30** | -74.5% | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `sliding` | `error_lv1` | 19.32 | **10.29** | -46.7% | 0.15 | 0.20 | 0.01 | 0.04 | 0.16 |
| `sliding` | `error_lv2` | 38.31 | **25.68** | -33.0% | 0.71 | 0.81 | 0.02 | 0.16 | 0.40 |
| `sliding` | `error_lv3` | 54.62 | **36.43** | -33.3% | 9.08 | 2.03 | 0.04 | 0.41 | 0.82 |

---

## 3. Univariate vs. Joint 5-Channel Multivariate Performance (Varying)

Direct side-by-side comparison between dedicated univariate adapters and the unified joint multivariate adapter:

| Radar Type | Error Level | UV PRI MAE (μs) | MV PRI MAE (μs) | PRI Δ (%) | UV PRI Hit | MV PRI Hit | UV RF MAE (MHz) | MV RF MAE (MHz) |
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