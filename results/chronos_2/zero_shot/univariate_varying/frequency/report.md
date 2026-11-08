# Chronos-2 Frequency benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.16231  | 0.18728  |        98.1875 |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 | 1.55758  | 5.30355  |        92.8168 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 | 1.27961  | 1.50754  |        80.9998 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.150625 | 0.174185 |        98.5393 |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.94412  | 1.2213   |        90.5682 |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 1.915    | 4.99308  |        82.4463 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.1675   | 0.19528  |        98.9401 |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 1.55841  | 1.7675   |        90.4649 |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 2.34485  | 6.77172  |        81.7297 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.159325 | 0.18322  |        99.1719 |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.814875 | 1.01239  |        92.4595 |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 1.47684  | 1.85532  |        78.3033 |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.231275 | 0.299445 |        97.8124 |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 1.13792  | 2.49538  |        91.4565 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 2.47448  | 4.89364  |        78.8717 |                     6313 |
