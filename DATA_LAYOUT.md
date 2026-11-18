# Complex PRI data and result names

**`new_complex_pri` is the current dataset protocol.** `old_complex_pri` is the
previous observed-future experiment. Their names identify different targets;
a later timestamp alone does not identify the protocol.

| Family | Local dataset | Target definition |
|---|---|---|
| `new_complex_pri` | `datasets/new_complex_pri/production/C1024_H32/single_radar` | 1024 observed context intervals followed by 32 consecutive source pulses; context losses retained |
| `old_complex_pri` | `datasets/old_complex_pri/single_radar` | 1024 observed intervals in total; losses may occur in the forecast horizon |

Both production collections cover fixed/varying profiles, eight radar types,
eight error levels, and 1000 sequences per combination with 700/100/200 splits.
Dataset CSVs remain local and Git-ignored. The new production collection was
generated completely; its full validator was interrupted before the final
report, so it is not described as fully audited.

## Artifact locations and Git scope

| Artifact | Current data | Previous data |
|---|---|---|
| Dataset galleries | [new_complex_pri](results/dataset_gallery/new_complex_pri/README.md) | [old_complex_pri](results/dataset_gallery/old_complex_pri/README.md) (previously published) |
| Chronos-2 zero-shot | [new_complex_pri](results/chronos2/zero_shot/new_complex_pri/README.md) | `results/chronos2/zero_shot/old_complex_pri/` (local) |
| MAE comparison tables and plots | [new_complex_pri](outputs/new_complex_pri/README.md) | `outputs/old_complex_pri/` (local) |

Raw dataset CSVs remain local and Git-ignored. Current `new_complex_pri` galleries,
Chronos-2 experiment results, MAE tables and comparison plots are published.
Development smoke outputs, validation reports, migration audit records and
publication previews remain local. Historical experiment results remain local.
The historical gallery retains its original published image contents.

PNG filenames also carry the family name. A forecast file such as
`new_complex_pri_stagger_error_lv2.png` therefore remains identifiable when
downloaded separately. Task, L and profile remain in the parent directory.

Run names retain their creation time: `run_20261118_151924` means 18 November 2026
at 15:19:24 in the shell's local time. The runner's automatic UTC names explicitly
end in `_UTC`. These IDs separate repeated experiments within the same family.

## Re-run commands and defaults

- Generate current data with `--protocol new_complex_pri`. The default root is
  `datasets/new_complex_pri/production/C1024_H32`, or its `smoke` counterpart
  with `--smoke-test`. A nonempty root is rejected.
- `--protocol consecutive_future_v2` remains a compatibility alias. Existing
  metadata keeps the versioned schema ID `consecutive_future_v2`; renaming a
  directory does not change the stored row format.
- The historical `--protocol observed` path defaults to `datasets/old_complex_pri`.
- Chronos zero-shot `--window-mode boundary` writes under
  `results/chronos2/zero_shot/new_complex_pri/<run>`. Historical window modes
  write under `.../old_complex_pri/<run>`.
- The dataset gallery defaults to `results/dataset_gallery/<family>` and rejects
  a nonempty output directory. Use an explicit fresh output for repeated galleries.
- `python -m foundation_models.chronos2.compare_context_mae --source <run>`
  writes tables under `outputs/<family>/mae_comparison/<run-name>` and refuses
  to overwrite an existing report.

Detailed generation and evaluation instructions are in
[the current protocol guide](dataset_generator/CONSECUTIVE_FUTURE.md).

## Name migration and provenance

The original production root `complex_pri_full_20261117_230416` was renamed to
`old_complex_pri`; `consecutive_future_v2` was renamed to `new_complex_pri`.
Matching result roots, galleries, table directories and recorded paths were
updated together. Dataset PDW CSVs, numeric metric CSVs, saved forecast arrays
and recorded original code fingerprints were preserved. Completed experiments
retain their original run IDs and have a `name_migration.json` record.

Code changed after those completed experiments. Strict resume fingerprint checks
remain enabled; the migration does not pretend that the completed runs used the
new reporting code. Use a fresh run directory when running the updated code.

Historical development smoke roots outside these production families and the
separate TimesFM branch audit remain historical development artifacts. They are
not the current production dataset.
