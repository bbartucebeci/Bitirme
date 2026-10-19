# PRI Benchmark Datasets

Synthetic pulse sequences for stable, Gaussian-jitter, and stagger radars.

## New layout

After running the updated generators, datasets are organized as:

    datasets/
      single_stable/
        clean/
        error_lv1/
        error_lv2/
        error_lv3/
      single_jitter/
        clean/
        error_lv1/
        error_lv2/
        error_lv3/
      single_stagger/
        clean/
        error_lv1/
        error_lv2/
        error_lv3/

Each error-level folder contains metadata.yaml and three split folders:
train, val, and test. Each split has a combined sequences.csv and
individual seq_XXXX.csv files.

## Older datasets

Datasets generated before this layout remain in flat folders such as
single_stable_1000x128_error_lv1 and
single_jitter_1000x128_clean. The older single_stable_1000x128
folder may also be present. These folders are not moved or deleted
by the new generators. Read them using their existing paths.

## Sequences and splits

Each error level has 1000 independent sequences: 700 train,
100 validation, and 200 test. Splitting is by sequence_id, so
pulses from one sequence cannot appear in multiple splits.

The 1000x128 designation means 1000 sequences generated over a
duration of 128 mean-PRI intervals. The observed row count can vary,
including in clean jitter or stagger data. Missing pulses reduce the
row count; false pulses and multipath echoes can increase it.

Do not concatenate different sequence_id values as one continuous
radar signal. Sort each sequence by pulse_index before using it.

## Error levels

clean has no added observation errors. The jitter radar still has
intrinsic Gaussian PRI variation, and the stagger radar still has
its repeating PRI pattern. error_lv1, error_lv2, and error_lv3
introduce increasing nonideal effects. See each metadata.yaml for
the exact radar and environment parameters.

## Reading a dataset

From the repository root:

    from pathlib import Path
    import pandas as pd

    dataset = Path("datasets/single_stagger/error_lv1")
    train = pd.read_csv(dataset / "train/sequences.csv")
    val = pd.read_csv(dataset / "val/sequences.csv")
    test = pd.read_csv(dataset / "test/sequences.csv")

    for sequence_id, sequence in train.groupby("sequence_id"):
        sequence = sequence.sort_values("pulse_index")
        # Process this sequence independently.

For an older flat dataset, change only the dataset path, for example:

    dataset = Path("datasets/single_stagger_1000x128_error_lv1")

The PRI column describes the generated pulse's source PRI.
Measured_Delta_TOA is the difference between adjacent observed TOAs;
missing, false, and echo pulses can affect that observed difference.
