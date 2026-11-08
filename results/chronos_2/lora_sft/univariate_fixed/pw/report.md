# Chronos-2 PW benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.008075 | 0.01008  |       100      |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.02442  | 0.03036  |        99.8903 |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.04027  | 0.05027  |        94.9409 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.008195 | 0.010155 |       100      |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.024035 | 0.02986  |        99.9688 |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.040685 | 0.050875 |        94.9584 |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.008205 | 0.010165 |       100      |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.02453  | 0.03038  |        99.922  |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.04036  | 0.05016  |        95.1685 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.00803  | 0.009965 |       100      |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.024095 | 0.030215 |        99.9532 |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.04053  | 0.05043  |        95.2329 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.008095 | 0.010075 |       100      |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.02429  | 0.031495 |        99.8747 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.041245 | 0.053245 |        94.9276 |                     6327 |
