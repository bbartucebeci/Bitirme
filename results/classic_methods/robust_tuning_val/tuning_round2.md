# Validation-split tuning of the robust-periodicity methods

Mean over the validation split (100 sequences per dataset, 40 datasets). `MAE all` is the tuning objective. One parameter is varied at a time; `defaults` is the setting in the source files.

| Method | Setting | MAE all (us) | MAE noisy lv1-3 (us) | Hit rate noisy (%) | ms / sequence |
|---|---|---:|---:|---:|---:|
| `sdif` | defaults | 19.875 | 23.588 | 72.4 | 19.0 |
| `sdif` | `toa.PHASE_TOL_US` = 2.0 | 20.770 | 24.782 | 72.1 | 18.9 |
| `sdif` | `toa.PHASE_TOL_US` = 4.0 | 19.875 | 23.588 | 72.4 | 18.1 |
| `sdif` | `toa.PHASE_TOL_US` = 8.0 | 19.875 | 23.588 | 72.4 | 19.5 |
| `sdif` | `toa.MIN_INLIER_FRACTION` = 0.7 | 19.875 | 23.588 | 72.4 | 21.0 |
| `sdif` | `toa.MIN_INLIER_FRACTION` = 0.8 | 19.875 | 23.588 | 72.4 | 20.4 |
| `sdif` | `toa.MIN_INLIER_FRACTION` = 0.9 | 19.875 | 23.588 | 72.4 | 20.4 |
| `sdif` | `toa.MIN_COVERAGE` = 0.5 | 19.875 | 23.588 | 72.4 | 20.1 |
| `sdif` | `toa.MIN_COVERAGE` = 0.7 | 19.875 | 23.588 | 72.4 | 20.8 |
| `sdif` | `toa.MIN_COVERAGE` = 0.85 | 19.875 | 23.588 | 72.4 | 20.4 |
| `sdif` | `toa.FALLBACK_WINDOW` = 32 | 20.010 | 23.729 | 72.3 | 21.3 |
| `sdif` | `toa.FALLBACK_WINDOW` = 64 | 19.903 | 23.629 | 72.3 | 22.2 |
| `sdif` | `toa.FALLBACK_WINDOW` = 96 | 19.875 | 23.588 | 72.4 | 22.6 |
| `sdif` | `cdif_sdif.BIN_WIDTH_US` = 1.0 | 19.875 | 23.588 | 72.4 | 48.5 |
| `sdif` | `cdif_sdif.BIN_WIDTH_US` = 2.0 | 19.875 | 23.588 | 72.4 | 21.8 |
| `sdif` | `cdif_sdif.BIN_WIDTH_US` = 4.0 | 19.875 | 23.588 | 72.4 | 14.4 |
| `sdif` | `cdif_sdif.SDIF_X` = 0.08 | 19.875 | 23.589 | 72.4 | 24.7 |
| `sdif` | `cdif_sdif.SDIF_X` = 0.15 | 19.875 | 23.588 | 72.4 | 17.8 |
| `sdif` | `cdif_sdif.SDIF_X` = 0.3 | 19.919 | 23.647 | 72.3 | 16.1 |
| `sdif` | `cdif_sdif.SDIF_X` = 0.5 | 22.074 | 26.520 | 70.9 | 15.4 |
| `sdif` | `cdif_sdif.SEARCH_RHO` = 0.5 | 42.070 | 43.274 | 63.2 | 17.2 |
| `sdif` | `cdif_sdif.SEARCH_RHO` = 0.7 | 19.875 | 23.588 | 72.4 | 17.4 |
| `sdif` | `cdif_sdif.SEARCH_RHO` = 0.85 | 19.875 | 23.588 | 72.4 | 18.8 |
| `cdif` | defaults | 19.875 | 23.589 | 72.4 | 47.1 |
| `cdif` | `cdif_sdif.CDIF_GAMMA` = 0.3 | 19.875 | 23.588 | 72.4 | 150.8 |
| `cdif` | `cdif_sdif.CDIF_GAMMA` = 0.5 | 19.875 | 23.588 | 72.4 | 88.5 |
| `cdif` | `cdif_sdif.CDIF_GAMMA` = 0.8 | 19.875 | 23.589 | 72.4 | 46.2 |
| `pri_transform` | defaults | 68.535 | 67.210 | 45.5 | 90.1 |
| `pri_transform` | `pri_transform.ALPHA` = 0.2 | 66.361 | 69.564 | 43.0 | 100.8 |
| `pri_transform` | `pri_transform.ALPHA` = 0.3 | 65.984 | 68.840 | 43.6 | 99.0 |
| `pri_transform` | `pri_transform.ALPHA` = 0.5 | 68.535 | 67.210 | 45.5 | 95.3 |
| `pri_transform` | `pri_transform.ALPHA` = 0.8 | 65.285 | 62.982 | 49.9 | 92.8 |
| `pri_transform` | `pri_transform.BETA` = 0.02 | 53.971 | 56.025 | 56.1 | 90.1 |
| `pri_transform` | `pri_transform.BETA` = 0.05 | 56.697 | 58.303 | 53.9 | 76.8 |
| `pri_transform` | `pri_transform.BETA` = 0.1 | 68.535 | 67.210 | 45.5 | 73.7 |
| `pri_transform` | `pri_transform.BETA` = 0.15 | 71.596 | 71.068 | 42.2 | 73.1 |
| `pri_transform` | `pri_transform.BETA` = 0.3 | 73.520 | 73.376 | 40.1 | 73.0 |
| `pri_transform` | `pri_transform.MIN_PERIODS` = 2.5 | 69.074 | 68.154 | 45.4 | 118.7 |
| `pri_transform` | `pri_transform.MIN_PERIODS` = 4.0 | 68.535 | 67.210 | 45.5 | 91.3 |
| `lomb_scargle` | defaults | 20.287 | 24.137 | 72.1 | 10.2 |
| `lomb_scargle` | `lomb_scargle.MIN_POWER` = 0.05 | 20.236 | 24.070 | 72.2 | 12.1 |
| `lomb_scargle` | `lomb_scargle.MIN_POWER` = 0.1 | 20.292 | 24.145 | 72.1 | 9.9 |
| `lomb_scargle` | `lomb_scargle.MIN_POWER` = 0.15 | 20.287 | 24.137 | 72.1 | 9.0 |
| `lomb_scargle` | `lomb_scargle.MIN_POWER` = 0.25 | 20.520 | 24.448 | 72.0 | 8.7 |
| `lomb_scargle` | `lomb_scargle.MIN_POWER` = 0.4 | 22.146 | 26.616 | 71.1 | 8.9 |
| `toa_grid_fit` | defaults | 19.831 | 23.530 | 72.4 | 91.9 |
| `toa_grid_fit` | `toa_grid_fit.RANSAC_ITERS` = 0 | 19.863 | 23.573 | 72.4 | 62.1 |
| `toa_grid_fit` | `toa_grid_fit.RANSAC_ITERS` = 12 | 19.831 | 23.530 | 72.4 | 92.6 |
| `toa_grid_fit` | `toa_grid_fit.RANSAC_ITERS` = 30 | 19.823 | 23.520 | 72.4 | 141.6 |
| `imm_filter` | defaults | 26.393 | 32.250 | 64.1 | 290.3 |
| `imm_filter` | `imm_filter.P_STAY` = 0.9 | 44.891 | 56.297 | 51.3 | 294.4 |
| `imm_filter` | `imm_filter.P_STAY` = 0.98 | 33.262 | 41.408 | 58.5 | 306.9 |
| `imm_filter` | `imm_filter.P_STAY` = 0.995 | 26.393 | 32.250 | 64.1 | 300.1 |
| `imm_filter` | `imm_filter.P_STAY` = 0.999 | 24.118 | 29.187 | 67.2 | 274.1 |
| `imm_filter` | `imm_filter.P_STAY` = 0.9999 | 23.452 | 28.263 | 67.9 | 284.9 |
| `imm_filter` | `imm_filter.PROPAGATE_MODES` = False | 26.393 | 32.250 | 64.1 | 300.0 |
| `imm_filter` | `imm_filter.PROPAGATE_MODES` = True | 30.401 | 35.873 | 49.3 | 309.7 |
| `forecast_combination` | defaults | 21.831 | 26.202 | 70.3 | 1710.3 |
| `forecast_combination` | `forecast_combination.WEIGHT_POWER` = 0.5 | 21.944 | 26.353 | 70.2 | 1698.9 |
| `forecast_combination` | `forecast_combination.WEIGHT_POWER` = 1.0 | 21.831 | 26.202 | 70.3 | 1706.8 |
| `forecast_combination` | `forecast_combination.WEIGHT_POWER` = 2.0 | 22.038 | 26.478 | 70.5 | 1617.3 |
| `forecast_combination` | `forecast_combination.WEIGHT_POWER` = 4.0 | 22.098 | 26.557 | 70.4 | 1371.2 |
| `period_estimation_template_gate` | defaults | 19.848 | 23.553 | 72.4 | 114.9 |
| `kalman_filter_template_gate` | defaults | 20.230 | 23.950 | 72.3 | 304.2 |
