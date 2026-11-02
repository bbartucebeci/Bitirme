# Chronos-2 PRI benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |       mae |      rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|----------:|----------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 |  0        |   0       |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 |  0.190295 |   0.20659 |        99.6719 |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 |  0.649795 |   1.73918 |        99.8423 |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 |  6.69739  |   8.85914 |        97.6255 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 40.5546   |  50.4887  |        16.1251 |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 40.312    |  50.1587  |        15.6292 |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 40.9725   |  50.9854  |        15.1265 |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 40.7318   |  51.1167  |        15.7506 |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 |  2.213    |   2.665   |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 41.8236   |  53.6843  |        68.0778 |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 76.5667   |  97.934   |        36.6731 |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 96.8007   | 120.509   |        17.5144 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 |  1.732    |   1.97    |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 11.2443   |  26.4006  |        91.2407 |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 32.3338   |  65.1764  |        71.6005 |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 53.014    |  92.2583  |        48.7764 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 |  2.635    |   3.04    |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 17.507    |  28.3761  |        74.1912 |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 38.0132   |  60.3005  |        41.5333 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 49.7185   |  73.1037  |        23.418  |                     6327 |
