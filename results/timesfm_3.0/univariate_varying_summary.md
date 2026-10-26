# PULSAR: Comprehensive TimesFM 3.0 Benchmark Summary [Univariate Varying Profile]

**Compiled on**: 2026-10-26 23:05:00

Evaluates off-the-shelf Zero-Shot vs. LoRA Fine-Tuned TimesFM 3.0 across all 5 PDW parameters on varying profile datasets.
Non-emitter pulses and false alarms are masked out; errors reflect true emitter pulse tracking accuracy.

---

## Pulse Repetition Interval (PRI) (Gate Tolerance: ±10 μs)

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

## Carrier Frequency (RF) (Gate Tolerance: ±2 MHz)

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

## Pulse Width (PW) (Gate Tolerance: ±0.1 μs)

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

## Angle of Arrival (AOA) (Gate Tolerance: ±2°)

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

## Received Peak Power (Amplitude) (Gate Tolerance: ±2 dBm)

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