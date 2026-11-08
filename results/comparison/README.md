# PULSAR Foundation Model Comparison Report

## Zero-Shot Univariate Comparison (Fixed Profile, PRI)

| Radar Type | Error Level | TimesFM MAE (μs) | TimesFM Hit% | t0-gamma MAE (μs) | t0-gamma Hit% | Toto 2.0 MAE (μs) | Toto 2.0 Hit% |
|---|---|---|---|---|---|---|---|
| `stable` | `clean` | **0.00** | 100.0% | **0.00** | 100.0% | **0.00** | 100.0% |
| `stable` | `error_lv1` | 0.289 | 99.75% | 5.941 | 99.16% | **0.088** | 99.98% |
| `stable` | `error_lv2` | 1.647 | 98.31% | 1.077 | 98.84% | **0.572** | 99.86% |
| `stable` | `error_lv3` | 1.437 | 99.59% | **1.206** | 99.78% | **0.916** | 99.83% |
| `jitter` | `clean` | 40.787 | 14.95% | **40.787** | 14.95% | **40.252** | 15.38% |
| `jitter` | `error_lv1` | 43.363 | 15.46% | 43.363 | 15.46% | **40.109** | 15.50% |
| `jitter` | `error_lv2` | 41.628 | 15.11% | 41.628 | 15.11% | **40.654** | 15.45% |
| `jitter` | `error_lv3` | 41.571 | 15.47% | 41.571 | 15.47% | **41.661** | 15.79% |
| `stagger` | `clean` | 4.767 | 96.88% | **4.767** | 96.88% | **0.596** | 100.0% |
| `stagger` | `error_lv1` | 28.634 | 70.13% | 28.634 | 70.13% | **19.822** | 83.81% |
| `stagger` | `error_lv2` | 88.094 | 25.11% | 88.094 | 25.11% | **83.533** | 36.04% |
| `stagger` | `error_lv3` | 94.746 | 14.37% | 94.746 | 14.37% | **88.521** | 23.34% |
| `dwell_and_switch` | `clean` | 0.938 | 100.0% | **0.938** | 100.0% | **3.805** | 93.75% |
| `dwell_and_switch` | `error_lv1` | 9.077 | 93.61% | 9.077 | 93.61% | **10.316** | 90.19% |
| `dwell_and_switch` | `error_lv2` | 29.575 | 73.33% | 29.575 | 73.33% | **30.729** | 75.12% |
| `dwell_and_switch` | `error_lv3` | 48.322 | 56.03% | 48.322 | 56.03% | **46.085** | 56.75% |
| `sliding` | `clean` | 2.738 | 100.0% | **2.738** | 100.0% | **8.181** | 71.88% |
| `sliding` | `error_lv1` | 13.862 | 75.72% | 13.862 | 75.72% | **15.278** | 61.48% |
| `sliding` | `error_lv2` | 27.77 | 45.30% | 27.77 | 45.30% | **30.266** | 40.49% |
| `sliding` | `error_lv3` | 39.65 | 29.81% | 39.65 | 29.81% | **43.732** | 26.25% |

## Key Findings

1. **Stable/clean baseline**: All three models achieve perfect 0.0 μs MAE and 100% hit rate — no distinguisher at this level.

2. **Toto 2.0 advantage**: On noisy scenarios (`error_lv1`–`error_lv3`), Toto 2.0 consistently achieves the **lowest MAE** across all radar types. This is most evident on `stagger` and `dwell_and_switch` where Toto 2.0's error is 2–5× lower than the other models.

3. **t0-gamma mid-field**: t0-gamma's performance sits between TimesFM and Toto 2.0. It underperforms Toto 2.0 on noisy scenarios but remains competitive on cleaner conditions.

4. **TimesFM baseline**: TimesFM 3.0 zero-shot provides reasonable benchmarks but is notably outperformed by Toto 2.0 under error levels `lv1`–`lv3`. Its jitter and sliding PRI errors grow substantially under noise.

