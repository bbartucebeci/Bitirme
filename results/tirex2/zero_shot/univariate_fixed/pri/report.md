# TiRex-2 PRI zero-shot benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.
The point forecast is TiRex-2's 0.5 quantile (median).

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |       mae |      rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|----------:|----------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 |  0        |   0       |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 |  0.213495 |   0.22839 |       100      |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 |  0.737885 |   0.98118 |        99.6094 |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 |  2.70899  |   4.70404 |        98.2622 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 40.3119   |  50.2461  |        15.9532 |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 40.0331   |  49.8241  |        15.7104 |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 40.8686   |  50.8804  |        14.9089 |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 41.208    |  51.4051  |        15.4867 |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 |  6.79564  |   8.105   |        65.62   |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 36.6503   |  45.6659  |        52.044  |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 69.4864   |  86.0846  |        33.7884 |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 93.0326   | 114.429   |        17.7121 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 |  6.58696  |   7.69556 |        81.25   |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 15.167    |  31.0744  |        74.2295 |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 32.6038   |  61.8564  |        55.2324 |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 53.0801   |  87.5035  |        37.6402 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 | 11.9554   |  14.2018  |        46.88   |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 19.2647   |  30.7898  |        42.7602 |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 34.8701   |  55.1336  |        30.4147 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 48.5718   |  69.7513  |        20.5262 |                     6327 |
