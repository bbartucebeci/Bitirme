# TiRex-2 AOA zero-shot benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.
The point forecast is TiRex-2's 0.5 quantile (median).

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   circular_mae |   circular_hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|---------------:|------------------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.04179  | 0.05164  |       100      |       0.04179  |                100      |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.172075 | 0.216455 |        99.9375 |       0.172075 |                 99.9375 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.441045 | 0.599175 |        99.8439 |       0.441045 |                 99.8439 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.04173  | 0.05173  |       100      |       0.04173  |                100      |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.17348  | 0.215575 |       100      |       0.17348  |                100      |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.43708  | 0.598445 |        99.8417 |       0.43708  |                 99.8417 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.84628  | 1.20367  |        99.5156 |       0.115905 |                 99.5781 |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 1.0512   | 1.329    |        99.2813 |       0.49183  |                 99.2813 |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 1.69417  | 2.58741  |        98.9673 |       1.21204  |                 98.9829 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.041975 | 0.051925 |       100      |       0.041975 |                100      |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.16985  | 0.21009  |       100      |       0.16985  |                100      |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.423875 | 0.533795 |        99.8559 |       0.423875 |                 99.8559 |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.04622  | 0.06074  |        99.9219 |       0.04622  |                 99.9219 |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.167105 | 0.21172  |        99.9688 |       0.167105 |                 99.9688 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.452645 | 0.6786   |        99.8906 |       0.452645 |                 99.8906 |                     6313 |
