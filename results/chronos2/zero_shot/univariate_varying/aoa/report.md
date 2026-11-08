# Chronos-2 AOA benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   circular_mae |   circular_hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|---------------:|------------------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.04106  | 0.0508   |       100      |       0.04106  |                100      |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.18466  | 0.308875 |        99.9532 |       0.18466  |                 99.9532 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.457145 | 0.759715 |        99.9376 |       0.44433  |                 99.9376 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.041675 | 0.05161  |       100      |       0.041675 |                100      |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.19257  | 0.235175 |        99.4844 |       0.19257  |                 99.4844 |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.455815 | 0.743705 |        99.9365 |       0.44981  |                 99.9365 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.82984  | 1.23099  |        99.6094 |       0.05774  |                 99.6875 |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 1.04472  | 1.31691  |        99.4062 |       0.47524  |                 99.4062 |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 1.68144  | 2.64824  |        99.2188 |       0.900295 |                 99.2813 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.040425 | 0.05018  |       100      |       0.040425 |                100      |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.161235 | 0.201165 |       100      |       0.161235 |                100      |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.409555 | 0.52426  |        99.9688 |       0.409555 |                 99.9688 |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.082905 | 0.095825 |        99.5    |       0.082905 |                 99.5    |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.162945 | 0.20242  |       100      |       0.162945 |                100      |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.437735 | 0.65359  |        99.9532 |       0.437735 |                 99.9532 |                     6313 |
