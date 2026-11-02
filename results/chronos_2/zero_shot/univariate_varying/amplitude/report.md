# Chronos-2 Amplitude benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.16348  | 0.202815 |       100      |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.51669  | 0.61698  |        99.5    |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.81149  | 1.01303  |        95.011  |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.159475 | 0.198445 |       100      |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.627655 | 0.750275 |        98.9844 |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 1.00755  | 1.21391  |        94.6924 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.163235 | 0.20247  |       100      |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.506415 | 0.606125 |        99.4688 |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.806495 | 1.00371  |        95.2355 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.16292  | 0.202545 |       100      |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.40109  | 0.500455 |        99.9844 |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.822245 | 1.02069  |        95.2497 |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.225065 | 0.26514  |        99.5    |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.407255 | 0.506295 |        99.9844 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.806885 | 1.01249  |        95.6144 |                     6313 |
