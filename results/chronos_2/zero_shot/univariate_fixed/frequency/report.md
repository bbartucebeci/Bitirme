# Chronos-2 Frequency benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.22146  | 0.250095 |        97.3447 |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 | 1.03982  | 2.8735   |        93.8187 |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 | 4.43758  | 6.21341  |        75.3014 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.32857  | 0.50834  |        99.125  |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.78411  | 0.992695 |        93.6327 |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 1.98502  | 3.74597  |        76.6341 |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.18933  | 0.213305 |        98.3488 |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.784205 | 0.901385 |        90.0294 |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 2.00694  | 3.92546  |        76.8503 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.13854  | 0.161965 |        99.0468 |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.704765 | 0.82046  |        93.14   |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 2.44783  | 7.92967  |        81.1308 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.19379  | 0.239545 |        98.6754 |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.678505 | 0.799195 |        93.694  |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 1.48199  | 2.05452  |        78.0389 |                     6327 |
