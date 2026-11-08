# TiRex-2 PW zero-shot benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.
The point forecast is TiRex-2's 0.5 quantile (median).

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.00797  | 0.00994  |       100      |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.024435 | 0.030585 |        99.8434 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.041255 | 0.051335 |        94.8751 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.008315 | 0.010435 |        99.9688 |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.02482  | 0.031455 |        99.7815 |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.04104  | 0.05179  |        95.191  |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.00807  | 0.009995 |       100      |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.02438  | 0.03047  |        99.844  |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.040435 | 0.05057  |        95.3183 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.00825  | 0.01014  |       100      |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.024125 | 0.02986  |        99.922  |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.040835 | 0.05055  |        95.24   |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.00842  | 0.01106  |        99.9219 |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.02473  | 0.030775 |        99.859  |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.04017  | 0.04981  |        95.2895 |                     6313 |
