# Validation-split tuning of the robust-periodicity methods

Mean over the validation split (100 sequences per dataset, 40 datasets). `MAE all` is the tuning objective. One parameter is varied at a time; `defaults` is the setting in the source files.

| Method | Setting | MAE all (us) | MAE noisy lv1-3 (us) | Hit rate noisy (%) | ms / sequence |
|---|---|---:|---:|---:|---:|
| `sdif` | defaults | 19.919 | 23.647 | 72.3 | 14.2 |
| `sdif` | `toa.PHASE_TOL_US` = 2.0 | 20.814 | 24.840 | 72.1 | 15.2 |
| `sdif` | `toa.PHASE_TOL_US` = 4.0 | 19.919 | 23.647 | 72.3 | 18.3 |
| `sdif` | `toa.PHASE_TOL_US` = 8.0 | 19.919 | 23.647 | 72.3 | 19.3 |
| `sdif` | `toa.MIN_INLIER_FRACTION` = 0.7 | 19.919 | 23.647 | 72.3 | 19.0 |
| `sdif` | `toa.MIN_INLIER_FRACTION` = 0.8 | 19.919 | 23.647 | 72.3 | 19.5 |
| `sdif` | `toa.MIN_INLIER_FRACTION` = 0.9 | 19.919 | 23.647 | 72.3 | 19.2 |
| `sdif` | `toa.MIN_COVERAGE` = 0.5 | 19.919 | 23.647 | 72.3 | 19.6 |
| `sdif` | `toa.MIN_COVERAGE` = 0.7 | 19.919 | 23.647 | 72.3 | 18.7 |
| `sdif` | `toa.MIN_COVERAGE` = 0.85 | 19.919 | 23.647 | 72.3 | 18.6 |
| `sdif` | `toa.FALLBACK_WINDOW` = 32 | 20.056 | 23.791 | 72.3 | 19.2 |
| `sdif` | `toa.FALLBACK_WINDOW` = 64 | 19.950 | 23.691 | 72.3 | 18.6 |
| `sdif` | `toa.FALLBACK_WINDOW` = 96 | 19.919 | 23.647 | 72.3 | 18.6 |
| `sdif` | `cdif_sdif.BIN_WIDTH_US` = 1.0 | 20.377 | 24.258 | 72.1 | 38.1 |
| `sdif` | `cdif_sdif.BIN_WIDTH_US` = 2.0 | 19.919 | 23.647 | 72.3 | 19.5 |
| `sdif` | `cdif_sdif.BIN_WIDTH_US` = 4.0 | 19.919 | 23.647 | 72.3 | 14.4 |
| `sdif` | `cdif_sdif.SDIF_X` = 0.15 | 19.875 | 23.588 | 72.4 | 20.9 |
| `sdif` | `cdif_sdif.SDIF_X` = 0.3 | 19.919 | 23.647 | 72.3 | 19.0 |
| `sdif` | `cdif_sdif.SDIF_X` = 0.5 | 22.074 | 26.520 | 70.9 | 17.3 |
| `sdif` | `cdif_sdif.SEARCH_RHO` = 0.5 | 41.476 | 42.482 | 63.6 | 18.2 |
| `sdif` | `cdif_sdif.SEARCH_RHO` = 0.7 | 19.919 | 23.647 | 72.3 | 18.5 |
| `sdif` | `cdif_sdif.SEARCH_RHO` = 0.85 | 19.919 | 23.647 | 72.3 | 18.2 |
| `cdif` | defaults | 19.875 | 23.588 | 72.4 | 91.5 |
| `cdif` | `cdif_sdif.CDIF_GAMMA` = 0.3 | 19.875 | 23.588 | 72.4 | 139.5 |
| `cdif` | `cdif_sdif.CDIF_GAMMA` = 0.5 | 19.875 | 23.588 | 72.4 | 90.2 |
| `cdif` | `cdif_sdif.CDIF_GAMMA` = 0.8 | 19.875 | 23.589 | 72.4 | 48.0 |
| `pri_transform` | defaults | 72.507 | 72.082 | 41.0 | 80.7 |
| `pri_transform` | `pri_transform.ALPHA` = 0.2 | 72.772 | 72.378 | 40.7 | 76.6 |
| `pri_transform` | `pri_transform.ALPHA` = 0.3 | 72.507 | 72.082 | 41.0 | 75.0 |
| `pri_transform` | `pri_transform.ALPHA` = 0.5 | 71.596 | 71.068 | 42.2 | 76.2 |
| `pri_transform` | `pri_transform.BETA` = 0.1 | 65.984 | 68.840 | 43.6 | 77.5 |
| `pri_transform` | `pri_transform.BETA` = 0.15 | 72.507 | 72.082 | 41.0 | 74.7 |
| `pri_transform` | `pri_transform.BETA` = 0.3 | 73.586 | 73.347 | 40.0 | 75.2 |
| `pri_transform` | `pri_transform.MIN_PERIODS` = 2.5 | 72.583 | 72.010 | 41.0 | 109.4 |
| `pri_transform` | `pri_transform.MIN_PERIODS` = 4.0 | 72.507 | 72.082 | 41.0 | 77.2 |
| `lomb_scargle` | defaults | 20.520 | 24.448 | 72.0 | 8.3 |
| `lomb_scargle` | `lomb_scargle.MIN_POWER` = 0.15 | 20.287 | 24.137 | 72.1 | 8.9 |
| `lomb_scargle` | `lomb_scargle.MIN_POWER` = 0.25 | 20.520 | 24.448 | 72.0 | 8.0 |
| `lomb_scargle` | `lomb_scargle.MIN_POWER` = 0.4 | 22.146 | 26.616 | 71.1 | 8.0 |
| `toa_grid_fit` | defaults | 19.831 | 23.530 | 72.4 | 114.2 |
| `toa_grid_fit` | `toa_grid_fit.RANSAC_ITERS` = 0 | 19.863 | 23.573 | 72.4 | 90.8 |
| `toa_grid_fit` | `toa_grid_fit.RANSAC_ITERS` = 12 | 19.831 | 23.530 | 72.4 | 123.4 |
| `toa_grid_fit` | `toa_grid_fit.RANSAC_ITERS` = 30 | 19.823 | 23.520 | 72.4 | 172.1 |
| `toa_grid_fit_hedged` | defaults | 20.096 | 23.884 | 71.5 | 126.4 |
| `period_estimation_template_gate` | defaults | 19.848 | 23.553 | 72.4 | 126.0 |
| `kalman_filter_template_gate` | defaults | 20.230 | 23.950 | 72.3 | 351.8 |
| `imm_filter` | defaults | 33.262 | 41.408 | 58.5 | 302.3 |
| `imm_filter` | `imm_filter.P_STAY` = 0.9 | 44.891 | 56.297 | 51.3 | 297.7 |
| `imm_filter` | `imm_filter.P_STAY` = 0.98 | 33.262 | 41.408 | 58.5 | 307.8 |
| `imm_filter` | `imm_filter.P_STAY` = 0.995 | 26.393 | 32.250 | 64.1 | 306.1 |
| `imm_filter` | `imm_filter.PROPAGATE_MODES` = False | 33.262 | 41.408 | 58.5 | 295.7 |
| `imm_filter` | `imm_filter.PROPAGATE_MODES` = True | 45.326 | 51.935 | 35.6 | 316.9 |
| `forecast_combination` | defaults | 22.038 | 26.478 | 70.5 | 1680.8 |
| `forecast_combination` | `forecast_combination.WEIGHT_POWER` = 1.0 | 21.831 | 26.202 | 70.3 | 1640.1 |
| `forecast_combination` | `forecast_combination.WEIGHT_POWER` = 2.0 | 22.038 | 26.478 | 70.5 | 1593.4 |
| `forecast_combination` | `forecast_combination.WEIGHT_POWER` = 4.0 | 22.098 | 26.557 | 70.4 | 1344.6 |
| `period_estimation` | defaults | 21.830 | 26.195 | 71.2 | 19.9 |
| `kalman_filter` | defaults | 23.288 | 28.027 | 68.3 | 245.4 |
