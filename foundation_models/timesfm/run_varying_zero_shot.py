"""PULSAR: High-Throughput Zero-Shot Evaluation Runner for Varying Profile.

Keeps TimesFM 3.0 warm in VRAM and executes zero-shot evaluation across all
5 univariate parameters and the joint 5-channel multivariate regime.
"""

from __future__ import annotations
from pathlib import Path
import time
from typing import List

from timesfm import TimesFM3Forecaster

from foundation_models.timesfm.evaluate import (
    evaluate_single_dataset,
    export_benchmark_results,
    PARAM_SPECS,
)
from foundation_models.timesfm.evaluate_multivariate import (
    evaluate_single_multivariate_dataset,
    export_multivariate_benchmark_results,
)

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
DATASETS_ROOT = PROJECT_ROOT / "datasets" / "single_radar" / "varying"
RESULTS_ROOT = PROJECT_ROOT / "results" / "timesfm_3.0" / "zero_shot"

RADAR_TYPES = ["stable", "jitter", "stagger", "dwell_and_switch", "sliding"]
ERROR_LEVELS = ["clean", "error_lv1", "error_lv2", "error_lv3"]


def run_all_varying_zero_shot():
    t_start_total = time.time()

    print("=" * 80)
    print("PULSAR: Loading Google TimesFM 3.0 for Complete Varying Zero-Shot Benchmarking")
    print("=" * 80)

    tfm = TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch", per_core_batch_size=32)

    # 1. Univariate Evaluations across all 5 parameters
    for param_key, spec in PARAM_SPECS.items():
        param_name = spec["name"]
        param_slug = spec["slug"]
        param_unit = spec["unit"]
        tolerance = spec["default_tol"]

        target_dir = RESULTS_ROOT / "univariate_varying" / param_slug
        plots_dir = target_dir / "plots"

        print("\n" + "-" * 80)
        print(f"Beginning Univariate Zero-Shot: {param_name} (±{tolerance:g} {param_unit})")
        print(f"Target Directory: {target_dir}")
        print("-" * 80)

        t_param_start = time.time()
        results = []

        for rtype in RADAR_TYPES:
            for elevel in ERROR_LEVELS:
                folder_name = f"1000x128_{elevel}"
                dataset_dir = DATASETS_ROOT / rtype / folder_name
                dataset_display = f"{rtype}/{folder_name}"

                res = evaluate_single_dataset(
                    tfm=tfm,
                    dataset_dir=dataset_dir,
                    dataset_display=dataset_display,
                    radar_type=rtype,
                    error_level=elevel,
                    context_len=96,
                    horizon_len=32,
                    max_test_seqs=200,
                    target_param=param_key,
                    tolerance=tolerance,
                    unit=param_unit,
                    param_display_name=param_name,
                    plots_dir=plots_dir,
                )
                if res:
                    results.append(res)

        export_benchmark_results(
            results,
            target_dir,
            title=f"TimesFM 3.0 Zero-Shot Benchmark Report [{param_name} Varying]",
            unit=param_unit,
        )
        t_param_elapsed = time.time() - t_param_start
        print(f"[COMPLETE] {param_name} finished in {t_param_elapsed:.1f}s")

    # 2. Joint 5-Channel Multivariate Evaluation
    print("\n" + "=" * 80)
    print("Beginning Joint 5-Channel Multivariate Zero-Shot [Varying Profile]")
    print("=" * 80)

    mv_target_dir = RESULTS_ROOT / "multivariate_varying"
    mv_plots_dir = mv_target_dir / "plots"

    t_mv_start = time.time()
    mv_results = []

    for rtype in RADAR_TYPES:
        for elevel in ERROR_LEVELS:
            folder_name = f"1000x128_{elevel}"
            dataset_dir = DATASETS_ROOT / rtype / folder_name
            dataset_display = f"{rtype}/{folder_name}"

            res = evaluate_single_multivariate_dataset(
                tfm=tfm,
                dataset_dir=dataset_dir,
                dataset_display=dataset_display,
                radar_type=rtype,
                error_level=elevel,
                context_len=96,
                horizon_len=32,
                max_test_seqs=200,
                plots_dir=mv_plots_dir,
            )
            if res:
                mv_results.append(res)

    export_multivariate_benchmark_results(
        mv_results,
        mv_target_dir,
        title="TimesFM 3.0 Joint 5-Channel Benchmark [ZERO_SHOT - Varying]",
    )
    t_mv_elapsed = time.time() - t_mv_start
    print(f"[COMPLETE] Multivariate Zero-Shot finished in {t_mv_elapsed:.1f}s")

    total_time = time.time() - t_start_total
    print("\n" + "=" * 80)
    print(f"ALL VARYING ZERO-SHOT BENCHMARKS COMPLETE in {total_time:.1f}s ({total_time/60:.1f} min)")
    print("=" * 80)


if __name__ == "__main__":
    run_all_varying_zero_shot()

