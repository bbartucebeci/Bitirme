# Chronos-2 AOA benchmark (fixed)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   circular_mae |   circular_hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|---------------:|------------------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.040115 | 0.049885 |       100      |       0.040115 |                100      |                     6392 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.16102  | 0.200205 |       100      |       0.16102  |                100      |                     6377 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.40871  | 0.52277  |        99.9844 |       0.40871  |                 99.9844 |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.040305 | 0.05034  |       100      |       0.040305 |                100      |                     6390 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.161175 | 0.200575 |       100      |       0.161175 |                100      |                     6364 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.40274  | 0.503465 |        99.9844 |       0.40274  |                 99.9844 |                     6339 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.040025 | 0.049795 |       100      |       0.040025 |                100      |                     6391 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.161335 | 0.200015 |       100      |       0.161335 |                100      |                     6375 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.401555 | 0.4971   |        99.9844 |       0.401555 |                 99.9844 |                     6333 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.03991  | 0.04949  |       100      |       0.03991  |                100      |                     6393 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.168545 | 0.243545 |        99.9688 |       0.168545 |                 99.9688 |                     6383 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.415575 | 0.55542  |        99.9688 |       0.415575 |                 99.9688 |                     6330 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |       0        |                100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.04059  | 0.050375 |       100      |       0.04059  |                100      |                     6390 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.16094  | 0.19982  |       100      |       0.16094  |                100      |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.403185 | 0.50278  |        99.9844 |       0.403185 |                 99.9844 |                     6327 |
