# PULSAR: Comprehensive TimesFM 3.0 Benchmark Summary (Univariate Fixed Profile)

**Compiled on**: 2026-10-26 20:29:56

This report provides an end-to-end performance assessment of Google TimesFM 3.0 across all 5 Pulse Description Word (PDW) parameters.
Crucially, **receiver noise pulses, false alarms, and missing gaps are filtered out**, evaluating model predictions strictly against ground-truth emitter pulses.

---

## Pulse Repetition Interval (PRI) (Gate Tolerance: ±10 μs)

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

## Carrier Frequency (RF) (Gate Tolerance: ±2 MHz)

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

## Pulse Width (PW) (Gate Tolerance: ±0.1 μs)

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

## Angle of Arrival (AOA) (Gate Tolerance: ±2°)

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

## Received Peak Power (Amplitude) (Gate Tolerance: ±2 dBm)

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