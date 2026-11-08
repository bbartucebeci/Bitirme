# Chronos-2 Frequency benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.118985 | 0.14569  |        99.9683 |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.77734  | 2.25922  |        99.1716 |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 | 1.32686  | 1.65955  |        84.8319 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.114465 | 0.14986  |        99.8906 |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.51877  | 0.634245 |        98.0772 |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 1.12007  | 1.67758  |        88.2917 |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.128805 | 0.15334  |        99.5468 |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.5149   | 0.63174  |        97.6762 |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 1.152    | 1.38174  |        85.7382 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.11177  | 0.135475 |        99.5781 |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.52039  | 0.633035 |        98.4947 |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 1.10119  | 1.65554  |        88.3158 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.11299  | 0.13742  |        99.7031 |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.5486   | 0.66415  |        97.2748 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 1.12728  | 1.4513   |        86.8871 |                     6327 |
