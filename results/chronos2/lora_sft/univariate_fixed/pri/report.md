# Chronos-2 PRI benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |       rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|-----------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 |  0       |   0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 |  0.07498 |   0.086925 |       100      |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 |  0.35777 |   0.942565 |        99.8735 |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 |  3.13136 |   3.80778  |        98.6975 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 40.248   |  50.1362   |        16.1718 |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 39.8743  |  49.5945   |        15.6447 |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 40.4725  |  50.2918   |        15.3124 |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 40.2612  |  50.1096   |        16.073  |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 |  2.41016 |   2.90296  |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 32.0124  |  41.2325   |        68.4243 |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 66.2011  |  84.1277   |        38.5185 |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 87.7104  | 110.141    |        19.0926 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 |  1.75796 |   1.99324  |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 |  8.67811 |  22.1724   |        95.5521 |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 20.8186  |  49.7664   |        83.946  |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 35.3464  |  74.701    |        68.6655 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 |  1.99108 |   2.40576  |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 |  9.47505 |  19.5546   |        82.6937 |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 21.8285  |  41.7442   |        54.487  |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 35.0545  |  58.5259   |        33.4515 |                     6327 |
