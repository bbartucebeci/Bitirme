# Chronos-2 PRI benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |      rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|----------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 |  0       |   0       |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 |  0.07432 |   0.08601 |       100      |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 |  0.34759 |   0.92486 |        99.8578 |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 |  3.41547 |   4.18009 |        98.696  |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 40.2818  |  50.1619  |        16.0157 |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 39.8739  |  49.62    |        15.724  |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 40.4998  |  50.3048  |        15.3319 |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 40.2532  |  50.1142  |        16.0526 |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 |  1.962   |   2.409   |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 31.4062  |  40.2226  |        67.8473 |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 65.8576  |  83.2562  |        36.7782 |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 87.6386  | 109.537   |        18.3187 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 |  2.281   |   2.474   |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 |  9.29555 |  22.8487  |        95.4585 |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 23.0578  |  53.7138  |        83.488  |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 38.697   |  79.2632  |        66.1492 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 |  2.081   |   2.491   |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 10.1718  |  20.7026  |        80.7087 |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 24.3697  |  44.945   |        50.3348 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 38.095   |  61.4195  |        30.527  |                     6327 |
