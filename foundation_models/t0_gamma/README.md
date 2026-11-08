# t0-gamma Foundation Model Benchmark

This directory provides the evaluation suite for **t0-gamma** (`theforecastingcompany/t0-gamma`), a 50M-parameter foundation model developed by TheForecastingCompany with support for temporal forecasting and auxiliary covariate conditioning.

---

## 1. Overview & Protocol

- **Context & Horizon**: 96 observed interval pulses context, 32 pulses forecast horizon.
- **Model Size**: ~50M parameters.
- **Evaluation Paradigm**: Zero-shot inference evaluated across 20 fixed single-radar conditions (5 radar types × 4 noise levels, 200 sequences per condition = 4,000 sequences).
- **Emitter Masking**: True emitter pulses (`Radar_ID == "R_SINGLE"`) scored; receiver Poisson false alarms and echoes masked out.
- **Shared Infrastructure**: Uses `foundation_models/common/dataset.py` and `foundation_models/common/metrics.py`.

---

## 2. Installation & Requirements

Install `t0` in your PyTorch environment:

```bash
pip install "tfc-t0[torch]>=0.6.0" rotary-embedding-torch
```

---

## 3. Usage & CLI Commands

```bash
# Evaluate Zero-Shot PRI on Fixed profile
python -m foundation_models.t0_gamma.evaluate --profile-mode fixed --target-param PRI

# Evaluate with Hybrid ESM Pre-Filtering (--clean-context)
python -m foundation_models.t0_gamma.evaluate --profile-mode fixed --target-param PRI --clean-context

# Evaluate specific radar type or error level
python -m foundation_models.t0_gamma.evaluate \
  --profile-mode fixed \
  --radar-type dwell_and_switch \
  --error-level clean

# Run without generating diagnostic plots
python -m foundation_models.t0_gamma.evaluate --profile-mode fixed --no-plots
```

---

## 4. Results Organization

Results are written to:
```
results/t0_gamma/
└── zero_shot/
    └── univariate_fixed/
        └── pri/
            ├── metrics.csv
            ├── report.md
            └── plots/
                ├── stable_clean.png
                └── ...
```
