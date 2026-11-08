# TiRex-2 Amplitude zero-shot benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.
The point forecast is TiRex-2's 0.5 quantile (median).

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.158975 | 0.19789  |       100      |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.402715 | 0.50354  |        99.9844 |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.8155   | 1.01191  |        95.0433 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.16175  | 0.20168  |       100      |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.39628  | 0.49343  |       100      |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.81899  | 1.03374  |        94.9786 |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.161885 | 0.201645 |       100      |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.402135 | 0.499665 |       100      |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.81218  | 1.01511  |        94.9414 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.1606   | 0.199695 |       100      |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.40227  | 0.501835 |        99.9688 |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.817795 | 1.01934  |        94.7918 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.159525 | 0.199155 |        99.9844 |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.400045 | 0.50159  |        99.9839 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.81152  | 1.01082  |        95.0292 |                     6327 |
