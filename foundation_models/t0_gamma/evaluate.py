"""PULSAR: t0-gamma univariate evaluation suite."""

from __future__ import annotations

import argparse
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

import numpy as np

from foundation_models.common.dataset import load_dataset_sequences, clean_pri_context
from foundation_models.common.metrics import compute_forecast_metrics
from foundation_models.common.plotting import save_forecast_plot
from foundation_models.common.summary import export_benchmark_results, PARAM_SPECS
from foundation_models.t0_gamma.adapter import T0GammaForecaster

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
DEFAULT_DATASETS_ROOT = PROJECT_ROOT / "datasets" / "single_radar"
DEFAULT_RESULTS_ROOT = PROJECT_ROOT / "results" / "t0_gamma"


def evaluate_single_dataset(
    model: Any,
    dataset_dir: Path,
    dataset_display: str,
    radar_type: str,
    error_level: str,
    context_len: int,
    horizon_len: int,
    max_test_seqs: Optional[int],
    target_param: str = "PRI",
    tolerance: float = 10.0,
    unit: str = "us",
    param_display_name: str = "PRI",
    plots_dir: Optional[Path] = None,
    clean_context: bool = False,
) -> Optional[Dict[str, Any]]:
    if not dataset_dir.exists():
        print(f"[SKIP] Directory not found: {dataset_dir}")
        return None

    try:
        test_seqs = load_dataset_sequences(
            dataset_dir, split="test", max_seqs=max_test_seqs, target_param=target_param
        )
    except Exception as e:
        print(f"[ERROR] Failed to load {dataset_display}: {e}")
        return None

    if not test_seqs:
        print(f"[SKIP] No test sequences in {dataset_display}")
        return None

    valid_items = []
    required_len = context_len + horizon_len
    for seq_id, ctx_vals, tgt_vals, mask_vals in test_seqs:
        if len(ctx_vals) >= required_len:
            c = ctx_vals[:context_len]
            if clean_context and target_param.upper() in ["PRI", "MEASURED_DELTA_TOA"]:
                c = clean_pri_context(c, target_len=context_len)
            valid_items.append(
                (seq_id, c, tgt_vals[context_len : context_len + horizon_len], mask_vals[context_len : context_len + horizon_len])
            )

    if not valid_items:
        print(f"[SKIP] No sequences meet required length ({required_len}) in {dataset_display}")
        return None

    contexts = [item[1] for item in valid_items]
    try:
        outputs = list(model.predict_batch(contexts=contexts, horizon=horizon_len))
    except Exception as e:
        print(f"[ERROR] Batch inference failed for {dataset_display}: {e}")
        return None

    mae_list, rmse_list, hit_rate_list = [], [], []
    for idx, (seq_id, ctx, gt, mask) in enumerate(valid_items):
        preds = np.asarray(outputs[idx].forecast, dtype=np.float32).squeeze()[:horizon_len]
        metrics = compute_forecast_metrics(preds, gt, tolerance=tolerance, mask=mask, unit=unit)
        if metrics.get("valid_pulses_evaluated", 0) == 0:
            continue
        mae_list.append(metrics["mae"])
        rmse_list.append(metrics["rmse"])
        hit_rate_list.append(metrics["hit_rate_pct"])

        # Diagnostic plot for the first sequence
        if plots_dir is not None and idx == 0:
            plots_dir.mkdir(parents=True, exist_ok=True)
            plot_path = plots_dir / f"{radar_type}_{error_level}.png"
            title = f"t0-gamma {param_display_name} Forecast | {dataset_display} ({seq_id})"
            try:
                save_forecast_plot(
                    plot_path,
                    title=title,
                    context=ctx,
                    ground_truth=gt,
                    predictions=preds,
                    tolerance=tolerance,
                    param_label=param_display_name,
                    unit=unit,
                )
            except Exception:
                pass

    return {
        "radar_type": radar_type,
        "error_level": error_level,
        "parameter": target_param,
        "evaluated_sequences": len(mae_list),
        "context_length": context_len,
        "horizon_length": horizon_len,
        f"mae_{unit}": round(float(np.mean(mae_list)), 3),
        f"rmse_{unit}": round(float(np.mean(rmse_list)), 3),
        "gate_hit_rate_pct": round(float(np.mean(hit_rate_list)), 2),
        "tolerance": tolerance,
        "unit": unit,
    }
