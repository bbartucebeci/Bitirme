# PRI Benchmark Datasets

This folder contains generated synthetic radar pulse datasets.

Each dataset is stored in its own subfolder. For example:

```text
datasets/
  single_stable_1000x128_clean/
  single_stable_1000x128_error_lv1/
  single_stable_1000x128_error_lv2/
  single_stable_1000x128_error_lv3/
```

Each dataset folder follows the same structure:

```text
dataset_name/
  metadata.yaml
  train/
    sequences.csv
    seq_XXXX.csv
  val/
    sequences.csv
    seq_XXXX.csv
  test/
    sequences.csv
    seq_XXXX.csv
```

## Dataset Naming

Dataset names follow this pattern:

```text
single_<radar_type>_<sequence_count>x<expected_pulses_per_sequence>_<error_level>
```

Example:

```text
single_stable_1000x128_error_lv1
```

This means:
- one radar type: stable
- 1000 independent sequences
- 128 expected transmitted pulses per sequence
- error level 1

## Error Levels

The error level describes how nonideal the generated radar observations are.

Current levels:

| Level | Meaning |
|---|---|
| `clean` | Ideal baseline with no missing pulses, no false pulses, and no measurement noise |
| `error_lv1` | Very close to ideal; tiny measurement noise and very small missing/false pulse effects |
| `error_lv2` | Mild nonideal case; visible but still moderate noise and pulse errors |
| `error_lv3` | Stronger nonideal case; more missing pulses, false pulses, multipath, and measurement noise |

The exact parameters for each dataset are saved in:

```text
metadata.yaml
```

Important fields in `metadata.yaml`:
- `error_level`
- `error_parameters`
- `radar_parameters`
- `environment_parameters`
- `split`

## Train, Validation, and Test Splits

Each dataset is split into:

```text
train/
val/
test/
```

For the 1000-sequence datasets:

| Split | Number of sequences |
|---|---:|
| train | 700 |
| val | 100 |
| test | 200 |

The split is done by `sequence_id`, not by individual rows. This prevents leakage between train, validation, and test data.

Leakage means the model accidentally sees part of the same sequence during training and testing, which makes evaluation unfair.

## Combined CSV Files

Each split contains a combined CSV file:

```text
train/sequences.csv
val/sequences.csv
test/sequences.csv
```

These files contain all sequences for that split.

Example:

```python
import pandas as pd

dataset_path = "datasets/single_stable_1000x128_error_lv1"

train_df = pd.read_csv(f"{dataset_path}/train/sequences.csv")
val_df = pd.read_csv(f"{dataset_path}/val/sequences.csv")
test_df = pd.read_csv(f"{dataset_path}/test/sequences.csv")
```

## Individual Sequence CSV Files

Each split folder also contains one CSV file per sequence:

```text
train/seq_0000.csv
train/seq_0001.csv
...
```

To read one sequence:

```python
seq_df = pd.read_csv("datasets/single_stable_1000x128_error_lv1/train/seq_0000.csv")
```

## How To Iterate Over Sequences

Rows with the same `sequence_id` belong to one independent pulse sequence.

Use `groupby("sequence_id")` when reading from a combined CSV:

```python
for sequence_id, seq_df in train_df.groupby("sequence_id"):
    seq_df = seq_df.sort_values("pulse_index")

    toa = seq_df["TOA"].to_numpy()
    pri = seq_df["PRI"].to_numpy()
    freq = seq_df["Frequency"].to_numpy()
    pw = seq_df["PW"].to_numpy()
    amp = seq_df["Amplitude"].to_numpy()
    aoa = seq_df["AOA"].to_numpy()

    # Use this sequence in your model or algorithm
```

Do not concatenate different `sequence_id` values as one continuous radar signal.

Each `sequence_id` is an independent radar pulse train.

## Important Note About Error Datasets

For clean datasets, each sequence usually has exactly the expected number of pulses.

For error datasets, the observed number of rows in a sequence may be different because:
- missing pulses remove genuine radar pulses
- false/noise pulses add extra observations
- multipath can add echo pulses

So `1000x128` means:

```text
1000 sequences, 128 expected transmitted pulses per sequence
```

It does not always mean every saved sequence has exactly 128 observed rows.

## Recommended Usage

For model development:

```python
train_df = pd.read_csv(f"{dataset_path}/train/sequences.csv")
val_df = pd.read_csv(f"{dataset_path}/val/sequences.csv")
test_df = pd.read_csv(f"{dataset_path}/test/sequences.csv")
```

Use:
- `train` for fitting or learning
- `val` for tuning parameters
- `test` only for final evaluation

For classical algorithms, you can use the same splits for fair comparison.
