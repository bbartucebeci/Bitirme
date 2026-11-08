# Toto 2.0 Foundation Model Benchmark

This directory provides the evaluation suite for **Toto 2.0** (`Datadog/Toto-2.0-22m`), a lightweight 22M-parameter time-series foundation model developed by Datadog.

---

## 1. Overview & Protocol

- **Context & Horizon**: 96 observed interval pulses context, 32 pulses forecast horizon.
- **Model Size**: ~22M parameters.
- **Key Operational Trait**: High noise robustness on corruptions (`error_lv1`–`error_lv3`), achieving competitive performance against classic Kalman and Period Estimation algorithms while remaining an unassisted neural forecaster.
- **Emitter Masking**: True emitter pulses (`Radar_ID == "R_SINGLE"`) scored; receiver Poisson false alarms and echoes masked out.
- **Shared Infrastructure**: Employs `foundation_models/common/dataset.py` and `foundation_models/common/metrics.py`.

---

## 2. Installation & Requirements

Install `toto` in your PyTorch environment:

```bash
pip install "toto-models>=1.0.0"
```

---

## 3. Usage & CLI Commands

```bash
# Evaluate Zero-Shot PRI on Fixed profile
python -m foundation_models.toto2.evaluate --profile-mode fixed --target-param PRI

# Evaluate with Hybrid ESM Pre-Filtering (--clean-context)
python -m foundation_models.toto2.evaluate --profile-mode fixed --target-param PRI --clean-context

# Evaluate specific radar type or error level
python -m foundation_models.toto2.evaluate \
  --profile-mode fixed \
  --radar-type sliding \
  --error-level error_lv2

# Run without generating diagnostic plots
python -m foundation_models.toto2.evaluate --profile-mode fixed --no-plots
```

---

## 4. Results Organization

Results are written to:
```
results/toto2/
└── zero_shot/
    └── univariate_fixed/
        └── pri/
            ├── metrics.csv
            ├── report.md
            └── plots/
                ├── stable_clean.png
                └── ...
```
