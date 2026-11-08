# TiRex-2 PW zero-shot benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.
The point forecast is TiRex-2's 0.5 quantile (median).

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.008175 | 0.01014  |       100      |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.024625 | 0.03049  |        99.8747 |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.041795 | 0.0543   |        94.6885 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.008515 | 0.01118  |        99.9375 |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.025105 | 0.032165 |        99.8126 |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.042995 | 0.0575   |        94.615  |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.008235 | 0.010275 |       100      |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.02471  | 0.030605 |        99.9064 |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.041305 | 0.051705 |        94.7713 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.00811  | 0.01005  |       100      |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.02431  | 0.03028  |        99.922  |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.041115 | 0.05159  |        94.9485 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.008175 | 0.010135 |       100      |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.02431  | 0.030315 |        99.9058 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.041945 | 0.05429  |        94.5879 |                     6327 |
