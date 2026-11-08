# TiRex-2 PRI zero-shot benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.
The point forecast is TiRex-2's 0.5 quantile (median).

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |       mae |       rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|----------:|-----------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 |  0        |   0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 |  0.1681   |   0.191875 |        99.9844 |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 |  0.899295 |   1.7443   |        99.5778 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 |  1.86355  |   2.86563  |        98.9173 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 48.548    |  60.3161   |        13.7033 |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 48.865    |  60.1541   |        12.9469 |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 48.7911   |  60.6087   |        14.1775 |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 49.6822   |  61.8324   |        13.4036 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 |  7.78409  |   8.7937   |        67.1252 |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 39.4933   |  48.9825   |        48.6883 |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 73.7287   |  92.7395   |        26.7105 |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 98.6286   | 121.892    |        12.6549 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 |  4.75815  |   5.46216  |        94.2658 |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 11.5063   |  23.3423   |        84.5959 |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 29.8976   |  60.5595   |        61.5055 |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 49.6904   |  87.1764   |        43.7355 |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 | 11.7934   |  15.1231   |        50.7346 |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 20.8521   |  33.1799   |        43.9153 |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 35.6291   |  54.3287   |        31.8231 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 49.8971   |  71.3856   |        19.6594 |                     6313 |
