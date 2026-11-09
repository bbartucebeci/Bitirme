# Chronos-2 PRI benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |       mae |       rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|----------:|-----------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 |  0        |   0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 |  0.055825 |   0.065015 |       100      |                     6396 |
| stable           | error_lv2     |             200 |               0 |                    0 |  1.66848  |   3.92637  |        98.749  |                     6357 |
| stable           | error_lv3     |             200 |               0 |                    0 |  0.74514  |   1.58313  |        99.7006 |                     6328 |
| jitter           | clean         |             200 |               0 |                    0 | 48.6982   |  60.1656   |        13.3751 |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 47.7936   |  59.3518   |        13.4912 |                     6388 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 48.7168   |  60.5986   |        13.7811 |                     6366 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 49.7394   |  61.4691   |        13.7743 |                     6307 |
| stagger          | clean         |             200 |               0 |                    0 |  2.21278  |   2.60514  |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 27.9619   |  36.8829   |        68.0994 |                     6398 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 63.2465   |  83.1859   |        29.437  |                     6364 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 93.5062   | 117.907    |        13.9962 |                     6327 |
| dwell_and_switch | clean         |             200 |               0 |                    0 |  1.72587  |   1.96516  |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 |  9.95535  |  23.6954   |        94.5756 |                     6396 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 21.6113   |  53.2462   |        85.7255 |                     6357 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 38.4307   |  81.2387   |        67.1822 |                     6325 |
| sliding          | clean         |             200 |               0 |                    0 |  2.22673  |   2.79665  |        99.8752 |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 10.2896   |  20.9499   |        79.5649 |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 25.0768   |  44.0233   |        48.0939 |                     6355 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 38.7376   |  61.1626   |        30.3285 |                     6315 |
