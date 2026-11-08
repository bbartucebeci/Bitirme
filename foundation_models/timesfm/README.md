# Google TimesFM 3.0 Single-Radar Benchmark

This directory provides the end-to-end implementation for running zero-shot and supervised fine-tuned (LoRA SFT) benchmarks using **Google TimesFM 3.0** (`google/timesfm-2.0-500m-pytorch` / TimesFM 3.0 PyTorch port) on PULSAR Electronic Warfare PDW sequences.

---

## 1. Overview & Protocol

- **Context & Horizon**: 96 observed interval pulses context, 32 pulses forecast horizon.
- **Emitter Masking**: True emitter pulses (`Radar_ID == "R_SINGLE"`) are scored; Poisson noise, multipath, and receiver false alarms are masked out during evaluation.
- **Zero-Drop Anchor Rule**: Pulse 0 arrival-time anchor (`Measured_Delta_TOA == 0.0`) is dynamically stripped so context strictly represents interval transitions.
- **Modality Support**:
  - **Univariate**: Individual forecasting across all 5 PDW parameters (`PRI`, `Frequency`, `PW`, `AOA`, `Amplitude`).
  - **Multivariate (5-Channel)**: Joint simultaneous forecasting across all 5 channels with normalized loss weighting.

---

## 2. LoRA Supervised Fine-Tuning (SFT)

PEFT Low-Rank Adaptation (LoRA) is applied to attention projections and feed-forward layers:
- **Rank ($r$)**: 16
- **Alpha ($\alpha$)**: 32
- **Dropout**: 0.05
- **Target Modules**: `seq_attn.query_proj`, `seq_attn.value_proj`, `ff0`, `ff1`
- **Loss**: Smooth L1 / Huber Loss ($\delta=1.0$)
- **Optimization**: AdamW ($\text{lr}=10^{-4}$), batch size 64, 3 epochs over 14,000 unified sequences.

Saved checkpoints follow the method-first hierarchy:
```
models/lora_sft/timesfm/
├── pri/best_model/
├── frequency/best_model/
├── pw/best_model/
├── aoa/best_model/
├── amplitude/best_model/
├── multivariate_fixed/best_model/
└── varying/
    ├── pri/best_model/
    ├── frequency/best_model/
    ├── pw/best_model/
    ├── aoa/best_model/
    ├── amplitude/best_model/
    └── multivariate_varying/best_model/
```

---

## 3. Usage & CLI Execution

### A. Univariate Zero-Shot Evaluation
```bash
# Evaluate Zero-Shot PRI on Fixed profile
python -m foundation_models.timesfm.evaluate --profile-mode fixed --target-param PRI

# Evaluate with Classical Hybrid Pre-Filtering (--clean-context)
python -m foundation_models.timesfm.evaluate --profile-mode fixed --target-param PRI --clean-context
```

### B. Univariate LoRA Fine-Tuning
```bash
# Fine-tune PRI on Fixed profile
python -m foundation_models.timesfm.train --profile-mode fixed --target-param PRI --epochs 3 --batch-size 64

# Fine-tune all 5 individual PDW parameters
python -m foundation_models.timesfm.train --profile-mode fixed --target-param Frequency --epochs 3
python -m foundation_models.timesfm.train --profile-mode fixed --target-param PW --epochs 3
python -m foundation_models.timesfm.train --profile-mode fixed --target-param AOA --epochs 3
python -m foundation_models.timesfm.train --profile-mode fixed --target-param Amplitude --epochs 3
```

### C. Univariate LoRA Evaluation
```bash
# Evaluate trained LoRA checkpoint on Fixed PRI
python -m foundation_models.timesfm.evaluate \
  --profile-mode fixed \
  --target-param PRI \
  --weights-dir models/lora_sft/timesfm/pri/best_model
```

### D. 5-Channel Joint Multivariate Training & Evaluation
```bash
# Train 5-channel joint multivariate model
python -m foundation_models.timesfm.train_multivariate --profile-mode fixed --epochs 3 --batch-size 64

# Evaluate 5-channel multivariate zero-shot vs LoRA
python -m foundation_models.timesfm.evaluate_multivariate --profile-mode fixed
python -m foundation_models.timesfm.evaluate_multivariate --profile-mode fixed \
  --weights-dir models/lora_sft/timesfm/multivariate_fixed/best_model
```

### E. Cross-Profile Generalization Evaluation
```bash
# Test Fixed checkpoints on Varying data, and Varying checkpoints on Fixed data
python -m foundation_models.timesfm.run_cross_evaluation --target-param PRI
python -m foundation_models.timesfm.run_cross_evaluation --target-param multivariate
```

---

## 4. Results Directory Layout

Results are structured under `results/timesfm/`:
```
results/timesfm/
├── zero_shot/
│   ├── univariate_fixed/{pri,frequency,pw,aoa,amplitude}/
│   ├── univariate_varying/{pri,frequency,pw,aoa,amplitude}/
│   ├── multivariate_fixed/
│   └── multivariate_varying/
├── lora_sft/
│   ├── univariate_fixed/{pri,frequency,pw,aoa,amplitude}/
│   ├── univariate_varying/{pri,frequency,pw,aoa,amplitude}/
│   ├── multivariate_fixed/
│   └── multivariate_varying/
├── cross_evaluation/
└── summaries/
    ├── fixed_summary.md
    ├── varying_summary.md
    └── cross_profile_generalization_report.md
```
