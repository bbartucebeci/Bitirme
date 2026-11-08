# Chronos-2 PRI benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |       mae |       rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|----------:|-----------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 |   0       |   0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 |   0.19221 |   0.462995 |        99.9844 |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 |   0.80412 |   1.97439  |        99.3225 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 |   1.01933 |   1.50004  |        99.5126 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 |  48.8282  |  60.641    |        13.1562 |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 |  56.9314  |  68.2929   |        12.9778 |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 |  49.6237  |  61.5681   |        13.6874 |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 |  48.9792  |  60.6555   |        13.3326 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 |   2.88899 |   3.48214  |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 |  42.3923  |  54.6656   |        66.0482 |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 |  80.5341  | 103.797    |        29.7355 |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 100.074   | 125.81     |        15.2899 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 |   1.28858 |   1.47565  |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 |  10.5136  |  24.9116   |        91.1932 |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 |  31.2673  |  66.5134   |        72.591  |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 |  48.7614  |  89.4366   |        52.1757 |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 |   3.24624 |   4.16622  |        95.6554 |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 |  17.9176  |  29.284    |        70.0523 |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 |  33.8085  |  53.801    |        44.0902 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 |  48.0704  |  70.9278   |        23.9282 |                     6313 |
