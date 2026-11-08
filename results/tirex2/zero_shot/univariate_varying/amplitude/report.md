# TiRex-2 Amplitude zero-shot benchmark (varying)

Dataset size: `1000x128`. Context: 96. Horizon: 32.
Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.
The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.
Sequences with no emitter pulses in the target window are excluded and counted.
The point forecast is TiRex-2's 0.5 quantile (median).

| radar_type       | error_level   |   num_sequences |   skipped_short |   skipped_no_emitter |      mae |     rmse |   hit_rate_pct |   valid_pulses_evaluated |
|:-----------------|:--------------|----------------:|----------------:|---------------------:|---------:|---------:|---------------:|-------------------------:|
| stable           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stable           | error_lv1     |             200 |               0 |                    0 | 0.16283  | 0.20209  |       100      |                     6393 |
| stable           | error_lv2     |             200 |               0 |                    0 | 0.403265 | 0.503705 |        99.9688 |                     6366 |
| stable           | error_lv3     |             200 |               0 |                    0 | 0.80507  | 1.0012   |        95.105  |                     6330 |
| jitter           | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| jitter           | error_lv1     |             200 |               0 |                    0 | 0.158995 | 0.19797  |       100      |                     6396 |
| jitter           | error_lv2     |             200 |               0 |                    0 | 0.407315 | 0.50953  |        99.9688 |                     6357 |
| jitter           | error_lv3     |             200 |               0 |                    0 | 0.81052  | 1.00655  |        95.0862 |                     6328 |
| stagger          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| stagger          | error_lv1     |             200 |               0 |                    0 | 0.163045 | 0.20204  |       100      |                     6395 |
| stagger          | error_lv2     |             200 |               0 |                    0 | 0.40743  | 0.509585 |        99.9366 |                     6361 |
| stagger          | error_lv3     |             200 |               0 |                    0 | 0.8067   | 1.00337  |        95.2357 |                     6312 |
| dwell_and_switch | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| dwell_and_switch | error_lv1     |             200 |               0 |                    0 | 0.1621   | 0.201645 |       100      |                     6392 |
| dwell_and_switch | error_lv2     |             200 |               0 |                    0 | 0.399975 | 0.49898  |        99.9844 |                     6353 |
| dwell_and_switch | error_lv3     |             200 |               0 |                    0 | 0.822585 | 1.01941  |        95.2144 |                     6326 |
| sliding          | clean         |             200 |               0 |                    0 | 0        | 0        |       100      |                     6400 |
| sliding          | error_lv1     |             200 |               0 |                    0 | 0.164915 | 0.204935 |       100      |                     6396 |
| sliding          | error_lv2     |             200 |               0 |                    0 | 0.404825 | 0.50351  |       100      |                     6362 |
| sliding          | error_lv3     |             200 |               0 |                    0 | 0.80585  | 1.00037  |        95.5001 |                     6313 |
