# new_complex_pri: fixed/varying and univariate/multivariate MAE

Chronos-2 zero-shot, H=32, 200 test sequences per condition. Source run: `run_20261118_151924`.
Each figure belongs to one L and one target. Its eight panels show individual radar types; x-axis categories are clean and error_lv1–error_lv7.
Fixed/varying comparisons hold input mode constant. Univariate/multivariate comparisons hold profile constant.
Multivariate means five input channels, scored here for PRI or Frequency. PRI uses µs; Frequency uses MHz.
Raw MAE definitions and existing per-sequence rounding are retained. Radar types/error levels are not averaged together.
Panel y-axes start at zero and have independent linear scales. Error levels are configured categories, not a monotone missing-rate axis.
The fixed and varying populations have different profile definitions; these are absolute MAE comparisons, not normalized errors or matched per-sequence parameter draws.

## Fixed vs varying

| Target | Held setting | L=96 | L=256 | L=512 | L=992 |
|---|---|---|---|---|---|
| PRI | univariate | [PNG](fixed_vs_varying/L96/new_complex_pri_fixed_vs_varying_pri_univariate_L96.png) | [PNG](fixed_vs_varying/L256/new_complex_pri_fixed_vs_varying_pri_univariate_L256.png) | [PNG](fixed_vs_varying/L512/new_complex_pri_fixed_vs_varying_pri_univariate_L512.png) | [PNG](fixed_vs_varying/L992/new_complex_pri_fixed_vs_varying_pri_univariate_L992.png) |
| PRI | multivariate | [PNG](fixed_vs_varying/L96/new_complex_pri_fixed_vs_varying_pri_multivariate_L96.png) | [PNG](fixed_vs_varying/L256/new_complex_pri_fixed_vs_varying_pri_multivariate_L256.png) | [PNG](fixed_vs_varying/L512/new_complex_pri_fixed_vs_varying_pri_multivariate_L512.png) | [PNG](fixed_vs_varying/L992/new_complex_pri_fixed_vs_varying_pri_multivariate_L992.png) |
| Frequency | univariate | [PNG](fixed_vs_varying/L96/new_complex_pri_fixed_vs_varying_frequency_univariate_L96.png) | [PNG](fixed_vs_varying/L256/new_complex_pri_fixed_vs_varying_frequency_univariate_L256.png) | [PNG](fixed_vs_varying/L512/new_complex_pri_fixed_vs_varying_frequency_univariate_L512.png) | [PNG](fixed_vs_varying/L992/new_complex_pri_fixed_vs_varying_frequency_univariate_L992.png) |
| Frequency | multivariate | [PNG](fixed_vs_varying/L96/new_complex_pri_fixed_vs_varying_frequency_multivariate_L96.png) | [PNG](fixed_vs_varying/L256/new_complex_pri_fixed_vs_varying_frequency_multivariate_L256.png) | [PNG](fixed_vs_varying/L512/new_complex_pri_fixed_vs_varying_frequency_multivariate_L512.png) | [PNG](fixed_vs_varying/L992/new_complex_pri_fixed_vs_varying_frequency_multivariate_L992.png) |

## Univariate vs multivariate

| Target | Held setting | L=96 | L=256 | L=512 | L=992 |
|---|---|---|---|---|---|
| PRI | fixed | [PNG](univariate_vs_multivariate/L96/new_complex_pri_univariate_vs_multivariate_pri_fixed_L96.png) | [PNG](univariate_vs_multivariate/L256/new_complex_pri_univariate_vs_multivariate_pri_fixed_L256.png) | [PNG](univariate_vs_multivariate/L512/new_complex_pri_univariate_vs_multivariate_pri_fixed_L512.png) | [PNG](univariate_vs_multivariate/L992/new_complex_pri_univariate_vs_multivariate_pri_fixed_L992.png) |
| PRI | varying | [PNG](univariate_vs_multivariate/L96/new_complex_pri_univariate_vs_multivariate_pri_varying_L96.png) | [PNG](univariate_vs_multivariate/L256/new_complex_pri_univariate_vs_multivariate_pri_varying_L256.png) | [PNG](univariate_vs_multivariate/L512/new_complex_pri_univariate_vs_multivariate_pri_varying_L512.png) | [PNG](univariate_vs_multivariate/L992/new_complex_pri_univariate_vs_multivariate_pri_varying_L992.png) |
| Frequency | fixed | [PNG](univariate_vs_multivariate/L96/new_complex_pri_univariate_vs_multivariate_frequency_fixed_L96.png) | [PNG](univariate_vs_multivariate/L256/new_complex_pri_univariate_vs_multivariate_frequency_fixed_L256.png) | [PNG](univariate_vs_multivariate/L512/new_complex_pri_univariate_vs_multivariate_frequency_fixed_L512.png) | [PNG](univariate_vs_multivariate/L992/new_complex_pri_univariate_vs_multivariate_frequency_fixed_L992.png) |
| Frequency | varying | [PNG](univariate_vs_multivariate/L96/new_complex_pri_univariate_vs_multivariate_frequency_varying_L96.png) | [PNG](univariate_vs_multivariate/L256/new_complex_pri_univariate_vs_multivariate_frequency_varying_L256.png) | [PNG](univariate_vs_multivariate/L512/new_complex_pri_univariate_vs_multivariate_frequency_varying_L512.png) | [PNG](univariate_vs_multivariate/L992/new_complex_pri_univariate_vs_multivariate_frequency_varying_L992.png) |

[Source experiment](../../../../results/chronos2/zero_shot/new_complex_pri/run_20261118_151924/report.md) · [All numeric comparisons](comparisons.csv)

CSV delta_right_minus_left is Varying−Fixed or Multivariate−Univariate. Negative means the right-hand series has lower MAE; it is not a percentage.
