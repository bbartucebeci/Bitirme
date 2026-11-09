# t0-gamma: Partially Omitted Signal Prediction and Reconstruction Report

This directory contains empirical demonstrations of **t0-gamma** forecasting radar pulse streams when the incoming Electronic Support Measures (ESM) intercept sequence suffers from **partially omitted signals** (missed pulses, receiver dropout, and fading).

## Generated Demonstration Plots

1. **`1_stable_radar_omitted_pulses.png`**: Stable PRI radar under 20% random pulse omission. Demonstrates flat reconstruction of the underlying 1000 μs emitter clock.
2. **`2_stagger_radar_omitted_pulses.png`**: 4-position Stagger PRI radar under 18% omission. Demonstrates pattern restoration and tactical gate conformance.
3. **`3_dwell_switch_omitted_pulses.png`**: Dwell-and-switch radar under 15% omission. Tracks burst plateau transitions despite dropped pulses.
4. **`4_sliding_pri_omitted_pulses.png`**: Sliding PRI sawtooth ramp under 15% omission. Recovers linear slope and phase.
5. **`5_multivariate_omitted_signal_dashboard.png`**: Synchronized 5-channel tactical dashboard (PRI, RF, PW, AOA, Amp) forecasting through intermittent signal dropouts.
6. **`6_omission_rate_robustness_comparison.png`**: Empirical robustness analysis across omission rates from 0% to 50%, comparing Zero-Shot vs LoRA Fine-Tuned t0-gamma on MAE and Tactical Hit Rate.

## Technical Summary

- **Signal Omission Mechanism**: In operational EW scenarios, non-ideal Probability of Intercept (POI < 1.0) and CFAR receiver thresholds drop pulses, causing measured $\Delta TOA$ intervals to jump to integer multiples of the fundamental PRI.
- **LoRA Adaptation Advantage**: LoRA fine-tuning adapts attention heads (`wQKV`, `wO`) to filter out pulse dropouts as outlier spikes and recover the true continuous radar modulation sequence with high tactical gate hit rates.
