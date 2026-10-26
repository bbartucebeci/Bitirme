"""PULSAR: Cross-Profile Generalization Evaluation Runner.

Cross-evaluates:
1. Fixed PRI LoRA Model on Varying Profile Test Sets (4,000 seqs)
2. Fixed Multivariate LoRA Model on Varying Profile Test Sets (4,000 seqs)
3. Varying PRI LoRA Model on Fixed Profile Test Sets (4,000 seqs)
4. Varying Multivariate LoRA Model on Fixed Profile Test Sets (4,000 seqs)

Outputs raw metrics to `results/timesfm_3.0/cross_evaluation/` and compiles the
master 4-way cross-profile generalization report.
"""

from __future__ import annotations
from pathlib import Path
import sys
import time
from typing import List

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from foundation_models.timesfm.adapter import TimesFMLoRAEngine
from foundation_models.timesfm.evaluate import (
    evaluate_single_dataset,
    export_benchmark_results,
)
from foundation_models.timesfm.evaluate_multivariate import (
    evaluate_single_multivariate_dataset,
    export_multivariate_benchmark_results,
)

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
DATASETS_ROOT = PROJECT_ROOT / "datasets" / "single_radar"
MODELS_ROOT = PROJECT_ROOT / "models" / "timesfm_lora"
CROSS_EVAL_ROOT = PROJECT_ROOT / "results" / "timesfm_3.0" / "cross_evaluation"

RADAR_TYPES = ["stable", "jitter", "stagger", "dwell_and_switch", "sliding"]
ERROR_LEVELS = ["clean", "error_lv1", "error_lv2", "error_lv3"]


def eval_univariate_pri_cross(weights_dir: Path, target_profile: str, output_subdir: Path, title: str):
    print("\n" + "=" * 80)
    print(f"PULSAR CROSS-EVAL: Univariate PRI [{title}]")
    print(f"Weights: {weights_dir}")
    print(f"Test Data: {target_profile.capitalize()} Profile (20 datasets, 4,000 sequences)")
    print(f"Destination: {output_subdir}")
    print("=" * 80)

    t0 = time.time()
    tfm = TimesFMLoRAEngine.load_for_inference(weights_dir=weights_dir)
    plots_dir = output_subdir / "plots"
    datasets_dir = DATASETS_ROOT / target_profile

    results = []
    for rtype in RADAR_TYPES:
        for elevel in ERROR_LEVELS:
            folder_name = f"1000x128_{elevel}"
            dataset_dir = datasets_dir / rtype / folder_name
            res = evaluate_single_dataset(
                tfm=tfm,
                dataset_dir=dataset_dir,
                dataset_display=f"{rtype}/{folder_name}",
                radar_type=rtype,
                error_level=elevel,
                context_len=96,
                horizon_len=32,
                max_test_seqs=200,
                target_param="PRI",
                tolerance=10.0,
                unit="us",
                param_display_name="Pulse Repetition Interval (PRI)",
                plots_dir=plots_dir,
            )
            if res:
                results.append(res)

    export_benchmark_results(results, output_subdir, title=title, unit="us")
    print(f"[COMPLETE] {title} finished in {time.time() - t0:.1f}s")


def eval_multivariate_cross(weights_dir: Path, target_profile: str, output_subdir: Path, title: str):
    print("\n" + "=" * 80)
    print(f"PULSAR CROSS-EVAL: Joint 5-Channel Multivariate [{title}]")
    print(f"Weights: {weights_dir}")
    print(f"Test Data: {target_profile.capitalize()} Profile (20 datasets, 4,000 sequences)")
    print(f"Destination: {output_subdir}")
    print("=" * 80)

    t0 = time.time()
    tfm = TimesFMLoRAEngine.load_for_inference(weights_dir=weights_dir)
    plots_dir = output_subdir / "plots"
    datasets_dir = DATASETS_ROOT / target_profile

    results = []
    for rtype in RADAR_TYPES:
        for elevel in ERROR_LEVELS:
            folder_name = f"1000x128_{elevel}"
            dataset_dir = datasets_dir / rtype / folder_name
            res = evaluate_single_multivariate_dataset(
                tfm=tfm,
                dataset_dir=dataset_dir,
                dataset_display=f"{rtype}/{folder_name}",
                radar_type=rtype,
                error_level=elevel,
                context_len=96,
                horizon_len=32,
                max_test_seqs=200,
                plots_dir=plots_dir,
            )
            if res:
                results.append(res)

    export_multivariate_benchmark_results(results, output_subdir, title=title)
    print(f"[COMPLETE] {title} finished in {time.time() - t0:.1f}s")


def run_all_cross_evaluations():
    t_start = time.time()

    # 1. Fixed PRI on Varying Profile Test Data
    eval_univariate_pri_cross(
        weights_dir=MODELS_ROOT / "pri" / "best_model",
        target_profile="varying",
        output_subdir=CROSS_EVAL_ROOT / "fixed_on_varying" / "pri",
        title="Train: Fixed | Test: Varying [Univariate PRI]",
    )

    # 2. Fixed Multivariate on Varying Profile Test Data
    eval_multivariate_cross(
        weights_dir=MODELS_ROOT / "multivariate_fixed" / "best_model",
        target_profile="varying",
        output_subdir=CROSS_EVAL_ROOT / "fixed_on_varying" / "multivariate",
        title="Train: Fixed | Test: Varying [Joint 5-Channel Multivariate]",
    )

    # 3. Varying PRI on Fixed Profile Test Data
    eval_univariate_pri_cross(
        weights_dir=MODELS_ROOT / "varying" / "pri" / "best_model",
        target_profile="fixed",
        output_subdir=CROSS_EVAL_ROOT / "varying_on_fixed" / "pri",
        title="Train: Varying | Test: Fixed [Univariate PRI]",
    )

    # 4. Varying Multivariate on Fixed Profile Test Data
    eval_multivariate_cross(
        weights_dir=MODELS_ROOT / "multivariate_varying" / "best_model",
        target_profile="fixed",
        output_subdir=CROSS_EVAL_ROOT / "varying_on_fixed" / "multivariate",
        title="Train: Varying | Test: Fixed [Joint 5-Channel Multivariate]",
    )

    total_time = time.time() - t_start
    print("\n" + "=" * 80)
    print(f"PULSAR: All Cross-Profile Evaluations Complete in {total_time:.1f}s ({total_time/60:.1f} min)")
    print("=" * 80)

    # 5. Automatically compile master cross-profile generalization matrix
    from foundation_models.common.summary import compile_cross_evaluation_summary
    compile_cross_evaluation_summary()


if __name__ == "__main__":
    run_all_cross_evaluations()
