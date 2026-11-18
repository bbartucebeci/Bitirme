# Chronos-2 zero-shot: complex PRI, 1024 intervals

This document describes the original **observed-future v1** experiment. For
the replacement consecutive-source-future v2 dataset, see
[CONSECUTIVE_FUTURE.md](../../dataset_generator/CONSECUTIVE_FUTURE.md).
Use `--dataset-size 1000x1056 --window-mode boundary` with that dataset; its
1024 context intervals are separate from the 32 future intervals. Existing v1
results and output directories remain historical and must not be resumed as v2.

Run from `long-seq-1024` with the dedicated Chronos environment. The new runner
reuses the existing loader, Chronos adapter, metrics and forecast plotting.
It never calls a trainer or reads train/validation CSVs. Dataset generation,
fine-tuning and existing experiment entry points are unchanged.

## Experiment protocol

- Profiles: fixed and varying.
- Radar types: stable, jitter, stagger, dwell_and_switch, sliding, sinusoidal,
  triangular_sliding, markov_agile.
- Levels: clean and error_lv1 through error_lv7.
- Tasks: PRI univariate, Frequency univariate, multivariate.
- Context lengths: 96, 256, 512, 992. Horizon: 32.
- Every condition uses all 200 test sequences from its `1000x1024` dataset.
  There is one forecast window per sequence, with no concatenation or padding.
- Default `tail` windows predict the same final 32 observed pulse positions
  across all four context lengths. Starts after anchor removal are 896, 736,
  480 and 0 respectively. The last 40 context points are shown in the plots.
- As in the existing benchmark, PRI context is `Measured_Delta_TOA` and PRI
  target is source `PRI` at the retained events. Frequency uses measured
  `Frequency` for both context and target. No missing-pulse correction is added.
- Multivariate input order is PRI, Frequency, PW, AOA, Amplitude. Chronos predicts
  all five channels jointly; the requested scores and two-panel plots cover
  PRI and Frequency only. No future covariates or cross-sequence learning are
  supplied. Predictions use the adapter's median point forecast.
- MAE, RMSE and gate hit rate use the repository's emitter mask and per-sequence
  aggregation. Gates remain ±10 µs for PRI and ±2 MHz for Frequency. Existing
  metric helper rounding is retained. Results remain separated by radar type,
  profile, error level, context length and task; no cross-radar average is made.

The full matrix has **1536 condition rows and 307200 sequence forecasts**
(128 datasets × 4 context lengths × 3 tasks × 200 test sequences).
These are forecasts of 32 positions each, not 307200 generated datasets.

## Run the complete experiment

No installation is required in the existing `bitirme-chronos2-venv` environment.
The base model is `amazon/chronos-2`; Hugging Face can use its local cache.
Set `--model-id` to a local base-model snapshot for an explicitly offline run.
Do not pass a fine-tuned adapter as the model.

```powershell
Set-Location -LiteralPath 'C:\Users\User\Desktop\DÇ'
if ((git branch --show-current).Trim() -ne 'long-seq-1024') {
    throw 'Aktif branch long-seq-1024 olmalı.'
}

$chronosDataRoot = Join-Path (Get-Location) 'datasets\complex_pri_full_20261117_230416\single_radar'
$chronosOutput = Join-Path (Get-Location) ("results\chronos2\zero_shot\complex_pri_1024\run_" + (Get-Date -Format 'yyyyMMdd_HHmmss'))

& "$env:USERPROFILE\bitirme-chronos2-venv\Scripts\python.exe" -B `
    -m foundation_models.chronos2.run_zero_shot `
    --datasets-root $chronosDataRoot `
    --dataset-size 1000x1024 `
    --profiles fixed varying `
    --tasks PRI Frequency multivariate `
    --context-lens 96 256 512 992 `
    --horizon 32 `
    --window-mode tail `
    --batch-size 16 `
    --device cuda `
    --output-dir $chronosOutput

