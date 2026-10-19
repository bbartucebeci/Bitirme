# PRI Benchmark Datasets

Synthetic pulse-sequence datasets for five PRI modulation types:
stable, Gaussian jitter, stagger, dwell-and-switch, and sliding.

## Organization

The current fixed-profile datasets are stored under:

    datasets/single_radar/fixed_profile/single_<radar_type>/
        single_<radar_type>_1000x128_<error_level>/

The varying-profile generators, when run, store their datasets under:

    datasets/single_radar/varying_profile/single_<radar_type>/
        single_<radar_type>_1000x128_<error_level>/

Supported radar types are `stable`, `jitter`, `stagger`,
`dwell_and_switch`, and `sliding`. Each type has `clean`,
`error_lv1`, `error_lv2`, and `error_lv3` datasets.

For example:

    datasets/single_radar/fixed_profile/single_stagger/
        single_stagger_1000x128_error_lv1/

The planned `multi_radar/` datasets are separate from these
single-radar datasets and are not described as available here.

## Files in Each Dataset

    single_<radar_type>_1000x128_<error_level>/
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

Varying-profile datasets also contain `profiles.csv`. It records
the sampled settings, sequence-to-profile mapping, and assigned
split. The `pri_arguments_json` column contains the exact
radar-type-specific PRI parameters for each profile.

`metadata.yaml` records the generator settings, error level,
sampling ranges where applicable, units, file names, and split
counts. In fixed-profile datasets it also records the fixed radar
parameters.

## Fixed and Varying Profiles

A fixed-profile dataset uses the same radar parameters for all
sequences of that radar type. It evaluates new observations of a
known configuration.

A varying-profile dataset samples a new parameter profile for
each sequence. Parameters remain fixed within that sequence.
The five radar types use the same sampled common-parameter
ranges and split assignments. This evaluates new configurations
drawn from the documented ranges, not configurations outside
those ranges.

Each dataset contains 1000 sequences: 700 train, 100 validation,
and 200 test. Splits are by whole sequence; varying-profile
datasets also have disjoint profile IDs across splits. Never
divide individual pulse rows between train and test.

## Sequence Length

`1000x128` means 1000 sequences generated over a duration of
128 mean-PRI intervals per sequence. It does not guarantee
exactly 128 saved rows. Even clean jitter, stagger, dwell-and-
switch, or sliding sequences can have different row counts.
Missing pulses decrease the count; false pulses and multipath
echoes can increase it.

Treat each `sequence_id` as an independent pulse train. Sort by
`pulse_index` and do not concatenate different sequences into
one continuous signal.

## Error Levels

`clean` adds no observation errors, but each radar type retains
its inherent PRI pattern. `error_lv1`, `error_lv2`, and
`error_lv3` add increasing nonideal effects. See the relevant
`metadata.yaml` for the exact POI, global drop rate, noise,
multipath, and other settings.

## Load a Split

Run this example from the repository root:

    from pathlib import Path
    import pandas as pd

    dataset = Path(
        "datasets/single_radar/fixed_profile/single_stagger/"
        "single_stagger_1000x128_error_lv1"
    )

    train = pd.read_csv(dataset / "train" / "sequences.csv")
    val = pd.read_csv(dataset / "val" / "sequences.csv")
    test = pd.read_csv(dataset / "test" / "sequences.csv")

    for sequence_id, sequence in train.groupby("sequence_id"):
        sequence = sequence.sort_values("pulse_index")
        # Process one independent sequence.

For a varying-profile dataset, replace `fixed_profile` with
`varying_profile` in the path. Its sampled settings can be read
with:

    profiles = pd.read_csv(dataset / "profiles.csv")

You can also read any `seq_XXXX.csv` directly from its split
folder. Use the same train, validation, and test splits for
time-series models and classical algorithms for a fair comparison.

## Targets and Labels

`PRI` is the generator's source PRI for that pulse.
`Measured_Delta_TOA` is the difference between adjacent observed
arrival times. Missing, false, and echo pulses can make these
different. Define which quantity your forecasting task predicts.

`profiles.csv` contains ground-truth generating parameters for
analysis, not ordinary predictive inputs. Do not accidentally
feed `radar_type`, `error_level`, `profile_id`, `sequence_id`,
`Radar_ID`, or future target values to a model as features.
