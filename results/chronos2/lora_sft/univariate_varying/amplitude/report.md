# Chronos-2 Amplitude benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.162385 | 0.2015   |       100      |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.39985  | 0.49954  |        99.9688 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.799455 | 0.9941   |        95.2483 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.15797  | 0.19666  |       100      |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.404965 | 0.508705 |        99.9844 |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.804915 | 1.0052   |        95.2901 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.16227  | 0.201035 |       100      |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.40263  | 0.501635 |       100      |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.79925  | 0.99591  |        95.283  |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.161655 | 0.200845 |       100      |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.39529  | 0.493785 |       100      |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.8131   | 1.00748  |        95.279  |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.169835 | 0.21027  |        99.8594 |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.40198  | 0.500495 |       100      |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.79985  | 0.992335 |        95.8678 |                     6313 |
