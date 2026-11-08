# Chronos-2 PW benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.00817  | 0.010135 |       100      |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.025145 | 0.03254  |        99.8278 |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.04211  | 0.05475  |        94.4504 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.00824  | 0.010415 |        99.9844 |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.02491  | 0.032    |        99.8594 |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.045415 | 0.06081  |        94.0495 |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.008285 | 0.010285 |       100      |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.024885 | 0.030865 |        99.9058 |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.04136  | 0.052375 |        94.9636 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.008125 | 0.0101   |       100      |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.02513  | 0.034565 |        99.922  |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.04104  | 0.05123  |        94.7538 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.009265 | 0.0113   |        99.5    |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.02491  | 0.033445 |        99.8591 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.04913  | 0.064635 |        94.0926 |                     6327 |
