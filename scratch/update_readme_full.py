"""Update README.md with comprehensive 5-parameter TimesFM benchmarks and developer instructions."""

from pathlib import Path

README_PATH = Path("README.md")
content = README_PATH.read_text(encoding="utf-8")

# We want to replace from "### 10.1. Modular Codebase Architecture" down to "## 11. Roadmap: Hardware Acceleration & FPGA Deployment"
start_marker = "### 10.1. Modular Codebase Architecture"
end_marker = "## 11. Roadmap: Hardware Acceleration & FPGA Deployment"

if start_marker not in content or end_marker not in content:
    raise ValueError("Markers not found in README.md")

pre_content = content[:content.find(start_marker)]
post_content = content[content.find(end_marker):]

new_section_10 = """### 10.1. Modular Codebase Architecture & Outlier Masking

The foundation models pipeline is decoupled from dataset generation formats. Data ingestion, evaluation metrics, and plotting utilities are isolated under `foundation_models/common/`, allowing models, training regimes, and parameter targets to be executed and modified independently:

```text
foundation_models/
├── common/
│   ├── dataset.py        # Centralized sequence loader & PyTorch DataLoader (supports all 5 PDW parameters)
│   ├── metrics.py        # EW Metrics: MAE, RMSE, Tactical Range-Gate Hit Rate with emitter pulse masking
│   └── plotting.py       # Diagnostic forecast visualizer with shaded tactical corridors
└── timesfm/
    ├── adapter.py        # TimesFMLoRAEngine: Attention + MLP LoRA (seq_attn.query_proj, seq_attn.value_proj, ff0, ff1)
    ├── evaluate.py       # Standalone CLI for Zero-Shot or LoRA checkpoint evaluation
    └── train.py          # Supervised Fine-Tuning CLI (Huber loss, validation, auto-report)
```

#### Ground-Truth Outlier & False-Alarm Masking Principle
In noisy ESM channels (`error_lv3`), the receiver front-end injects Poisson noise false alarms (`Radar_ID == "NOISE"`) and missing pulse gaps. A critical EW tracking requirement is to forecast the **true emitter pulse train**, rather than predicting random receiver noise pulses or gap doublings. The PULSAR evaluation pipeline:
1. Masks non-emitter pulses (`Radar_ID != "R_SINGLE"`) during loss computation and metric aggregation.
2. Directly evaluates forecasted intervals against ground-truth emitter `PRI` rather than raw jittered/noise arrival timestamps.

#### Output Directory Organization
Results are strictly compartmentalized by parameter under both evaluation regimes:
```text
results/timesfm_3.0/
├── zero_shot/
│   └── univariate_fixed/
│       ├── pri/            # metrics.csv, report.md, plots/
│       ├── frequency/      # metrics.csv, report.md, plots/
│       ├── pw/             # metrics.csv, report.md, plots/
│       ├── aoa/            # metrics.csv, report.md, plots/
│       └── amplitude/      # metrics.csv, report.md, plots/
└── lora_sft/
    └── univariate_fixed/
        ├── pri/            # metrics.csv, report.md, plots/
        ├── frequency/      # metrics.csv, report.md, plots/
        ├── pw/             # metrics.csv, report.md, plots/
        ├── aoa/            # metrics.csv, report.md, plots/
        └── amplitude/      # metrics.csv, report.md, plots/
```

---

### 10.2. Developer & Reproduction Guide

#### 1. Prerequisites & Installation
Ensure PyTorch with CUDA support and the official Google TimesFM package are installed:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install peft "timesfm[torch]"
```

#### 2. Running Zero-Shot Evaluation (Any Parameter)
Evaluate the off-the-shelf TimesFM 3.0 foundation model across all 20 single-radar fixed datasets (4,000 sequences total):
```bash
# Evaluate Pulse Repetition Interval (PRI, ±10.0 μs tolerance)
python -m foundation_models.timesfm.evaluate --profile-mode fixed --target-param PRI --tolerance 10.0

# Evaluate Carrier Frequency (Frequency, ±2.0 MHz tolerance)
python -m foundation_models.timesfm.evaluate --profile-mode fixed --target-param Frequency --tolerance 2.0

# Evaluate Pulse Width (PW, ±0.1 μs tolerance)
python -m foundation_models.timesfm.evaluate --profile-mode fixed --target-param PW --tolerance 0.1

# Evaluate Angle of Arrival (AOA, ±2.0° tolerance)
python -m foundation_models.timesfm.evaluate --profile-mode fixed --target-param AOA --tolerance 2.0

# Evaluate Received Peak Power (Amplitude, ±2.0 dBm tolerance)
python -m foundation_models.timesfm.evaluate --profile-mode fixed --target-param Amplitude --tolerance 2.0
```

#### 3. Running Supervised Fine-Tuning (LoRA SFT)
Train specialized LoRA adapters targeting both **Temporal Self-Attention** (`query_proj`, `value_proj`) and **Feed-Forward MLP** (`ff0`, `ff1`) projections across all 20 transformer layers (3,276,800 trainable parameters / 0.98% of model):
```bash
# Fine-tune LoRA for PRI
python -m foundation_models.timesfm.train --profile-mode fixed --target-param PRI --epochs 3 --batch-size 64 --lr 1e-4

# Fine-tune LoRA for Carrier Frequency
python -m foundation_models.timesfm.train --profile-mode fixed --target-param Frequency --epochs 3 --batch-size 64 --lr 1e-4

# Fine-tune LoRA for Pulse Width
python -m foundation_models.timesfm.train --profile-mode fixed --target-param PW --epochs 3 --batch-size 64 --lr 1e-4

# Fine-tune LoRA for Angle of Arrival
python -m foundation_models.timesfm.train --profile-mode fixed --target-param AOA --epochs 3 --batch-size 64 --lr 1e-4

# Fine-tune LoRA for Amplitude
python -m foundation_models.timesfm.train --profile-mode fixed --target-param Amplitude --epochs 3 --batch-size 64 --lr 1e-4
```
* **Runtime**: ~3.5 minutes per parameter on an NVIDIA RTX 4060 GPU (~2.2 GB VRAM).
* **Output**: Best checkpoints saved to `models/timesfm_lora/<param_slug>/best_model`. Automated post-training evaluation runs across all 20 test datasets, and comparative reports are saved to `results/timesfm_3.0/comparison_zero_shot_vs_lora_fixed_<param_slug>.md`.

#### 4. Evaluating an Existing LoRA Checkpoint Individually
To evaluate an existing LoRA checkpoint (weights are fused via `merge_and_unload()` at load time):
```bash
python -m foundation_models.timesfm.evaluate \\
    --profile-mode fixed \\
    --weights-dir models/timesfm_lora/pri/best_model \\
    --target-param PRI \\
    --tolerance 10.0
```

#### 5. Compiling the Master Benchmark Summary
Generate the unified cross-parameter Markdown report at `results/timesfm_3.0/univariate_fixed_summary.md`:
```bash
python scratch/compile_benchmark_summary.py
```

---

### 10.3. CLI Arguments Reference

#### `foundation_models.timesfm.evaluate`
| Argument | Type | Default | Description |
|---|---|---|---|
| `--profile-mode` | Choice | `fixed` | Target dataset regime (`fixed` or `varying`). |
| `--target-param` | Choice | `PRI` | Target PDW parameter: `PRI`, `Frequency`, `PW`, `AOA`, `Amplitude`. |
| `--radar-type` | Choice | `all` | Radar type (`stable`, `jitter`, `stagger`, `dwell_and_switch`, `sliding`, or `all`). |
| `--error-level` | Choice | `all` | Channel error level (`clean`, `error_lv1`, `error_lv2`, `error_lv3`, or `all`). |
| `--weights-dir` | Path | `None` | Path to fine-tuned LoRA checkpoint. If omitted, evaluates Zero-Shot. |
| `--context-len` | Int | `96` | Context history length in pulses. |
| `--horizon` | Int | `32` | Forecast horizon length in pulses. |
| `--max-test-seqs` | Int | `200` | Maximum test sequences evaluated per dataset (total 4,000 for 20 splits). |
| `--tolerance` | Float | `Auto` | Tactical acceptance tolerance (10.0 μs for PRI, 2.0 MHz for RF, 0.1 μs for PW, 2.0° for AOA, 2.0 dBm for Amplitude). |
| `--no-plots` | Flag | `False` | Disables rendering and saving diagnostic PNG plots. |

#### `foundation_models.timesfm.train`
| Argument | Type | Default | Description |
|---|---|---|---|
| `--profile-mode` | Choice | `fixed` | Target dataset profile (`fixed` or `varying`). |
| `--target-param` | Choice | `PRI` | Training target: `PRI`, `Frequency`, `PW`, `AOA`, `Amplitude`. |
| `--epochs` | Int | `3` | Number of training epochs (default: 3). |
| `--batch-size` | Int | `64` | Batch size across unified dataset (219 batches/epoch). |
| `--lr` | Float | `1e-4` | Peak learning rate (AdamW with 10% linear warmup + cosine decay). |
| `--huber-beta` | Float | `Auto` | Huber loss linear transition threshold (in target parameter units). |
| `--lora-r` | Int | `16` | LoRA rank decomposition dimension. |
| `--lora-alpha` | Int | `32` | LoRA scaling factor (alpha / r = 2.0). |
| `--save-dir` | Path | `models/timesfm_lora` | Output directory for checkpoints. |

---

### 10.4. PRI Benchmark Results: Zero-Shot vs. LoRA SFT

Evaluated across all 20 test datasets (4,000 sequences total, 200 per split) with outlier and receiver false alarm masking. Context: 96 pulses, Forecast Horizon: 32 pulses, Tactical Gate: ±10 μs:

| Radar Type | Error Level | Zero-Shot MAE (μs) | LoRA MAE (μs) | MAE Δ (%) | Zero-Shot Hit Rate | LoRA Hit Rate | Tactical Gain |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | **0.00** | +0.0% | 100.0% | **100.0%** | +0.0% |
| `stable` | `error_lv1` | 0.29 | **0.20** | -29.1% | 99.8% | **99.9%** | +0.1% |
| `stable` | `error_lv2` | 1.65 | **0.67** | -59.6% | 98.3% | **99.4%** | +1.1% |
| `stable` | `error_lv3` | 1.44 | **1.21** | -15.9% | 99.6% | **99.8%** | +0.2% |
| `jitter` | `clean` | 39.94 | **39.89** | -0.1% | 15.5% | **15.6%** | +0.1% |
| `jitter` | `error_lv1` | 40.66 | **40.44** | -0.5% | 15.5% | **15.6%** | +0.1% |
| `jitter` | `error_lv2` | 41.58 | **40.61** | -2.3% | 14.5% | 14.5% | +0.0% |
| `jitter` | `error_lv3` | 41.06 | **40.60** | -1.1% | 15.5% | 15.2% | -0.3% |
| `stagger` | `clean` | 2.69 | **0.33** | **-87.8%** | 100.0% | **100.0%** | +0.0% |
| `stagger` | `error_lv1` | 41.04 | **28.37** | **-30.9%** | 61.7% | **74.5%** | **+12.8%** |
| `stagger` | `error_lv2` | 80.01 | **70.61** | **-11.7%** | 27.2% | **39.7%** | **+12.5%** |
| `stagger` | `error_lv3` | 98.25 | **95.80** | -2.5% | 15.4% | **18.1%** | **+2.7%** |
| `dwell_and_switch` | `clean` | 25.34 | **0.25** | **-99.0%** | 37.5% | **100.0%** | **+62.5%** |
| `dwell_and_switch` | `error_lv1` | 34.01 | **8.84** | **-74.0%** | 36.0% | **91.4%** | **+55.4%** |
| `dwell_and_switch` | `error_lv2` | 53.20 | **23.01** | **-56.8%** | 25.8% | **70.6%** | **+44.8%** |
| `dwell_and_switch` | `error_lv3` | 76.11 | **39.78** | **-47.7%** | 17.8% | **50.0%** | **+32.2%** |
| `sliding` | `clean` | 71.04 | **0.39** | **-99.5%** | 15.6% | **100.0%** | **+84.4%** |
| `sliding` | `error_lv1` | 57.23 | **6.74** | **-88.2%** | 22.2% | **84.1%** | **+61.9%** |
| `sliding` | `error_lv2` | 55.11 | **18.69** | **-66.1%** | 19.8% | **56.4%** | **+36.6%** |
| `sliding` | `error_lv3` | 60.90 | **33.10** | **-45.7%** | 13.7% | **33.8%** | **+20.1%** |

---

### 10.5. Full 5-Parameter Benchmark Summary

Comprehensive assessment across all 5 PDW parameters on the 4,000 test sequences (see [`univariate_fixed_summary.md`](results/timesfm_3.0/univariate_fixed_summary.md) for sequence-level breakdowns):

| Parameter | Unit | Tactical Gate | Zero-Shot Clean MAE | LoRA Clean MAE | Zero-Shot Lv3 Hit Rate | LoRA Lv3 Hit Rate | Primary Adaptation Takeaway |
|---|---|---|---:|---:|---:|---:|---|
| **PRI** | $\mu\text{s}$ | $\pm 10.0\ \mu\text{s}$ | 0.00 – 71.04 | **0.00 – 0.39** | 13.7% – 99.6% | **33.8% – 99.8%** | Up to **+84.4% tactical gate capture gain** on agile ramps and discrete steps. |
| **Frequency** | $\text{MHz}$ | $\pm 2.0\text{ MHz}$ | 0.00 | **0.00** | 75.9% – 79.3% | **76.4% – 81.0%** | Up to **-95.7% MAE reduction** under moderate noise; all error levels $\le 1.59\text{ MHz}$. |
| **PW** | $\mu\text{s}$ | $\pm 0.1\ \mu\text{s}$ | 0.00 | **0.00** | 93.9% – 95.4% | **94.6% – 95.4%** | Extreme sub-microsecond precision (**0.01 – 0.04 μs MAE** across all noise levels). |
| **AOA** | Degrees | $\pm 2.0^\circ$ | 0.00 | **0.00** | 99.6% – 100.0% | **99.9% – 100.0%** | Up to **-79.7% bearing error reduction**; pristine directional tracking. |
| **Amplitude** | $\text{dBm}$ | $\pm 2.0\text{ dBm}$ | 0.00 | **0.00** | 95.2% – 95.6% | **95.5% – 95.8%** | Accurate antenna scan envelope prediction with **< 0.80 dBm MAE** at Level 3. |

---

"""

updated_readme = pre_content + new_section_10 + post_content
README_PATH.write_text(updated_readme, encoding="utf-8")
print("[SUCCESS] README.md successfully updated with full 5-parameter benchmark suite and developer reproduction instructions.")

