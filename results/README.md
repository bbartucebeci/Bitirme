# Experiment results

The current complex PRI dataset is **new_complex_pri**. Historical complex PRI
outputs are labeled **old_complex_pri**. See [the data/result layout](../DATA_LAYOUT.md)
for target definitions and local dataset locations.

| Output | Current | Historical |
|---|---|---|
| Dataset example PNGs | [new_complex_pri](dataset_gallery/new_complex_pri/README.md) | [old_complex_pri](dataset_gallery/old_complex_pri/README.md) (previously published) |
| Chronos-2 zero-shot forecasts and metrics | [new_complex_pri](chronos2/zero_shot/new_complex_pri/README.md) | `chronos2/zero_shot/old_complex_pri/` (local) |
| Chronos-2 LoRA SFT forecasts and metrics | [new_complex_pri SFT](chronos2/lora_sft/new_complex_pri/README.md) | - |
| Chronos-2 SFT versus zero-shot MAE | [32 comparison plots](../outputs/new_complex_pri/sft_vs_zero_shot/run_20261119_184059/README.md) | - |
| L=96/256/512/992 MAE tables | [new_complex_pri](../outputs/new_complex_pri/README.md) | `outputs/old_complex_pri/` at repository root (local) |

Current new_complex_pri experiment outputs are published; raw datasets and
development/validation artifacts remain Git-ignored. The historical gallery retains
its previously published image contents under the renamed paths.

Other model families and older branches' results retain their existing names;
they should not be assumed to use the current dataset merely because they are
present in this repository.
