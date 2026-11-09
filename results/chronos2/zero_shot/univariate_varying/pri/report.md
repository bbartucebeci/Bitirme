# Chronos-2 PRI benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |       mae |       rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|----------:|-----------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 |   0       |   0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 |   0.18398 |   0.207035 |        99.6562 |                     6396 |
| stable           | error_lv2     |             200 |               0 |                    0 |   4.68813 |   8.03445  |        98.624  |                     6357 |
| stable           | error_lv3     |             200 |               0 |                    0 |   1.69241 |   4.4306   |        98.9233 |                     6328 |
| jitter           | clean         |             200 |               0 |                    0 |  49.0135  |  60.5751   |        13.0473 |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 |  48.7278  |  60.5194   |        13.57   |                     6388 |
| jitter           | error_lv2     |             200 |               0 |                    0 |  49.2231  |  61.3086   |        13.5308 |                     6366 |
| jitter           | error_lv3     |             200 |               0 |                    0 |  55.6803  |  67.7514   |        13.7502 |                     6307 |
| stagger          | clean         |             200 |               0 |                    0 |   2.88899 |   3.48214  |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 |  42.8291  |  55.0001   |        69.5952 |                     6398 |
| stagger          | error_lv2     |             200 |               0 |                    0 |  73.9915  |  96.461    |        32.0832 |                     6364 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 101.087   | 126.713    |        13.8413 |                     6327 |
| dwell_and_switch | clean         |             200 |               0 |                    0 |   1.28858 |   1.47566  |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 |  13.5104  |  28.0872   |        91.028  |                     6396 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 |  30.3077  |  63.3203   |        77.4869 |                     6357 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 |  50.4903  |  93.8724   |        51.9924 |                     6325 |
| sliding          | clean         |             200 |               0 |                    0 |   3.24624 |   4.16622  |        95.6554 |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 |  19.2191  |  29.833    |        74.7204 |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 |  33.2328  |  52.8573   |        40.5761 |                     6355 |
| sliding          | error_lv3     |             200 |               0 |                    0 |  54.847   |  78.1219   |        25.0412 |                     6315 |
