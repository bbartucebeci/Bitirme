# Classic Methods Side-by-Side Comparison [PRI - Varying]

## 1. Root Mean Squared Error (RMSE) & Mean Absolute Error (MAE)

| Radar Type | Error Level | Rolling Median RMSE (us) | Period Est. RMSE (us) | HMM RMSE (us) | Rolling Median MAE (us) | Period Est. MAE (us) | HMM MAE (us) |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `stable` | `error_lv1` | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 | 0.01 |
| `stable` | `error_lv2` | 0.07 | 0.04 | 0.14 | 0.07 | 0.04 | 0.08 |
| `stable` | `error_lv3` | 0.17 | 0.08 | 0.88 | 0.17 | 0.08 | 0.34 |
| `jitter` | `clean` | 60.37 | 59.83 | 59.83 | 48.56 | 48.41 | 48.41 |
| `jitter` | `error_lv1` | 60.93 | 60.23 | 60.23 | 49.19 | 48.70 | 48.70 |
| `jitter` | `error_lv2` | 61.47 | 60.14 | 61.70 | 49.06 | 47.81 | 48.55 |
| `jitter` | `error_lv3` | 58.90 | 58.64 | 58.68 | 47.73 | 47.53 | 47.58 |
| `stagger` | `clean` | 130.44 | 0.00 | 0.00 | 99.80 | 0.00 | 0.00 |
| `stagger` | `error_lv1` | 130.70 | 17.96 | 17.96 | 100.06 | 11.88 | 11.88 |
| `stagger` | `error_lv2` | 130.65 | 76.14 | 76.14 | 100.03 | 51.48 | 51.48 |
| `stagger` | `error_lv3` | 131.25 | 109.29 | 115.30 | 100.80 | 78.00 | 83.80 |
| `dwell_and_switch` | `clean` | 212.59 | 0.00 | 0.00 | 177.44 | 0.00 | 0.00 |
| `dwell_and_switch` | `error_lv1` | 210.75 | 20.62 | 38.99 | 175.10 | 5.82 | 21.72 |
| `dwell_and_switch` | `error_lv2` | 211.03 | 38.35 | 56.01 | 174.26 | 11.57 | 26.68 |
| `dwell_and_switch` | `error_lv3` | 206.67 | 87.81 | 153.66 | 171.75 | 34.60 | 93.62 |
| `sliding` | `clean` | 96.85 | 0.00 | 42.79 | 84.12 | 0.00 | 36.47 |
| `sliding` | `error_lv1` | 97.02 | 8.32 | 47.69 | 84.28 | 3.66 | 39.81 |
| `sliding` | `error_lv2` | 97.96 | 21.78 | 58.96 | 85.19 | 10.54 | 48.47 |
| `sliding` | `error_lv3` | 97.90 | 48.03 | 71.14 | 85.12 | 21.59 | 56.39 |

## 2. Tactical Gate Hit Rate (+/-10 us) & Inference Latency

| Radar Type | Error Level | Rolling Median Hit Rate | Period Est. Hit Rate | HMM Hit Rate | Rolling Median Latency (us) | Period Est. Latency (us) | HMM Latency (us) |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 100.0% | 100.0% | 100.0% | 123.3 | 114.3 | 108.5 |
| `stable` | `error_lv1` | 100.0% | 100.0% | 100.0% | 101.7 | 4691.8 | 56096.8 |
| `stable` | `error_lv2` | 100.0% | 100.0% | 99.6% | 105.3 | 4549.2 | 53013.9 |
| `stable` | `error_lv3` | 100.0% | 100.0% | 99.6% | 103.2 | 4549.2 | 44740.1 |
| `jitter` | `clean` | 13.2% | 13.8% | 13.8% | 99.8 | 4678.1 | 24661.1 |
| `jitter` | `error_lv1` | 13.2% | 13.7% | 13.7% | 101.8 | 4586.2 | 20907.2 |
| `jitter` | `error_lv2` | 13.4% | 14.2% | 14.2% | 102.0 | 4646.4 | 24315.3 |
| `jitter` | `error_lv3` | 11.7% | 13.2% | 13.0% | 98.7 | 4759.3 | 20522.4 |
| `stagger` | `clean` | 33.4% | 100.0% | 100.0% | 96.0 | 4578.7 | 22411.6 |
| `stagger` | `error_lv1` | 33.3% | 93.7% | 93.7% | 99.0 | 4665.8 | 25212.5 |
| `stagger` | `error_lv2` | 33.4% | 73.2% | 73.2% | 99.6 | 4684.2 | 25069.7 |
| `stagger` | `error_lv3` | 33.2% | 62.7% | 61.1% | 101.8 | 4577.3 | 28445.7 |
| `dwell_and_switch` | `clean` | 25.9% | 100.0% | 100.0% | 98.0 | 4774.6 | 19009.8 |
| `dwell_and_switch` | `error_lv1` | 26.6% | 97.9% | 93.2% | 98.4 | 4811.6 | 27100.1 |
| `dwell_and_switch` | `error_lv2` | 27.8% | 95.5% | 91.4% | 102.0 | 4800.8 | 33725.7 |
| `dwell_and_switch` | `error_lv3` | 26.9% | 88.0% | 69.2% | 102.2 | 4682.5 | 32485.5 |
| `sliding` | `clean` | 6.1% | 100.0% | 12.9% | 100.2 | 4741.1 | 55961.9 |
| `sliding` | `error_lv1` | 6.4% | 89.8% | 11.1% | 97.0 | 4676.9 | 53830.0 |
| `sliding` | `error_lv2` | 6.3% | 80.8% | 9.9% | 99.7 | 4721.5 | 58023.2 |
| `sliding` | `error_lv3` | 6.5% | 56.0% | 10.2% | 101.2 | 4702.0 | 54801.3 |
