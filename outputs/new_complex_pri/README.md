# new_complex_pri: Chronos-2 MAE tables and comparisons

## Completed LoRA SFT results

SFT run: `run_20261119_184059`, evaluated on the same test CSVs and boundary
windows as the zero-shot run below. Both cover 1,536 conditions, 200 sequences
per condition, L=96/256/512/992 and H=32.

- [SFT Excel workbook](lora_sft/mae_comparison/run_20261119_184059/new_complex_pri_chronos2_lora_sft_mae.xlsx)
- [SFT MAE tables across L](lora_sft/mae_comparison/run_20261119_184059/MAE_comparison.md)
- [SFT fixed/varying and uni/multivariate comparisons](lora_sft/comparisons/run_20261119_184059/README.md)
- [SFT versus zero-shot: 32 plots](sft_vs_zero_shot/run_20261119_184059/README.md)
- [SFT final metrics and forecast plots](../../results/chronos2/lora_sft/new_complex_pri/README.md)

## Zero-shot results

Current dataset protocol: 1024 observed context intervals followed by 32
consecutive transmitted future pulses. Context losses remain active.

Run: `run_20261118_151924`. Fixed/varying, eight radar types, eight error levels,
L=96/256/512/992, H=32, 200 test sequences per condition. Univariate PRI/Frequency
and five-channel multivariate input are reported separately.

- [Excel workbook](mae_comparison/run_20261118_151924/new_complex_pri_chronos2_zero_shot_mae.xlsx)
- [All MAE tables](mae_comparison/run_20261118_151924/MAE_comparison.md)
- [Eight table PNGs](mae_comparison/run_20261118_151924/png)
- [Source experiment](../../results/chronos2/zero_shot/new_complex_pri/run_20261118_151924/report.md)

Each table row compares one radar/error condition across context lengths.
Green cells mark the lowest MAE in that row; tied minima are all marked.
These table checks reconcile reported scores; they do not replace a full dataset audit.

## Fixed/varying and univariate/multivariate comparisons

[Open all 32 comparison plots](comparisons/run_20261118_151924/README.md).
Each L=96/256/512/992 has separate PRI and Frequency figures. Eight radar panels
show clean and error_lv1–error_lv7 without averaging radar types together.

- Fixed vs varying holds the input mode constant, with separate univariate and multivariate figures.
- Univariate vs multivariate holds the profile constant, with separate fixed and varying figures.
- Panel y-axes are independent linear MAE scales starting at zero. Lower is better.
- [All numeric comparison pairs](comparisons/run_20261118_151924/comparisons.csv)

To reproduce in a fresh output directory:

```powershell
python -B -m foundation_models.chronos2.plot_mae_comparisons --source results/chronos2/zero_shot/new_complex_pri/run_20261118_151924 --output-dir outputs/new_complex_pri/comparisons/<fresh-run-name>
```