if ($LASTEXITCODE -ne 0) { throw 'Deney tamamlanamadı; son hata mesajını incele.' }
Write-Host "Rapor: $chronosOutput\report.md"
```

All eight radar types and eight error levels are defaults. To restrict a smoke
run, use `--radar-types stagger markov_agile --error-levels error_lv7
--max-test-seqs 2`. Omit `--max-test-seqs` for the full test split.
`--plot-sequence-id seq_0800` selects the same test sequence ID for each
condition (also the default first test sequence in the current full dataset).
In varying mode the ID refers to each condition's own sampled radar profile;
matching IDs across error levels do not imply paired corruption realizations.

## Preflight, progress and restart

Before loading Chronos, the runner checks every requested dataset's metadata,
test-file count and interval length. It records CSV/metadata SHA-256 hashes,
window starts and example IDs. It fails on incomplete datasets instead of
silently excluding a condition. This is an experiment input check; use
`dataset_generator.validate_datasets` for the full synthesis-parameter audit.

`--coverage-only` performs this preflight without model inference. If you use
it with the intended output directory, add `--resume` when starting inference
there. A fresh run otherwise requires an empty output directory.

The terminal prints `[PREFLIGHT]`, `[BATCH]` and `[PROGRESS]` messages. Completed
conditions have a marker written after their metrics, example and PNG. To
resume, repeat the original command with the **same output directory** and
`--resume`; do not generate a new timestamp. Input hashes, protocol settings
and relevant source-code fingerprints must match. A partially completed
condition is rerun; completed ones are reused. Batch size and device may change
on resume, e.g. lower `--batch-size` if GPU memory is insufficient. Chronos counts
variates within its internal batching, so this option is not a promise of 16
five-channel sequences in a single GPU batch.

`random` and `first` window modes are optional. Random starts are deterministic
and saved in the manifest, but are drawn separately per context length; only
`tail` guarantees matching target positions across all lengths.

## Outputs

```text
<output>/
  run_config.json                # protocol and source-code fingerprint
  runtime.json                   # environment, actual device, model revision
  coverage.csv                   # 128 rows for the full dataset selection
  test_windows.json              # input hashes, exact windows, example IDs
  metrics.csv                    # 1536 condition rows for a complete run
  report.md                      # protocol and links to condition reports
  PRI|Frequency|multivariate/
    L96|L256|L512|L992/
      fixed|varying/
        metrics.csv             # 64 conditions per task/length/profile
        report.md
        per_sequence/<radar>_<level>.csv
        examples/<radar>_<level>.json
        plots/<radar>_<level>.png
        completed/<radar>_<level>.json
  by_radar/<task>/<radar>/metrics.csv
  by_radar/<task>/<radar>/report.md
```

Full runs produce 1536 example PNGs and 1536 per-sequence metric CSVs.
Example JSONs preserve the actual context, target, forecast, emitter mask and
start index; multivariate JSONs preserve all five model outputs. Inference time
includes prediction and CPU conversion, excludes CSV loading and plotting,
and per-sequence timing is batch-amortized. The run is not a latency benchmark.

Root metrics are refreshed after each condition. Markdown reports are refreshed
after each task/context group. Input datasets and prior experiment outputs
are never modified. No commit or push is performed by the runner.

## Verification during implementation

`test_zero_shot.py` checks target alignment across contexts, observed PRI versus
source PRI, five-channel inputs, PRI/RF-only outputs, random manifests, report
grouping, missing files, input-change rejection and coverage-only resume.

The dedicated environment passed 27 tests across the generator, gallery,
existing window loader and new experiment runner. An offline CUDA integration
using cached base model revision `29ec3766d36d6f73f0696f85560a422f50e8498c`
completed all 48 selected conditions: fixed/varying × stagger/markov_agile ×
error_lv7 × four contexts × three tasks, one test sequence each. Reports,
example JSONs and PNGs were generated; a second invocation verified resume.
These are smoke results, not the full 200-sequence benchmark.

The full default preflight also passed against
`datasets/complex_pri_full_20261117_230416/single_radar`: 128 datasets,
200 test sequences each, 25600 selected sequences. The full inference matrix
was not started. Smoke artifacts are under the ignored local directory
`datasets/chronos2_zero_shot_integration_20261118`; the coverage manifest is
under `datasets/chronos2_zero_shot_coverage_20261118`.
