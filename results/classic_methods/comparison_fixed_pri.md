# Classic Methods Side-by-Side Comparison [PRI - Fixed]

## 1. Root Mean Squared Error (RMSE) & Mean Absolute Error (MAE)

| Radar Type | Error Level | Rolling Median RMSE (us) | Period Est. RMSE (us) | HMM RMSE (us) | Rolling Median MAE (us) | Period Est. MAE (us) | HMM MAE (us) |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| `stable` | `error_lv1` | 0.01 | 0.01 | 0.27 | 0.01 | 0.01 | 0.10 |
| `stable` | `error_lv2` | 0.08 | 0.04 | 10.14 | 0.08 | 0.04 | 3.55 |
| `stable` | `error_lv3` | 0.15 | 0.09 | 19.35 | 0.15 | 0.09 | 6.71 |
| `jitter` | `clean` | 51.17 | 50.09 | 50.09 | 40.66 | 39.62 | 39.62 |
| `jitter` | `error_lv1` | 51.21 | 51.06 | 52.30 | 41.59 | 41.51 | 42.41 |
| `jitter` | `error_lv2` | 49.77 | 49.24 | 49.26 | 39.35 | 39.06 | 39.07 |
| `jitter` | `error_lv3` | 50.66 | 50.67 | 51.13 | 40.43 | 40.45 | 40.81 |
| `stagger` | `clean` | 121.51 | 0.00 | 0.00 | 98.44 | 0.00 | 0.00 |
| `stagger` | `error_lv1` | 121.70 | 36.65 | 36.65 | 98.76 | 29.27 | 29.27 |
| `stagger` | `error_lv2` | 121.77 | 60.30 | 60.40 | 98.92 | 40.58 | 40.67 |
| `stagger` | `error_lv3` | 121.70 | 88.96 | 87.73 | 98.92 | 66.09 | 64.97 |
| `dwell_and_switch` | `clean` | 150.00 | 0.00 | 0.00 | 150.00 | 0.00 | 0.00 |
| `dwell_and_switch` | `error_lv1` | 160.68 | 23.06 | 23.17 | 150.16 | 6.80 | 12.39 |
| `dwell_and_switch` | `error_lv2` | 167.34 | 52.62 | 79.83 | 150.19 | 18.36 | 42.09 |
| `dwell_and_switch` | `error_lv3` | 188.06 | 91.67 | 136.14 | 150.25 | 40.69 | 80.27 |
| `sliding` | `clean` | 92.19 | 0.00 | 35.87 | 80.00 | 0.00 | 30.55 |
| `sliding` | `error_lv1` | 92.39 | 12.68 | 49.77 | 80.19 | 4.18 | 41.49 |
| `sliding` | `error_lv2` | 93.10 | 23.77 | 56.80 | 80.78 | 9.51 | 45.97 |
| `sliding` | `error_lv3` | 93.66 | 43.75 | 66.34 | 81.36 | 18.97 | 52.07 |

## 2. Tactical Gate Hit Rate (+/-10 us) & Inference Latency

| Radar Type | Error Level | Rolling Median Hit Rate | Period Est. Hit Rate | HMM Hit Rate | Rolling Median Latency (us) | Period Est. Latency (us) | HMM Latency (us) |
|---|---|---:|---:|---:|---:|---:|---:|
| `stable` | `clean` | 100.0% | 100.0% | 100.0% | 224.0 | 111.9 | 108.3 |
| `stable` | `error_lv1` | 100.0% | 100.0% | 99.8% | 125.2 | 4801.2 | 152836.5 |
| `stable` | `error_lv2` | 100.0% | 100.0% | 97.9% | 110.1 | 4729.6 | 145132.3 |
| `stable` | `error_lv3` | 100.0% | 100.0% | 96.7% | 106.5 | 4751.5 | 146799.6 |
| `jitter` | `clean` | 15.7% | 17.3% | 17.3% | 124.6 | 4724.6 | 59311.6 |
| `jitter` | `error_lv1` | 14.4% | 14.3% | 14.2% | 122.1 | 4750.4 | 54779.2 |
| `jitter` | `error_lv2` | 17.7% | 16.1% | 16.1% | 114.6 | 4641.3 | 30699.6 |
| `jitter` | `error_lv3` | 16.9% | 16.2% | 16.1% | 103.7 | 4729.6 | 63138.4 |
| `stagger` | `clean` | 34.4% | 100.0% | 100.0% | 99.3 | 5018.3 | 106695.3 |
| `stagger` | `error_lv1` | 34.2% | 85.3% | 85.3% | 101.3 | 5070.5 | 112994.3 |
| `stagger` | `error_lv2` | 34.1% | 79.7% | 79.7% | 104.5 | 5111.7 | 118546.7 |
| `stagger` | `error_lv3` | 34.2% | 67.0% | 67.1% | 103.0 | 4832.3 | 113988.7 |
| `dwell_and_switch` | `clean` | 0.0% | 100.0% | 100.0% | 98.9 | 5102.5 | 114292.9 |
| `dwell_and_switch` | `error_lv1` | 7.9% | 97.3% | 95.9% | 100.1 | 4913.4 | 129715.2 |
| `dwell_and_switch` | `error_lv2` | 13.9% | 93.6% | 85.0% | 105.0 | 4951.6 | 124107.8 |
| `dwell_and_switch` | `error_lv3` | 28.9% | 85.7% | 72.7% | 110.0 | 5078.6 | 114103.9 |
| `sliding` | `clean` | 12.5% | 100.0% | 25.0% | 148.8 | 5167.7 | 123255.2 |
| `sliding` | `error_lv1` | 6.1% | 91.7% | 12.7% | 105.0 | 5143.7 | 123842.7 |
| `sliding` | `error_lv2` | 6.2% | 79.9% | 12.1% | 102.5 | 5162.3 | 129681.8 |
| `sliding` | `error_lv3` | 6.0% | 62.4% | 11.4% | 110.3 | 5046.8 | 128530.1 |
