# Chronos-2 Frequency benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.108045 | 0.131445 |       100      |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.89569  | 2.64432  |        97.4991 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 | 1.0004   | 1.22113  |        88.285  |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.101215 | 0.124815 |       100      |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.501485 | 0.62008  |        98.6892 |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 1.253    | 2.65431  |        89.5915 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.11534  | 0.140985 |        99.6875 |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.52824  | 0.644355 |        98.1826 |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 1.22321  | 2.09525  |        87.6501 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.10878  | 0.132975 |       100      |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.523675 | 0.635815 |        97.6911 |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 1.08204  | 1.30367  |        86.6059 |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.12184  | 0.149765 |        99.5469 |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.547595 | 0.67939  |        97.2829 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 1.12085  | 1.48114  |        86.1965 |                     6313 |
