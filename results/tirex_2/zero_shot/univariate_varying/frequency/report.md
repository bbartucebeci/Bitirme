# TiRex-2 Frequency zero-shot benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.
The point forecast is TiRex-2's 0.5 quantile (median).

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.19489  | 0.221475 |        98.0015 |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 | 1.70095  | 2.77322  |        90.3191 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 | 1.44051  | 1.73252  |        78.9247 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.16141  | 0.189965 |        98.7389 |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 2.32228  | 3.96758  |        90.6794 |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 1.92697  | 3.78766  |        76.5177 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.248405 | 0.279385 |        96.9068 |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 2.2728   | 3.58123  |        86.42   |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 1.80221  | 2.40432  |        72.5504 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.174995 | 0.2016   |        98.7183 |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.997185 | 1.37619  |        89.5298 |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 2.94071  | 4.79452  |        74.0504 |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.63988  | 1.03781  |        97.9219 |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 1.78883  | 3.74568  |        88.0979 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 1.95271  | 3.48454  |        74.1708 |                     6313 |
