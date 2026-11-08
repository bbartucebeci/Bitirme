# Chronos-2 AOA benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   circular_mae |   circular_hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|---------------:|------------------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.0403   | 0.05001  |       100      |       0.0403   |                100      |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.16577  | 0.217855 |        99.9844 |       0.16577  |                 99.9844 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.41071  | 0.519745 |        99.9688 |       0.41071  |                 99.9688 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.04087  | 0.05075  |       100      |       0.04087  |                100      |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.16122  | 0.20176  |       100      |       0.16122  |                100      |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.407575 | 0.506405 |        99.9839 |       0.407575 |                 99.9839 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.829185 | 1.22576  |        99.5156 |       0.06128  |                 99.5156 |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 1.03214  | 1.26046  |        99.4844 |       0.463535 |                 99.4844 |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 1.66644  | 2.63262  |        99.1562 |       0.89902  |                 99.2031 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.039735 | 0.049505 |       100      |       0.039735 |                100      |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.16031  | 0.19937  |       100      |       0.16031  |                100      |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.401555 | 0.50016  |       100      |       0.401555 |                100      |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.040105 | 0.049915 |       100      |       0.040105 |                100      |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.16065  | 0.199965 |       100      |       0.16065  |                100      |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.407305 | 0.505345 |       100      |       0.407305 |                100      |                     6313 |
