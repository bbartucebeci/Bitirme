# PULSAR: Unified Benchmark Summary [Fixed Profile]

**Compiled on**: 2026-10-27 00:19:35

Comprehensive performance report evaluating Google TimesFM 3.0 across all single-radar fixed profile datasets.
Outliers and non-emitter pulses are masked out ($\text{Radar\_ID} == \text{'R\_SINGLE'}$); all metrics evaluate true emitter pulse tracking.

---

## 1. Univariate PDW Parameter Benchmarks (Fixed)

Evaluates Zero-Shot vs. Dedicated LoRA Fine-Tuning across all 5 parameters on 4,000 test sequences:


### Pulse Repetition Interval (PRI) (Gate Tolerance: ±10 μs)

| Radar Type | Error Level | Zero-Shot MAE (us) | LoRA SFT MAE (us) | MAE Δ (%) | Zero-Shot Hit Rate | LoRA Hit Rate | Hit Rate Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv1` | 0.29 | **0.20** | -29.1% | 99.8% | **99.9%** | +0.1% |
| `stable` | `error_lv2` | 1.65 | **0.67** | -59.6% | 98.3% | **99.4%** | +1.0% |
| `stable` | `error_lv3` | 1.44 | **1.21** | -15.9% | 99.6% | **99.8%** | +0.2% |
| `jitter` | `clean` | 39.94 | **39.89** | -0.1% | 15.5% | **15.6%** | +0.1% |
| `jitter` | `error_lv1` | 40.66 | **40.44** | -0.5% | 15.5% | **15.6%** | +0.1% |
| `jitter` | `error_lv2` | 41.58 | **40.61** | -2.3% | 14.5% | 14.5% | +0.0% |
| `jitter` | `error_lv3` | 41.06 | **40.60** | -1.1% | 15.5% | 15.2% | -0.2% |
| `stagger` | `clean` | 2.69 | **0.33** | -87.8% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv1` | 41.04 | **28.37** | -30.9% | 61.7% | **74.5%** | +12.8% |
| `stagger` | `error_lv2` | 80.01 | **70.61** | -11.7% | 27.2% | **39.7%** | +12.5% |
| `stagger` | `error_lv3` | 98.25 | **95.80** | -2.5% | 15.4% | **18.1%** | +2.8% |
| `dwell_and_switch` | `clean` | 25.34 | **0.25** | -99.0% | 37.5% | **100.0%** | +62.5% |
| `dwell_and_switch` | `error_lv1` | 34.01 | **8.84** | -74.0% | 36.0% | **91.4%** | +55.4% |
| `dwell_and_switch` | `error_lv2` | 53.20 | **23.01** | -56.8% | 25.8% | **70.6%** | +44.8% |
| `dwell_and_switch` | `error_lv3` | 76.11 | **39.78** | -47.7% | 17.8% | **50.0%** | +32.2% |
| `sliding` | `clean` | 71.04 | **0.39** | -99.5% | 15.6% | **100.0%** | +84.4% |
| `sliding` | `error_lv1` | 57.23 | **6.74** | -88.2% | 22.2% | **84.1%** | +61.9% |
| `sliding` | `error_lv2` | 55.11 | **18.69** | -66.1% | 19.8% | **56.4%** | +36.5% |
| `sliding` | `error_lv3` | 60.90 | **33.10** | -45.7% | 13.7% | **33.8%** | +20.1% |

### Carrier Frequency (RF) (Gate Tolerance: ±2 MHz)

