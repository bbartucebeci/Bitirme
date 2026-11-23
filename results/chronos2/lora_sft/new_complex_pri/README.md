# new_complex_pri: Chronos-2 LoRA SFT

Completed run: [run_20261119_184059](run_20261119_184059/report.md).
24 independently fitted adapters: two profiles x three tasks x four context
lengths. Each adapter pools all eight radar types and eight error levels.

Evaluation covers fixed/varying, L=96/256/512/992, H=32, 200 test sequences per
condition: **1,536 condition rows and 307,200 sequence forecasts**. Every L uses
the same consecutive, loss-free horizon within a given sequence. PRI context
uses measured Delta-TOA and the target uses source PRI; Frequency retains the
measured-frequency definition. Joint input/training uses five channels, while
reported joint metrics cover PRI and Frequency.

- [Final metrics](run_20261119_184059/metrics.csv)
- [Run configuration](run_20261119_184059/run_config.json)
- [SFT MAE tables and workbook](../../../../outputs/new_complex_pri/lora_sft/mae_comparison/run_20261119_184059/MAE_comparison.md)
- [Fixed/varying and uni/multivariate plots](../../../../outputs/new_complex_pri/lora_sft/comparisons/run_20261119_184059/README.md)
- [Zero-shot versus SFT comparison plots](../../../../outputs/new_complex_pri/sft_vs_zero_shot/run_20261119_184059/README.md)
- [Example seq_0800: multivariate, varying, stagger, L=992, error_lv2](run_20261119_184059/multivariate/L992/varying/plots/new_complex_pri_stagger_error_lv2.png)

The final run contains 1,536 example prediction PNGs under
`<task>/L<length>/<profile>/plots/`, alongside condition and per-sequence metrics.
Test hashes/window indices and the zero-shot reference fingerprints are retained
for provenance. CSVs here are **experiment metrics**, not raw radar datasets.
Weights, training audits, smoke outputs, validation files, example JSON dumps
and internal per-condition completion markers are excluded from publication.

The source RNG depends on error level, so error levels are independent source
realizations. SFT versus zero-shot comparisons use identical test data/windows;
they do not imply matched corruptions across error levels. Base model ID is the
same (`amazon/chronos-2`); the original zero-shot runtime did not record a concrete
model revision. See [the protocol guide](../../../../foundation_models/chronos2/SFT_1024.md).
