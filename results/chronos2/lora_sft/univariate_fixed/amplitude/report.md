# Chronos-2 Amplitude benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.15819  | 0.1969   |       100      |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.39997  | 0.49769  |       100      |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.80969  | 1.0035   |        95.25   |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.16126  | 0.200925 |       100      |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.394445 | 0.491    |       100      |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.806565 | 1.00285  |        95.2331 |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.160735 | 0.20023  |       100      |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.399895 | 0.49664  |       100      |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.808965 | 1.00998  |        95.1983 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.159935 | 0.198835 |       100      |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.39777  | 0.49398  |        99.9844 |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.806525 | 1.00466  |        95.0729 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.15883  | 0.197175 |       100      |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.39866  | 0.505995 |        99.9839 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.80129  | 0.998355 |        95.3142 |                     6327 |
