# Chronos-2 complex PRI LoRA SFT experiment

Dataset: new_complex_pri. Completed conditions: 1536. Mode: boundary. Horizon: 32.
Adapters are fitted on train only, selected by validation loss, and scored on test only. Input files are never modified.
Tail mode shares the final targets; boundary mode shares the first H consecutive source pulses after the stored context boundary.
PRI input is observed Delta-TOA; PRI target is source PRI, following the repository definition.
Frequency input/target retain the repository's measured Frequency definition.
Multivariate inference receives five channels; only PRI and Frequency are scored and plotted.
No cross-radar/error-level averages are used for comparison. No context cleaning is applied.
Timing is wall time for prediction plus CPU conversion; per-sequence timing is batch-amortized.

## Condition reports

- [PRI, L=96, fixed](PRI/L96/fixed/report.md)
- [PRI, L=96, varying](PRI/L96/varying/report.md)
- [PRI, L=256, fixed](PRI/L256/fixed/report.md)
- [PRI, L=256, varying](PRI/L256/varying/report.md)
- [PRI, L=512, fixed](PRI/L512/fixed/report.md)
- [PRI, L=512, varying](PRI/L512/varying/report.md)
- [PRI, L=992, fixed](PRI/L992/fixed/report.md)
- [PRI, L=992, varying](PRI/L992/varying/report.md)
- [Frequency, L=96, fixed](Frequency/L96/fixed/report.md)
- [Frequency, L=96, varying](Frequency/L96/varying/report.md)
- [Frequency, L=256, fixed](Frequency/L256/fixed/report.md)
- [Frequency, L=256, varying](Frequency/L256/varying/report.md)
- [Frequency, L=512, fixed](Frequency/L512/fixed/report.md)
- [Frequency, L=512, varying](Frequency/L512/varying/report.md)
- [Frequency, L=992, fixed](Frequency/L992/fixed/report.md)
- [Frequency, L=992, varying](Frequency/L992/varying/report.md)
- [multivariate, L=96, fixed](multivariate/L96/fixed/report.md)
- [multivariate, L=96, varying](multivariate/L96/varying/report.md)
- [multivariate, L=256, fixed](multivariate/L256/fixed/report.md)
- [multivariate, L=256, varying](multivariate/L256/varying/report.md)
- [multivariate, L=512, fixed](multivariate/L512/fixed/report.md)
- [multivariate, L=512, varying](multivariate/L512/varying/report.md)
- [multivariate, L=992, fixed](multivariate/L992/fixed/report.md)
- [multivariate, L=992, varying](multivariate/L992/varying/report.md)
