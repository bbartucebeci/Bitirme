# Chronos-2 PW benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.007895 | 0.009845 |       100      |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.024035 | 0.0298   |        99.8908 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.040735 | 0.0508   |        95.1441 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.008315 | 0.010635 |        99.9844 |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.02418  | 0.030255 |        99.8752 |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.040125 | 0.049925 |        95.4734 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.00803  | 0.009945 |       100      |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.02417  | 0.030135 |        99.9053 |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.03992  | 0.049695 |        95.4293 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.008155 | 0.01008  |       100      |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.023825 | 0.029525 |        99.9376 |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.04038  | 0.051225 |        95.6618 |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.008035 | 0.01008  |       100      |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.02442  | 0.03042  |        99.8902 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.039515 | 0.049075 |        95.6401 |                     6313 |