| Radar Type | Error Level | Zero-Shot MAE (MHz) | LoRA SFT MAE (MHz) | MAE Δ (%) | Zero-Shot Hit Rate | LoRA Hit Rate | Hit Rate Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv1` | 0.13 | **0.12** | -6.9% | 99.5% | 99.4% | -0.0% |
| `stable` | `error_lv2` | 4.55 | **0.80** | -82.3% | 92.5% | **93.7%** | +1.2% |
| `stable` | `error_lv3` | 1.52 | **1.43** | -6.1% | 79.0% | **80.3%** | +1.3% |
| `jitter` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `jitter` | `error_lv1` | 0.16 | **0.14** | -13.0% | 99.2% | **99.4%** | +0.2% |
| `jitter` | `error_lv2` | 2.04 | **0.78** | -61.8% | 91.5% | **92.4%** | +0.9% |
| `jitter` | `error_lv3` | 1.61 | **1.56** | -3.3% | 75.9% | **76.4%** | +0.5% |
| `stagger` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv1` | 0.27 | **0.21** | -22.5% | 97.0% | **98.0%** | +1.0% |
| `stagger` | `error_lv2` | 23.23 | **0.99** | -95.7% | 89.6% | **91.0%** | +1.5% |
| `stagger` | `error_lv3` | 2.00 | **1.54** | -23.3% | 77.4% | **79.3%** | +1.9% |
| `dwell_and_switch` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `dwell_and_switch` | `error_lv1` | 0.14 | **0.13** | -11.0% | 99.0% | **99.7%** | +0.7% |
| `dwell_and_switch` | `error_lv2` | 3.04 | **1.06** | -65.2% | 90.8% | 90.8% | -0.1% |
| `dwell_and_switch` | `error_lv3` | 6.18 | **1.59** | -74.3% | 77.4% | **80.2%** | +2.9% |
| `sliding` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv1` | 0.16 | **0.14** | -10.8% | 98.6% | **98.8%** | +0.2% |
| `sliding` | `error_lv2` | 1.79 | **0.80** | -55.7% | 91.8% | **93.6%** | +1.8% |
| `sliding` | `error_lv3` | 1.65 | **1.49** | -9.7% | 79.3% | **81.0%** | +1.7% |

### Pulse Width (PW) (Gate Tolerance: ±0.1 μs)

| Radar Type | Error Level | Zero-Shot MAE (us) | LoRA SFT MAE (us) | MAE Δ (%) | Zero-Shot Hit Rate | LoRA Hit Rate | Hit Rate Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv1` | 0.01 | 0.01 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv2` | 0.03 | **0.02** | -17.2% | 99.7% | **100.0%** | +0.3% |
| `stable` | `error_lv3` | 0.04 | 0.04 | +0.0% | 94.8% | **95.1%** | +0.3% |
| `jitter` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `jitter` | `error_lv1` | 0.01 | 0.01 | +0.0% | 100.0% | 100.0% | +0.0% |
| `jitter` | `error_lv2` | 0.03 | **0.02** | -7.7% | 99.7% | **99.9%** | +0.2% |
| `jitter` | `error_lv3` | 0.04 | **0.04** | -2.4% | 95.0% | **95.3%** | +0.3% |
| `stagger` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv1` | 0.01 | 0.01 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv2` | 0.04 | **0.02** | -40.0% | 98.8% | **99.9%** | +1.1% |
| `stagger` | `error_lv3` | 0.04 | **0.04** | -8.9% | 93.9% | **94.6%** | +0.6% |
| `dwell_and_switch` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `dwell_and_switch` | `error_lv1` | 0.01 | 0.01 | +0.0% | 100.0% | 100.0% | +0.0% |
| `dwell_and_switch` | `error_lv2` | 0.03 | 0.03 | +0.0% | 99.9% | **99.9%** | +0.0% |
| `dwell_and_switch` | `error_lv3` | 0.05 | **0.04** | -16.7% | 94.9% | **95.4%** | +0.6% |
| `sliding` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv1` | 0.01 | 0.01 | +0.0% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv2` | 0.02 | 0.02 | +0.0% | 99.9% | 99.9% | +0.0% |
| `sliding` | `error_lv3` | 0.04 | **0.04** | -2.4% | 95.4% | **95.4%** | +0.0% |

### Angle of Arrival (AOA) (Gate Tolerance: ±2°)

| Radar Type | Error Level | Zero-Shot MAE (deg) | LoRA SFT MAE (deg) | MAE Δ (%) | Zero-Shot Hit Rate | LoRA Hit Rate | Hit Rate Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv1` | 0.04 | 0.04 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv2` | 0.18 | **0.17** | -7.2% | 99.9% | **100.0%** | +0.1% |
| `stable` | `error_lv3` | 0.40 | **0.40** | -0.7% | 100.0% | 100.0% | +0.0% |
| `jitter` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `jitter` | `error_lv1` | 0.04 | **0.04** | -2.4% | 100.0% | 100.0% | +0.0% |
| `jitter` | `error_lv2` | 0.32 | **0.17** | -48.1% | 99.7% | **100.0%** | +0.3% |
| `jitter` | `error_lv3` | 0.41 | **0.41** | -1.0% | 99.9% | **100.0%** | +0.0% |
| `stagger` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv1` | 0.04 | 0.04 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv2` | 0.83 | **0.17** | -79.7% | 98.6% | **99.9%** | +1.3% |
| `stagger` | `error_lv3` | 0.55 | **0.41** | -25.8% | 99.6% | **100.0%** | +0.4% |
| `dwell_and_switch` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `dwell_and_switch` | `error_lv1` | 0.04 | 0.04 | +0.0% | 100.0% | 100.0% | +0.0% |
| `dwell_and_switch` | `error_lv2` | 0.30 | **0.17** | -43.7% | 99.5% | **100.0%** | +0.5% |
| `dwell_and_switch` | `error_lv3` | 0.53 | **0.41** | -22.2% | 99.7% | **100.0%** | +0.2% |
| `sliding` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv1` | 0.04 | **0.04** | -2.4% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv2` | 0.32 | **0.17** | -48.3% | 99.6% | **100.0%** | +0.3% |
| `sliding` | `error_lv3` | 0.45 | **0.43** | -3.4% | 99.9% | **99.9%** | +0.0% |

### Received Peak Power (Amplitude) (Gate Tolerance: ±2 dBm)

| Radar Type | Error Level | Zero-Shot MAE (dBm) | LoRA SFT MAE (dBm) | MAE Δ (%) | Zero-Shot Hit Rate | LoRA Hit Rate | Hit Rate Δ |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv1` | 0.16 | 0.16 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv2` | 0.41 | **0.40** | -0.7% | 100.0% | 100.0% | +0.0% |
| `stable` | `error_lv3` | 0.81 | **0.80** | -1.0% | 95.3% | **95.5%** | +0.2% |
| `jitter` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `jitter` | `error_lv1` | 0.16 | **0.16** | -0.6% | 100.0% | 100.0% | +0.0% |
| `jitter` | `error_lv2` | 0.41 | **0.40** | -1.0% | 100.0% | **100.0%** | +0.0% |
| `jitter` | `error_lv3` | 0.80 | **0.79** | -1.1% | 95.5% | **95.8%** | +0.2% |
| `stagger` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv1` | 0.16 | **0.16** | -0.6% | 100.0% | 100.0% | +0.0% |
| `stagger` | `error_lv2` | 0.43 | **0.40** | -8.1% | 99.7% | **100.0%** | +0.3% |
| `stagger` | `error_lv3` | 0.81 | **0.80** | -0.9% | 95.2% | **95.6%** | +0.3% |
| `dwell_and_switch` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `dwell_and_switch` | `error_lv1` | 0.16 | **0.16** | -0.6% | 100.0% | 100.0% | +0.0% |
| `dwell_and_switch` | `error_lv2` | 0.40 | **0.40** | -1.2% | 99.9% | **100.0%** | +0.1% |
| `dwell_and_switch` | `error_lv3` | 0.81 | **0.80** | -0.6% | 95.3% | **95.5%** | +0.1% |
| `sliding` | `clean` | 0.00 | 0.00 | +0.0% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv1` | 0.16 | **0.16** | -0.6% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv2` | 0.40 | **0.40** | -0.5% | 100.0% | 100.0% | +0.0% |
| `sliding` | `error_lv3` | 0.80 | **0.79** | -1.1% | 95.6% | **95.6%** | +0.0% |

