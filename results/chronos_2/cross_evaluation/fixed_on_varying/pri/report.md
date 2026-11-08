# Chronos-2 PRI benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |       mae |      rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|----------:|----------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 |  0        |   0       |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 |  0.06612  |   0.10997 |        99.9844 |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 |  0.31024  |   0.54454 |        99.9053 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 |  0.663475 |   0.9637  |        99.8245 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 48.4665   |  60.2346  |        13.8126 |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 48.7363   |  60.0701  |        13.0871 |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 48.4138   |  60.0074  |        13.9732 |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 48.5321   |  60.0958  |        14.0189 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 |  2.84445  |   3.39014 |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 32.8683   |  43.2674  |        65.2517 |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 68.7007   |  89.0883  |        27.6068 |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 92.021    | 117.835   |        15.4929 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 |  2.08704  |   2.32869 |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 |  8.40393  |  21.4494  |        94.7674 |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 24.6188   |  57.9834  |        79.8635 |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 40.288    |  82.3425  |        63.6574 |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 |  3.48925  |   4.28233 |        93.4059 |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 12.584    |  23.6495  |        72.3345 |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 27.4455   |  45.3152  |        47.6759 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 39.9951   |  60.8984  |        29.262  |                     6313 |
