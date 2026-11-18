# new_complex_pri: consecutive-source future protocol

`new_complex_pri` is the public data/output family name. The stored schema ID
remains `consecutive_future_v2` for file-format compatibility. See
[DATA_LAYOUT.md](../DATA_LAYOUT.md) for the previous `old_complex_pri` collection
and the canonical result/table locations.

The active replacement protocol uses 1024 **observed context intervals** and
up to 32 consecutive transmitted future pulses. PRI laws, clock functions,
profile distributions, noise levels, POI/global probabilities and radar types
are unchanged. False pulses, echoes and mode switching remain disabled.

## Storage: one authoritative CSV per sequence

The generator writes `train|val|test/seq_NNNN.csv` incrementally. It no longer
accumulates all sequence DataFrames in RAM or writes a second `sequences.csv`,
including when explicitly generating the older observed-future protocol.
Historical combined files remain readable through legacy fallbacks; validators
compare them when present on historical datasets. No new path requires them.

For v2, the sequence CSV itself contains the complete source PDWs through the
stored horizon. There is **no second trace file or model-facing PDW copy**.
Additional columns are:

| Column | Meaning |
|---|---|
| `source_pulse_id` | Consecutive ID assigned before receiver filtering |
| `poi_keep`, `global_keep` | Independent hypothetical receiver retention masks |
| `observed_keep` | Logical AND of both masks |
| `sequence_index` | Selected model row, or -1 for excluded source rows |
| `pulse_index` | Equals sequence_index; -1 rows are audit-only |
| `segment` | anchor, context, horizon or missed_context |

`dataset_generator.sequence_io.read_sequence_frame` selects rows with nonnegative
sequence indices and verifies their identity/order. All seven PDW fields are
selected together. Masks and source IDs are never model input channels.
`Measured_Delta_TOA` on selected rows is computed between their measured TOAs;
on unselected audit rows it retains the complete-source interval and is not
consumed by the model. The first selected row has zero delta and is the anchor.

The filename tag `1000x1056` means **1000 model sequences with 1056 selected
intervals**, not a fixed number of raw CSV rows. Each projected sequence has
1057 rows including its anchor. Raw CSVs have additional excluded source rows
when context pulses were missed. Their counts are recorded in `generation.csv`.
This preserves the dropped PDWs while avoiding duplicated PDW storage.

## Generation and boundary

1. Generate a complete measured stream through the existing engine with POI=1,
   global drop=0 and source tracking enabled. Keep existing clock, measurement,
   environment and receiver effects. Fail if receiver filtering removes or
   reorders a source ID; do not silently repair a collision.
2. Sample the configured POI/global masks using a dedicated recorded loss seed.
   Sampling all channel values before filtering gives each missing pulse a full
   PDW to restore. These are counterfactual measured values, not noiseless labels.
3. Select the first 1025 retained pulses: anchor plus 1024 context intervals.
4. If the last context source ID is k, select source IDs k+1 through k+32 for
   the future, independently of their masks. Every channel is restored together.
5. Save one CSV, the initialization, source-buffer budget, attempts and loss seed.

The modulation source continues through both segments. It is not restarted at
the boundary. The existing PRI target remains the repo's clock-adjusted source
`PRI`; PRI input remains observed Delta-TOA. Other channels retain their measured
target definitions and configured measurement noise. New realizations are not
claimed to match old dataset bytes because random-number consumption changes.

After anchor removal, C=1024 and any L<=C, H<=stored maximum use:

```python
context = selected_rows[C-L:C]
target = selected_rows[C:C+H]
```

`--window-mode boundary` is required for v2 evaluation. First/random/tail modes
are rejected because they may score a different boundary, especially at smaller H.
L=96/128/256/512/992/1024 therefore share targets; H=16 shares the first 16 targets
of H=32. To compare larger horizons, generate one dataset with a sufficiently
large maximum and slice its future prefixes, rather than regenerate for each H.

## Dataset inventory and separation

| Root | Role |
|---|---|
| `datasets/old_complex_pri` | Previous 1000x1024 production data with losses in the horizon; retained locally as the old protocol |
| `datasets/single_radar` | Older experiment data; not the new benchmark source |
| `datasets/new_complex_pri/smoke/C1024_H32` | New 10-sequence-per-condition smoke collection |
| `datasets/new_complex_pri/production/C1024_H32` | Locally generated 1000-sequence-per-condition production collection |

The generator uses a fresh root for each v2 collection and rejects nonempty
roots, so protocols or partial runs cannot be silently merged. `collection.json`
records purpose, schema, C/H budgets, seed, code hashes, selected conditions and
completion state. Interrupted collections remain `building`; evaluation rejects
them. A complete all-condition collection has 128 combinations. Sequence IDs
remain split 700/100/200 in production and 7/1/2 in smoke runs, for both profiles.

No existing dataset is moved, renamed, deleted or overwritten. `datasets/` remains
Git-ignored. No dataset or result push is part of this implementation.

