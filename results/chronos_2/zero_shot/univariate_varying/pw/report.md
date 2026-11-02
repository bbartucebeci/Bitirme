# Chronos-2 PW benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.00796  | 0.00995  |       100      |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.024445 | 0.03057  |        99.8122 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.043065 | 0.05911  |        94.8892 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.008635 | 0.012045 |        99.9844 |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.025045 | 0.033345 |        99.796  |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.045005 | 0.05912  |        94.8154 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.0081   | 0.010075 |       100      |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.028515 | 0.034915 |        99.3898 |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.04056  | 0.050485 |        95.1918 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.00824  | 0.010175 |       100      |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.02474  | 0.03234  |        99.8752 |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.041915 | 0.05641  |        95.1141 |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.008155 | 0.01044  |        99.9844 |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.02476  | 0.03106  |        99.874  |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.04036  | 0.050975 |        95.3456 |                     6313 |
