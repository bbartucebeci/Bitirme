# TiRex-2 Frequency zero-shot benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.
The point forecast is TiRex-2's 0.5 quantile (median).

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.25112  | 0.282635 |        96.2511 |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.747255 | 0.86982  |        91.1578 |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 | 5.4744   | 8.75317  |        68.7758 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 1.627    | 2.91126  |        98.4532 |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 1.49568  | 2.34566  |        91.6367 |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 2.93984  | 4.94775  |        70.8721 |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.18897  | 0.212585 |        97.9844 |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.884735 | 1.02153  |        88.9635 |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 2.2224   | 3.13748  |        71.1732 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.14578  | 0.169995 |        98.9374 |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.84807  | 0.97782  |        90.3195 |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 1.63076  | 1.90094  |        75.2501 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.256585 | 0.369975 |        98.4638 |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.844265 | 0.973315 |        90.8878 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 1.75481  | 2.03834  |        75.5722 |                     6327 |
