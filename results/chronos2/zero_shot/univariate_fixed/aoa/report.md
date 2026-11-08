# Chronos-2 AOA benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   circular_mae |   circular_hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|---------------:|------------------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.04069  | 0.050485 |       100      |       0.04069  |                100      |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.16197  | 0.20172  |       100      |       0.16197  |                100      |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.84406  | 1.0393   |        99.2944 |       0.84406  |                 99.2944 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.04141  | 0.05225  |       100      |       0.04141  |                100      |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.16733  | 0.213215 |        99.9375 |       0.16733  |                 99.9375 |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.421635 | 0.578055 |        99.9219 |       0.421635 |                 99.9219 |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.04056  | 0.05053  |       100      |       0.04056  |                100      |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.163965 | 0.20295  |       100      |       0.163965 |                100      |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.64758  | 0.864735 |        99.2188 |       0.64758  |                 99.2188 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.040725 | 0.050325 |       100      |       0.040725 |                100      |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.175315 | 0.27338  |        99.9688 |       0.175315 |                 99.9688 |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.433325 | 0.63059  |        99.9376 |       0.433325 |                 99.9376 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.04653  | 0.056355 |       100      |       0.04653  |                100      |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.162255 | 0.201125 |       100      |       0.162255 |                100      |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.75925  | 0.909245 |        99.4199 |       0.75925  |                 99.4199 |                     6327 |