def main():
    parser = argparse.ArgumentParser(description="PULSAR: t0-gamma Univariate Evaluation")
    parser.add_argument("--model-id", type=str, default="theforecastingcompany/t0-gamma")
    parser.add_argument("--radar-type", type=str, default="all")
    parser.add_argument("--profile-mode", choices=["fixed", "varying"], default="fixed")
    parser.add_argument("--error-level", type=str, default="all")
    parser.add_argument("--target-param", type=str, default="PRI")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--tolerance", type=float, default=None)
    parser.add_argument("--tolerance-us", type=float, default=None)
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--clean-context", action="store_true", help="Apply classical clean_pri_context filter to input context before inference")
    parser.add_argument("--no-plots", action="store_true")

    args = parser.parse_args()

    param_key = "PRI" if args.target_param == "Measured_Delta_TOA" else args.target_param
    spec = PARAM_SPECS.get(param_key, {"name": param_key, "slug": param_key.lower(), "unit": "units", "default_tol": 1.0, "scale": 1.0})
    param_name = spec["name"]
    param_unit = spec["unit"]
    param_slug = spec["slug"]
    tolerance = args.tolerance or args.tolerance_us or spec["default_tol"]

    if args.results_dir is None:
        target_dir = DEFAULT_RESULTS_ROOT / "zero_shot" / f"univariate_{args.profile_mode}" / param_slug
    else:
        target_dir = args.results_dir

    plots_dir = None if args.no_plots else target_dir / "plots"
    radar_types = ["stable", "jitter", "stagger", "dwell_and_switch", "sliding"] if args.radar_type == "all" else [args.radar_type]
    error_levels = ["clean", "error_lv1", "error_lv2", "error_lv3"] if args.error_level == "all" else [args.error_level]

    model = T0GammaForecaster.load_for_inference(model_id=args.model_id)

    print("=" * 70)
    print(f"t0-gamma Univariate Evaluation | {param_name} | {args.profile_mode}")
    print(f"Model: {args.model_id}")
    print("=" * 70)

    results = []
    t_start = time.time()
    for rtype in radar_types:
        for elevel in error_levels:
            # Discover the actual folder name (supports both 1000x128 and smoke-test 10x128)
            dataset_dir = None
            for pattern in [f"1000x128_{elevel}", f"10x128_{elevel}"]:
                candidate = DEFAULT_DATASETS_ROOT / args.profile_mode / rtype / pattern
                if candidate.exists():
                    dataset_dir = candidate
                    break
            if dataset_dir is None:
                print(f"[SKIP] Directory not found for {rtype}/{elevel}")
                continue
            dataset_display = f"{rtype}/{dataset_dir.name}"
            res = evaluate_single_dataset(
                model=model,
                dataset_dir=dataset_dir,
                dataset_display=dataset_display,
                radar_type=rtype,
                error_level=elevel,
                context_len=args.context_len,
                horizon_len=args.horizon,
                max_test_seqs=args.max_test_seqs,
                target_param=param_key,
                tolerance=tolerance,
                unit=param_unit,
                param_display_name=param_name,
                plots_dir=plots_dir,
                clean_context=args.clean_context,
            )
            if res:
                results.append(res)

    total = time.time() - t_start
    print(f"\nCompleted in {total:.1f}s")

    if results:
        title = f"t0-gamma Zero-Shot Univariate Benchmark [{param_name} {args.profile_mode.capitalize()}]"
        export_benchmark_results(results, target_dir, title=title, unit=param_unit)


if __name__ == "__main__":
    main()