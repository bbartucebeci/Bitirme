# Chronos-2 Amplitude benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.160025 | 0.198905 |       100      |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.403235 | 0.50202  |       100      |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 | 1.32882  | 1.52638  |        93.5073 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.212565 | 0.25245  |        99.5    |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.422185 | 0.52225  |        99.4844 |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.83074  | 1.03365  |        94.4305 |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.16201  | 0.201915 |       100      |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.403425 | 0.500985 |       100      |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.866165 | 1.08702  |        94.3807 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.16191  | 0.201295 |       100      |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.405145 | 0.511495 |        99.9688 |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.82645  | 1.04889  |        94.5988 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.303205 | 0.342    |        99.5    |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.40543  | 0.523215 |        99.9839 |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.808675 | 1.00783  |        95.1101 |                     6327 |
