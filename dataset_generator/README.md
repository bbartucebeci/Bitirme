# Complex PRI single-radar benchmark

This benchmark has eight source laws (`stable`, `jitter`, `stagger`,
`dwell_and_switch`, `sliding`, `sinusoidal`, `triangular_sliding`, `markov_agile`),
two profile modes, and eight error levels (`clean`, `error_lv1`–`error_lv7`).
The approved numerical definitions are in `configs/radar_profiles.yaml` and
`configs/error_levels.yaml`. Fixed RF is constant 9000 MHz; varying RF is sampled
once per profile and remains constant before measurement noise.

Stagger has 32 fixed levels (16–32 varying), with no added source PRI jitter.
Fixed levels are L[j] = 750 + 500j/31 µs, with the existing permutation retained.
Varying uses the existing equally spaced construction μ(1±s), but with
s ~ Uniform(0.24,0.30). Sorted source-level separation must be strictly >10 µs:
16.129 µs fixed, at least 12.387 µs varying for μ≥800 and K≤32.
This requirement applies before clock/noise; it does not assert that ±10 µs
evaluation corridors are disjoint.
D&S has five ordered levels and equal dwell lengths: 32 fixed, choice of 32/48/64
varying. Triangular sliding is separate from the existing sliding ramp; its cycle
has 10 rising and 10 falling transitions without duplicate turning points.
Markov PRI has four states A–D. Fixed levels are 850/950/1050/1150 µs;
varying levels are μ × [1−s, 1−s/3, 1+s/3, 1+s] with s uniform in [0.12,0.18].
Each row of the explicit transition matrix has probability 0.70 for the next
cyclic state (A→B→C→D→A) and 0.10 for each other state, including the current
state. The initial state is uniform. The matrix is doubly stochastic, so the
stationary expected PRI is 1000 µs (fixed) or μ (varying). Its finite capture mean
is not forced.
Sinusoidal PRI uses fixed N=7.2391, or N sampled uniformly in [6.5,9.5], rejecting
exact discrete periods <=1024. All periodic types start at random source phase.

Existing clock settings/functions, receiver filters, masking/target definitions,
and the pooled fine-tuning strategy are retained. The three new source classes
use the base `Radar` clock defaults (zero); no new oscillator parameters are
invented. There is no mode switching. The interleaved scenario is not expanded.
Its existing radar constructor calls retain zero pattern phase by default.

POI and global drop are independent stages. False pulse rate and multipath are
zero at every new level. In Level 7, POI=0.75 and global drop=0.005 give nominal
combined loss 25.375%. Source patterns advance even when pulses are missed.
Losses are Bernoulli draws, not quotas imposed on each sequence.

## Output and reproducibility

The generator defaults to the separate `datasets/complex_pri_v1` output root.
Nonempty single-radar destinations are rejected before CLI generation starts.
Use `--radar-type all_single` for this benchmark, not the interleaved `all` mode.
Generation keeps the existing seed 20261020 and the CRC32 per-sequence seed key.
Each error level uses the same varying profiles; source realizations and masks
are not paired across error levels because the pulse seed includes the level.

Each capture contains 1024 observed intervals and one anchor row (1025 rows).
The saved `PRI` is source PRI at retained events; `Measured_Delta_TOA` is observed
spacing. Complete source cycles have the specified mean, but partial/noisy
captures need not average to that mean. Do not normalize them after generation.
The first/remaining 70/10/20 percent of sequence IDs form train/validation/test.
For 1000 sequences this is 700/100/200; smoke tests use 7/1/2.

Each split retains both per-sequence CSVs and combined `sequences.csv`.
`profiles.csv` records varying source definitions. `generation.csv` records each
sequence seed and actual initialization (phase or Markov initial state/source
seed). `metadata.yaml` records the effective RF mode, seed, profile definition,
and SHA256 of the canonical JSON profile configuration. PDW columns are unchanged.

## Smoke checks only

From the repository root, with the generator environment:

```powershell
python -B -m unittest dataset_generator.test_complex_pri -v
python -B -m dataset_generator.generate_datasets --radar-type all_single --profile-mode both --error-level all --pulses-per-sequence 1024 --freq-mode constant --smoke-test --output-dir datasets/complex_pri_v1_smoke
python -B -m dataset_generator.validate_datasets --datasets-root datasets/complex_pri_v1_smoke/single_radar --dataset-size 10x1024 --report datasets/complex_pri_v1_smoke_validation.json
```

Use a fresh output directory for a repeated smoke run. The above generates only
10 sequences per condition: 128 datasets, 1280 captures. Full production is a
separate operation and is not part of the smoke workflow.

With the Chronos/PyTorch environment (no model weights are loaded):

```powershell
python -B -m foundation_models.chronos2.make_window_manifest --datasets-root datasets/complex_pri_v1_smoke/single_radar --dataset-size 10x1024 --output datasets/complex_pri_v1_smoke/windows_random.json
python -B -m dataset_generator.validate_datasets --datasets-root datasets/complex_pri_v1_smoke/single_radar --dataset-size 10x1024 --check-loaders --window-manifest datasets/complex_pri_v1_smoke/windows_random.json --report datasets/complex_pri_v1_smoke_validation.json
python -B -m unittest foundation_models.chronos2.test_windows -v
```

The validator checks every CSV, split membership and combined CSV equality;
model/classical random windows are compared after the existing float32 model
conversion. All four context lengths also share the last 32 targets in tail mode.
No model training, model download or benchmark-wide inference is needed.

Training/evaluation entry points accept `--datasets-root` (the directory containing
`fixed/` and `varying/`) and `--dataset-size`. Select both explicitly for new data.
TimesFM's unified loaders still pool all selected radar/error conditions. Losses,
weights, cleaning and model algorithms are unchanged. Results for custom roots
are kept in separate namespaces. Classical context sweeps accept the same root
and a fresh window manifest. Their resumable output directory must also be fresh.
`summarize_context_sweep.py` now defaults to separate reports/plots under
`by_radar/<type>/`; error levels are not averaged. `--legacy-overview` is only
for the old five-law experiment.

## Sequence galleries

The plotter supports all eight radar types/error levels and 1024 intervals. It
creates one figure per radar/profile/channel, with all selected error levels in
separate panels (80 PNGs for the complete matrix). The same test sequence ID is
selected in every condition, defaulting to the first test ID in metadata. Anchor
rows are excluded at every capture length. Optional `--channels`, `--pulses` and
`--start` arguments allow a subset or a closer look at a window.

```powershell
python -B -m dataset_generator.plot_sequence_gallery --datasets-root <production-root>/single_radar --dataset-size 1000x1024 --first-test-id 800 --pulses 1024 --output-dir <new-gallery-directory>
```

All selected inputs are checked before output is created. CSVs are only read;
the plotter does not invoke generation and refuses a nonempty output directory.
The published production gallery is [here](../results/dataset_gallery/complex_pri_1024/README.md).
