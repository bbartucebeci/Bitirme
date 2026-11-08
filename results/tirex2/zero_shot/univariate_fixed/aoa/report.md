# TiRex-2 AOA zero-shot benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.
The point forecast is TiRex-2's 0.5 quantile (median).

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   circular_mae |   circular_hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|---------------:|------------------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.04233  | 0.052305 |       100      |       0.04233  |                100      |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.169595 | 0.225575 |        99.9688 |       0.169595 |                 99.9688 |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.454305 | 0.624795 |        99.6205 |       0.454305 |                 99.6205 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.043465 | 0.057115 |        99.9688 |       0.043465 |                 99.9688 |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.17791  | 0.23334  |        99.9062 |       0.17791  |                 99.9062 |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.43873  | 0.585765 |        99.7339 |       0.43873  |                 99.7339 |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.04146  | 0.05146  |       100      |       0.04146  |                100      |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.16572  | 0.205    |       100      |       0.16572  |                100      |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.41879  | 0.54565  |        99.8907 |       0.41879  |                 99.8907 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.04058  | 0.050285 |       100      |       0.04058  |                100      |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.167435 | 0.210125 |        99.9844 |       0.167435 |                 99.9844 |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.41595  | 0.51991  |        99.9844 |       0.41595  |                 99.9844 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.044105 | 0.0541   |       100      |       0.044105 |                100      |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.16519  | 0.20763  |        99.9688 |       0.16519  |                 99.9688 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.415765 | 0.52002  |        99.9375 |       0.415765 |                 99.9375 |                     6327 |