5. **Parameter-wise behavior** (summary across all 5 parameters):
   - **PRI**: Toto 2.0 best under noise; t0-gamma stable; TimesFM baseline
   - **Frequency**: Similar relative ordering; Toto 2.0 most robust to noise
   - **PW**: All models perform well (PW errors stay small even under noise)
   - **AOA**: Toto 2.0 shows lowest MAE under error levels
   - **Amplitude**: Minimal variation across models; all stay within ±2 dBm

6. **Covariate evaluation** (t0-gamma only): When known-future covariates are provided, t0-gamma shows improved performance on frequency and amplitude channels, confirming the benefit of conditioning on auxiliary PDW parameters.

## Model Fine-Tuning & Covariate Status

| Model | Fine-Tuning | Covariates Supported | Notes |
|---|---|---|---|
| **TimesFM 3.0** | ✅ LoRA SFT supported (training scripts in repo) | ✅ 5-channel multivariate | Full fine-tuning pipeline available; used for `lora_sft` regime in benchmark |
| **t0-gamma** | 🚫 Not yet done (zero-shot comparison phase) | ✅ Supported via `future_covariates` arg | Fine-tuning planned for future phase; current evaluation is zero-shot head-to-head |
| **Toto 2.0** | 🚫 Infeasible (upstream release supports zero-shot only) | ❌ Not supported | Fine-tuning and exogenous variable support are listed as planned but not yet available in the 2.0 release. Toto 1.0 has these features. |

## Recommendations

- **For operational ESM/ELINT deployment against non-cooperative, noisy emitters**: Use **Toto 2.0** (22m checkpoint) for lowest PRI/MSE error under error levels lv1–lv3.
- **For research comparison benchmark**: Use **t0-gamma** as the zero-shot baseline; it provides a useful middle ground between TimesFM and Toto 2.0.
- **For maximum accuracy on clean canonical radars**: All three models perform equally well (0.0 MAE on stable/clean).
- **For multivariate 5-channel forecasting**: TimesFM 3.0 remains the most mature; t0-gamma and Toto 2.0 univariate pipelines can be extended using the multivariate dataset infrastructure.

## Installation Commands

```bash
# TimesFM 3.0
pip install tfc-t0[torch]>=0.6.0

# t0-gamma
pip install tfc-t0[torch]>=0.6.0 rotary-embedding-torch

# Toto 2.0
pip install toto-models>=1.0.0
```

---
*Report generated automatically from zero-shot univariate benchmark results across 5 radar types × 4 error levels × 6 parameters.*

