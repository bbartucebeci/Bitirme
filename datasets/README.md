# Datasets

This folder contains synthetic radar pulse datasets.

# Datasets

This folder contains generated PRI benchmark datasets.

## Folder Structure

Each dataset follows the same structure:

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




## How To Read The Dataset

```python
import pandas as pd

train_df = pd.read_csv("datasets/single_stable_1000x128/train/sequences.csv")
val_df = pd.read_csv("datasets/single_stable_1000x128/val/sequences.csv")
test_df = pd.read_csv("datasets/single_stable_1000x128/test/sequences.csv")
```

## How To Read One Sequence

```python
seq_df = pd.read_csv("datasets/single_stable_1000x128/train/seq_0000.csv")
```

## Important

Rows with the same `sequence_id` belong to one pulse sequence.

Do not concatenate different `sequence_id` values as one continuous radar signal.
Each `sequence_id` is an independent radar pulse train.
