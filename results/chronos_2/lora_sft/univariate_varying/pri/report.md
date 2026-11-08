# Chronos-2 PRI benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |       mae |       rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|----------:|-----------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 |  0        |   0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 |  0.07232  |   0.150605 |        99.9844 |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 |  0.303725 |   0.657695 |        99.9209 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 |  0.614365 |   1.00107  |        99.8412 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 48.4924   |  60.2591   |        13.7655 |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 48.7955   |  60.135    |        13.1804 |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 48.4883   |  60.0889   |        14.0213 |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 48.5308   |  60.092    |        13.8445 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 |  2.1839   |   2.57534  |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 32.2247   |  42.2894   |        64.0949 |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 68.6853   |  88.9254   |        26.2893 |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 91.7925   | 117.686    |        14.7067 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 |  1.78121  |   2.01908  |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 |  7.57349  |  19.8826   |        95.9086 |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 23.0702   |  56.7777   |        82.979  |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 37.9522   |  80.9217   |        67.182  |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 |  2.13791  |   2.65058  |        99.8752 |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 11.33     |  22.5174   |        76.4303 |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 24.6167   |  43.1211   |        50.1568 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 38.0275   |  59.7639   |        30.1551 |                     6313 |