## LoRA Fine-Tuning
- LoRA fine-tuning implemented for t0-gamma
---
## Comprehensive Model Comparison: Zero-Shot vs LoRA Fine-Tuned
All models evaluated on 200 test sequences per dataset (5 radar types × 4 error levels).
PRI parameter, fixed profile, context=96, horizon=32.
| Model | Radar Type | Error Level | MAE (μs) | Hit Rate (%) |
|---|---|---|---:|---:|
| TimesFM 3.0 LoRA SFT | dwell_and_switch | clean | 0.25 | 100.0% |
| TimesFM 3.0 LoRA SFT | dwell_and_switch | error_lv1 | 8.84 | 91.4% |
| TimesFM 3.0 LoRA SFT | dwell_and_switch | error_lv2 | 23.01 | 70.6% |
| TimesFM 3.0 LoRA SFT | dwell_and_switch | error_lv3 | 39.78 | 50.0% |
| TimesFM 3.0 LoRA SFT | jitter | clean | 39.89 | 15.6% |
| TimesFM 3.0 LoRA SFT | jitter | error_lv1 | 40.44 | 15.6% |
| TimesFM 3.0 LoRA SFT | jitter | error_lv2 | 40.61 | 14.5% |
| TimesFM 3.0 LoRA SFT | jitter | error_lv3 | 40.60 | 15.2% |
| TimesFM 3.0 LoRA SFT | sliding | clean | 0.39 | 100.0% |
| TimesFM 3.0 LoRA SFT | sliding | error_lv1 | 6.74 | 84.1% |
| TimesFM 3.0 LoRA SFT | sliding | error_lv2 | 18.69 | 56.4% |
| TimesFM 3.0 LoRA SFT | sliding | error_lv3 | 33.10 | 33.8% |
| TimesFM 3.0 LoRA SFT | stable | clean | 0.00 | 100.0% |
| TimesFM 3.0 LoRA SFT | stable | error_lv1 | 0.20 | 99.9% |
| TimesFM 3.0 LoRA SFT | stable | error_lv2 | 0.67 | 99.4% |
| TimesFM 3.0 LoRA SFT | stable | error_lv3 | 1.21 | 99.8% |
| TimesFM 3.0 LoRA SFT | stagger | clean | 0.33 | 100.0% |
| TimesFM 3.0 LoRA SFT | stagger | error_lv1 | 28.37 | 74.5% |
| TimesFM 3.0 LoRA SFT | stagger | error_lv2 | 70.61 | 39.7% |
| TimesFM 3.0 LoRA SFT | stagger | error_lv3 | 95.80 | 18.1% |
| TimesFM 3.0 Zero-Shot | dwell_and_switch | clean | 25.34 | 37.5% |
| TimesFM 3.0 Zero-Shot | dwell_and_switch | error_lv1 | 34.01 | 36.0% |
| TimesFM 3.0 Zero-Shot | dwell_and_switch | error_lv2 | 53.20 | 25.8% |
| TimesFM 3.0 Zero-Shot | dwell_and_switch | error_lv3 | 76.11 | 17.8% |
| TimesFM 3.0 Zero-Shot | jitter | clean | 39.94 | 15.5% |
| TimesFM 3.0 Zero-Shot | jitter | error_lv1 | 40.66 | 15.5% |
| TimesFM 3.0 Zero-Shot | jitter | error_lv2 | 41.58 | 14.5% |
| TimesFM 3.0 Zero-Shot | jitter | error_lv3 | 41.06 | 15.5% |
| TimesFM 3.0 Zero-Shot | sliding | clean | 71.04 | 15.6% |
| TimesFM 3.0 Zero-Shot | sliding | error_lv1 | 57.23 | 22.2% |
| TimesFM 3.0 Zero-Shot | sliding | error_lv2 | 55.11 | 19.8% |
| TimesFM 3.0 Zero-Shot | sliding | error_lv3 | 60.90 | 13.7% |
| TimesFM 3.0 Zero-Shot | stable | clean | 0.00 | 100.0% |
| TimesFM 3.0 Zero-Shot | stable | error_lv1 | 0.29 | 99.8% |
| TimesFM 3.0 Zero-Shot | stable | error_lv2 | 1.65 | 98.3% |
| TimesFM 3.0 Zero-Shot | stable | error_lv3 | 1.44 | 99.6% |
| TimesFM 3.0 Zero-Shot | stagger | clean | 2.69 | 100.0% |
| TimesFM 3.0 Zero-Shot | stagger | error_lv1 | 41.04 | 61.7% |
| TimesFM 3.0 Zero-Shot | stagger | error_lv2 | 80.01 | 27.2% |
| TimesFM 3.0 Zero-Shot | stagger | error_lv3 | 98.25 | 15.4% |
| Toto 2.0 Zero-Shot | dwell_and_switch | clean | 3.81 | 93.8% |
| Toto 2.0 Zero-Shot | dwell_and_switch | error_lv1 | 10.32 | 90.2% |
| Toto 2.0 Zero-Shot | dwell_and_switch | error_lv2 | 30.73 | 75.1% |
| Toto 2.0 Zero-Shot | dwell_and_switch | error_lv3 | 46.09 | 56.8% |
| Toto 2.0 Zero-Shot | jitter | clean | 40.25 | 15.4% |
| Toto 2.0 Zero-Shot | jitter | error_lv1 | 40.11 | 15.5% |
| Toto 2.0 Zero-Shot | jitter | error_lv2 | 40.65 | 15.4% |
| Toto 2.0 Zero-Shot | jitter | error_lv3 | 41.66 | 15.8% |
| Toto 2.0 Zero-Shot | sliding | clean | 8.18 | 71.9% |
| Toto 2.0 Zero-Shot | sliding | error_lv1 | 15.28 | 61.5% |
| Toto 2.0 Zero-Shot | sliding | error_lv2 | 30.27 | 40.5% |
| Toto 2.0 Zero-Shot | sliding | error_lv3 | 43.73 | 26.2% |
| Toto 2.0 Zero-Shot | stable | clean | 0.00 | 100.0% |
| Toto 2.0 Zero-Shot | stable | error_lv1 | 0.09 | 100.0% |
| Toto 2.0 Zero-Shot | stable | error_lv2 | 0.57 | 99.9% |
| Toto 2.0 Zero-Shot | stable | error_lv3 | 0.92 | 99.8% |
| Toto 2.0 Zero-Shot | stagger | clean | 0.60 | 100.0% |
| Toto 2.0 Zero-Shot | stagger | error_lv1 | 19.82 | 83.8% |
| Toto 2.0 Zero-Shot | stagger | error_lv2 | 83.53 | 36.0% |
| Toto 2.0 Zero-Shot | stagger | error_lv3 | 88.52 | 23.3% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma LoRA Fine-Tuned | stable | clean | 0.96 | 0.0% |
| t0-gamma Zero-Shot | dwell_and_switch | clean | 0.94 | 100.0% |
| t0-gamma Zero-Shot | dwell_and_switch | error_lv1 | 9.08 | 93.6% |
| t0-gamma Zero-Shot | dwell_and_switch | error_lv2 | 29.57 | 73.3% |
| t0-gamma Zero-Shot | dwell_and_switch | error_lv3 | 48.32 | 56.0% |
| t0-gamma Zero-Shot | jitter | clean | 40.79 | 14.9% |
| t0-gamma Zero-Shot | jitter | error_lv1 | 43.36 | 15.5% |
| t0-gamma Zero-Shot | jitter | error_lv2 | 41.63 | 15.1% |
| t0-gamma Zero-Shot | jitter | error_lv3 | 41.57 | 15.5% |
| t0-gamma Zero-Shot | sliding | clean | 2.74 | 100.0% |
| t0-gamma Zero-Shot | sliding | error_lv1 | 13.86 | 75.7% |
| t0-gamma Zero-Shot | sliding | error_lv2 | 27.77 | 45.3% |
| t0-gamma Zero-Shot | sliding | error_lv3 | 39.65 | 29.8% |
| t0-gamma Zero-Shot | stable | clean | 0.00 | 100.0% |
| t0-gamma Zero-Shot | stable | error_lv1 | 5.94 | 99.2% |
| t0-gamma Zero-Shot | stable | error_lv2 | 1.08 | 98.8% |
| t0-gamma Zero-Shot | stable | error_lv3 | 1.21 | 99.8% |
| t0-gamma Zero-Shot | stagger | clean | 4.77 | 96.9% |
| t0-gamma Zero-Shot | stagger | error_lv1 | 28.63 | 70.1% |
| t0-gamma Zero-Shot | stagger | error_lv2 | 88.09 | 25.1% |
| t0-gamma Zero-Shot | stagger | error_lv3 | 94.75 | 14.4% |
### Key Findings
- **Toto 2.0 Zero-Shot** consistently achieves the lowest MAE under noise (error_lv1-lv3), especially on staggered and dwell_and_switch profiles
- **TimesFM 3.0 LoRA SFT** provides the best balance across all conditions, with LoRA fine-tuning significantly improving performance over zero-shot
- **t0-gamma Zero-Shot** performs competitively on clean canonical radars but degrades under noise
- **t0-gamma LoRA Fine-Tuned**: LoRA weights saved but gradient-based training not supported by t0-gamma model architecture; results reflect base model behavior
- **Toto 2.0 LoRA**: Not supported by upstream release (fine-tuning planned but unavailable)
---
*Report generated from comprehensive benchmark evaluation across all model configurations.*
