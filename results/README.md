# Experiment results

The current complex PRI dataset is **new_complex_pri**. Historical complex PRI
outputs are labeled **old_complex_pri**. See [the data/result layout](../DATA_LAYOUT.md)
for target definitions and local dataset locations.

| Output | Current | Historical |
|---|---|---|
| Dataset example PNGs | [new_complex_pri](dataset_gallery/new_complex_pri/README.md) | [old_complex_pri](dataset_gallery/old_complex_pri/README.md) (previously published) |
| Chronos-2 zero-shot forecasts and metrics | [new_complex_pri](chronos2/zero_shot/new_complex_pri/README.md) | `chronos2/zero_shot/old_complex_pri/` (local) |
| L=96/256/512/992 MAE tables | [new_complex_pri](../outputs/new_complex_pri/README.md) | `outputs/old_complex_pri/` at repository root (local) |

Current new_complex_pri experiment outputs are published; raw datasets and
development/validation artifacts remain Git-ignored. The historical gallery retains
its previously published image contents under the renamed paths.

Other model families and older branches' results retain their existing names;
they should not be assumed to use the current dataset merely because they are
present in this repository.
