# TiRex-2 PRI zero-shot benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.
The point forecast is TiRex-2's 0.5 quantile (median).

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |       mae |      rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|----------:|----------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 |   0       |   0       |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 |   0.17718 |   0.22448 |        99.9375 |                     6396 |
| stable           | error_lv2     |             200 |               0 |                    0 |   1.06788 |   1.97056 |        99.4678 |                     6357 |
| stable           | error_lv3     |             200 |               0 |                    0 |   1.81819 |   3.49721 |        98.8453 |                     6328 |
| jitter           | clean         |             200 |               0 |                    0 |  48.6721  |  60.2054  |        13.2035 |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 |  47.879   |  59.5113  |        13.5364 |                     6388 |
| jitter           | error_lv2     |             200 |               0 |                    0 |  49.1985  |  61.2942  |        13.7719 |                     6366 |
| jitter           | error_lv3     |             200 |               0 |                    0 |  48.921   |  61.108   |        14.0131 |                     6307 |
| stagger          | clean         |             200 |               0 |                    0 |   7.76579 |   8.80651 |        66.7815 |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 |  31.6973  |  39.8207  |        53.7552 |                     6398 |
| stagger          | error_lv2     |             200 |               0 |                    0 |  72.1602  |  90.6219  |        27.9123 |                     6364 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 101.58    | 124.969   |        12.4258 |                     6327 |
| dwell_and_switch | clean         |             200 |               0 |                    0 |   4.7697  |   5.47168 |        94.2035 |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 |  14.58    |  27.9428  |        84.0001 |                     6396 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 |  27.873   |  57.317   |        64.4011 |                     6357 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 |  51.3078  |  89.2755  |        42.4519 |                     6325 |
| sliding          | clean         |             200 |               0 |                    0 |  11.7808  |  15.0957  |        50.8599 |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 |  19.0878  |  30.4515  |        46.1651 |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 |  36.3621  |  55.6786  |        29.7393 |                     6355 |
| sliding          | error_lv3     |             200 |               0 |                    0 |  52.9391  |  76.0227  |        19.3636 |                     6315 |