## Modules using sequence files

- Generator: incremental per-sequence writer, optional v2 assembly and metadata.
- Validator: no combined file required; audits complete source records, loss draws,
  selected IDs, all restored horizon PDWs, splits and model-window alignment.
- Shared foundation-model and classical array readers: project source CSVs through
  the shared reader. Their historical combined-only fallback remains available.
- Shared unified training factories: construct v2 samples using the stored
  boundary while retaining the existing training Dataset/loss contracts.
- Legacy first-window evaluation loaders: reject v2 explicitly. Such entry points
  must use `load_split(..., window_mode='boundary')` before benchmarking v2;
  they continue reading old per-sequence datasets without a combined file.
- Chronos zero-shot runner and manifest builder: support explicit boundary mode,
  include complete input hashes, and write new results under a v2-specific root.
- Gallery: projects selected rows and marks the horizon boundary with a dotted line.

## Commands

From the repository root, with the generator environment:

```powershell
& "$env:USERPROFILE\bitirme-generator-venv\Scripts\python.exe" -B `
    -m dataset_generator.generate_datasets `
    --protocol new_complex_pri --context-intervals 1024 --max-horizon 32 `
    --radar-type all_single --profile-mode both --error-level all `
    --freq-mode constant --smoke-test
```

This uses the default **smoke** root above and refuses to overwrite it. For
repeated smoke runs, provide a fresh explicit `--output-dir`.

With the Chronos environment, validate all source records and loader contracts:

```powershell
& "$env:USERPROFILE\bitirme-chronos2-venv\Scripts\python.exe" -B `
    -m dataset_generator.validate_datasets `
    --datasets-root datasets/new_complex_pri/smoke/C1024_H32/single_radar `
    --dataset-size 10x1056 --check-loaders `
    --report datasets/new_complex_pri/smoke/C1024_H32/validation_report.json
```

For Chronos on the new protocol, explicitly use `--dataset-size 1000x1056`
(or `10x1056` for smoke) and `--window-mode boundary`. The existing L=96/256/512/992
and H=32 configuration remains usable; L=1024 is now possible too. Do not resume
an old-protocol result folder or compare the two protocols as if their targets
were identical. Full production generation and full model evaluation are
separate steps. Production was subsequently generated locally by the user.
Its collection is marked complete; the full production validator was stopped
at the user's request before writing its final report. It must not be
described as fully validated.

## Start the production Chronos zero-shot experiment

Run on `long-seq-1024` with the existing Chronos environment. This command selects
both profiles, all eight radar types and all eight error levels by default.
It uses all 200 test sequences per condition. The tasks are PRI univariate,
Frequency univariate, and five-channel multivariate input scored for PRI/RF.

```powershell
Set-Location -LiteralPath 'C:\Users\User\Desktop\DÇ'
if ((git branch --show-current).Trim() -ne 'long-seq-1024') {
    throw 'Aktif branch long-seq-1024 olmalı.'
}

$chronosDataRoot = Join-Path (Get-Location) 'datasets\new_complex_pri\production\C1024_H32\single_radar'
$chronosOutput = Join-Path (Get-Location) ("results\chronos2\zero_shot\new_complex_pri\run_" + (Get-Date -Format 'yyyyMMdd_HHmmss'))

& "$env:USERPROFILE\bitirme-chronos2-venv\Scripts\python.exe" -u -B `
    -m foundation_models.chronos2.run_zero_shot `
    --datasets-root $chronosDataRoot `
    --dataset-size 1000x1056 `
    --profiles fixed varying `
    --tasks PRI Frequency multivariate `
    --context-lens 96 256 512 992 `
    --horizon 32 `
    --window-mode boundary `
    --plot-sequence-id seq_0800 `
    --batch-size 16 `
    --device cuda `
    --output-dir $chronosOutput

if ($LASTEXITCODE -ne 0) { throw 'Deney tamamlanamadı; son hata mesajını incele.' }
Write-Host "Rapor: $chronosOutput\report.md"
```

This produces 1536 condition rows, 307200 sequence forecasts and 1536 example
PNGs. Results are separated by profile, task, context, radar type and error level.
There is no fine-tuning stage. Test-input preflight does not replace the full
generation audit. To resume an interrupted experiment, reuse the exact output
directory and arguments and add `--resume`; do not create a new timestamp.

## Acceptance checks

- Forced POI and global loss remove an entire known PDW row, including hopping RF.
- The same lost row in the future is selected with all measured fields intact.
- Source IDs prove continuity across the boundary for every radar law, including
  Markov; no receiver-induced source gaps are accepted.
- All L values share targets, all H values share context and target prefixes,
  and the declared budgets are enforced.
- One authoritative CSV per sequence; no combined copy, no second trace copy.
- Source projection masks and source IDs are excluded from the five input channels.
- Legacy observed-future tests and historical combined-file reads still work.
- The full smoke matrix, common loaders and a small real Chronos inference run
  are checked before any production run.