---

## 2. Joint 5-Channel Multivariate Benchmarks (Fixed)

Predicts all 5 PDW channels simultaneously across the 32-pulse horizon using tactical priority weighted Huber loss.

| Radar Type | Error Level | PRI ZS (μs) | PRI LoRA (μs) | PRI Δ | RF ZS (MHz) | RF LoRA (MHz) | PW LoRA (μs) | AOA LoRA (°) | Amp LoRA (dBm) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | +0.0% | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `stable` | `error_lv1` | 0.22 | **0.16** | -27.8% | 0.13 | 0.16 | 0.01 | 0.04 | 0.16 |
| `stable` | `error_lv2` | 0.63 | **0.60** | -4.1% | 1.13 | 0.90 | 0.02 | 0.16 | 0.41 |
| `stable` | `error_lv3` | 1.07 | **1.06** | -1.5% | 1.55 | 1.63 | 0.04 | 0.40 | 0.81 |
| `jitter` | `clean` | 39.82 | **39.80** | -0.1% | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `jitter` | `error_lv1` | 40.34 | **40.27** | -0.2% | 0.17 | 0.14 | 0.01 | 0.04 | 0.16 |
| `jitter` | `error_lv2` | 40.50 | **40.49** | -0.0% | 0.91 | 0.91 | 0.02 | 0.17 | 0.40 |
| `jitter` | `error_lv3` | 40.39 | **40.23** | -0.4% | 1.66 | 2.07 | 0.04 | 0.41 | 0.79 |
| `stagger` | `clean` | 3.21 | **2.69** | -16.2% | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `stagger` | `error_lv1` | 38.62 | **27.75** | -28.1% | 0.23 | 0.23 | 0.01 | 0.04 | 0.16 |
| `stagger` | `error_lv2` | 79.36 | **68.86** | -13.2% | 3.29 | 1.06 | 0.02 | 0.17 | 0.40 |
| `stagger` | `error_lv3` | 97.98 | **94.09** | -4.0% | 1.46 | 1.72 | 0.04 | 0.41 | 0.80 |
| `dwell_and_switch` | `clean` | 26.76 | **23.42** | -12.5% | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `dwell_and_switch` | `error_lv1` | 19.14 | **8.79** | -54.1% | 0.14 | 0.20 | 0.01 | 0.04 | 0.16 |
| `dwell_and_switch` | `error_lv2` | 40.78 | **21.52** | -47.2% | 1.09 | 1.09 | 0.02 | 0.17 | 0.40 |
| `dwell_and_switch` | `error_lv3` | 64.40 | **37.96** | -41.1% | 2.75 | 1.85 | 0.04 | 0.41 | 0.80 |
| `sliding` | `clean` | 107.05 | **20.58** | -80.8% | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `sliding` | `error_lv1` | 17.81 | **6.84** | -61.6% | 0.15 | 0.17 | 0.01 | 0.04 | 0.16 |
| `sliding` | `error_lv2` | 35.64 | **17.47** | -51.0% | 1.01 | 0.90 | 0.02 | 0.17 | 0.40 |
| `sliding` | `error_lv3` | 51.49 | **31.12** | -39.6% | 1.52 | 1.74 | 0.04 | 0.40 | 0.80 |

---

## 3. Univariate vs. Joint 5-Channel Multivariate Performance (Fixed)

Direct side-by-side comparison between dedicated univariate adapters and the unified joint multivariate adapter:

| Radar Type | Error Level | UV PRI MAE (μs) | MV PRI MAE (μs) | PRI Δ (%) | UV PRI Hit | MV PRI Hit | UV RF MAE (MHz) | MV RF MAE (MHz) |
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