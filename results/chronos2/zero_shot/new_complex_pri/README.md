# new_complex_pri: Chronos-2 zero-shot

Current protocol: 1024 observed context intervals and 32 consecutive source future pulses.

Completed run: [run_20261118_151924](run_20261118_151924/report.md).
The run covers fixed/varying profiles, eight radar types, eight error levels,
L=96/256/512/992 and H=32. Each condition scores 200 test sequences.

- [Overall metrics](run_20261118_151924/metrics.csv)
- [Run configuration](run_20261118_151924/run_config.json)
- [MAE comparisons](../../../../outputs/new_complex_pri/README.md)
- [Example seq_0800 forecast: multivariate, varying, stagger, L=992, error_lv2](run_20261118_151924/multivariate/L992/varying/plots/new_complex_pri_stagger_error_lv2.png)

Forecasts are under `<run>/<task>/L<length>/<profile>/plots/`.
Tasks are PRI univariate, Frequency univariate and five-channel multivariate input.
All prediction PNGs have the `new_complex_pri_` filename prefix. MAE/RMSE and gate hit
rates retain their original definitions. Raw datasets are not stored here.
