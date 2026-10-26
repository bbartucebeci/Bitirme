"""Evaluation CLI for Google TimesFM 3.0 (Zero-Shot or LoRA-Fine-Tuned)."""

from __future__ import annotations
import argparse
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from foundation_models.common.dataset import load_dataset_sequences
from foundation_models.common.metrics import compute_forecast_metrics
from foundation_models.common.plotting import save_forecast_plot
from foundation_models.timesfm.adapter import TimesFMLoRAEngine

# Path resolution
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
DEFAULT_DATASETS_ROOT = PROJECT_ROOT / "datasets" / "single_radar"

PARAM_SPECS = {
    "PRI": {"name": "PRI", "slug": "pri", "unit": "us", "default_tol": 10.0, "scale": 1000.0},
    "Frequency": {"name": "Carrier Frequency", "slug": "frequency", "unit": "MHz", "default_tol": 2.0, "scale": 1000.0},
    "PW": {"name": "Pulse Width", "slug": "pw", "unit": "us", "default_tol": 0.1, "scale": 1.0},
    "AOA": {"name": "Angle of Arrival", "slug": "aoa", "unit": "deg", "default_tol": 2.0, "scale": 100.0},
    "Amplitude": {"name": "Amplitude", "slug": "amplitude", "unit": "dBm", "default_tol": 2.0, "scale": 50.0},
}


def evaluate_single_dataset(
    tfm: Any,
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
) -> Optional[Dict[str, Any]]:
    """Evaluates TimesFM on one dataset using batched GPU prediction and emitter pulse masking."""
    if not dataset_dir.exists():
        print(f"[SKIP] Directory not found: {dataset_dir}")
        return None

    try:
        test_seqs = load_dataset_sequences(
            dataset_dir,
            split="test",
            max_seqs=max_test_seqs,
            target_param=target_param,
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
            ctx = ctx_vals[:context_len]
            gt = tgt_vals[context_len : context_len + horizon_len]
            mask = mask_vals[context_len : context_len + horizon_len]
            valid_items.append((seq_id, ctx, gt, mask))

    if not valid_items:
        print(f"[SKIP] No sequences meet required length ({required_len}) in {dataset_display}")
        return None

    contexts = [item[1] for item in valid_items]
    try:
        outputs = list(tfm.predict_batch(contexts=contexts, horizon=horizon_len))
    except Exception as e:
        print(f"[ERROR] Batch inference failed for {dataset_display}: {e}")
        return None

    mae_list, rmse_list, hit_rate_list = [], [], []

    for idx, (seq_id, ctx, gt, mask) in enumerate(valid_items):
        preds = np.asarray(outputs[idx].forecast, dtype=np.float32).squeeze()[:horizon_len]
        metrics = compute_forecast_metrics(preds, gt, tolerance=tolerance, mask=mask, unit=unit)

        mae_list.append(metrics["mae"])
        rmse_list.append(metrics["rmse"])
        hit_rate_list.append(metrics["hit_rate_pct"])

        # Diagnostic plot for the first sequence
        if plots_dir is not None and idx == 0:
            plots_dir.mkdir(parents=True, exist_ok=True)
            plot_path = plots_dir / f"{radar_type}_{error_level}.png"
            title = f"TimesFM 3.0 {param_display_name} Forecast | {dataset_display} ({seq_id})"
            save_forecast_plot(
                plot_path=plot_path,
                title=title,
                context=ctx,
                ground_truth=gt,
                predictions=preds,
                tolerance=tolerance,
                param_label=param_display_name,
                unit=unit,
            )

    mean_mae = float(np.mean(mae_list))
    mean_rmse = float(np.mean(rmse_list))
    mean_hit_rate = float(np.mean(hit_rate_list))

    print(
        f"[EVAL] {dataset_display:32s} | "
        f"Seqs: {len(mae_list):3d} | "
        f"MAE: {mean_mae:7.2f} {unit} | "
        f"RMSE: {mean_rmse:7.2f} {unit} | "
        f"Hit Rate (±{tolerance:g}{unit}): {mean_hit_rate:5.1f}%"
    )

    return {
        "radar_type": radar_type,
        "error_level": error_level,
        "parameter": target_param,
        "evaluated_sequences": len(mae_list),
        "context_length": context_len,
        "horizon_length": horizon_len,
        f"mae_{unit}": round(mean_mae, 3),
        f"rmse_{unit}": round(mean_rmse, 3),
        "gate_hit_rate_pct": round(mean_hit_rate, 2),
        "tolerance": tolerance,
        "unit": unit,
    }


def export_benchmark_results(
    results: List[Dict[str, Any]],
    results_dir: Path,
    title: str,
    unit: str = "us",
):
    """Saves metrics CSV and readable report Markdown."""
    results_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(results)

    csv_path = results_dir / "metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n[SAVED] Metrics CSV: {csv_path}")

    mae_col = f"mae_{unit}" if f"mae_{unit}" in results[0] else "mae_us"
    rmse_col = f"rmse_{unit}" if f"rmse_{unit}" in results[0] else "rmse_us"
    tol_val = results[0].get("tolerance", 10.0)

    md_path = results_dir / "report.md"
    md_content = [
        f"# {title}\n",
        f"**Evaluated on**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"**Context History**: {results[0]['context_length']} pulses | **Forecast Horizon**: {results[0]['horizon_length']} pulses\n",
        f"\n| Radar Type | Error Level | Seqs | MAE ({unit}) | RMSE ({unit}) | Gate Hit Rate (+/-{tol_val:g}{unit}) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in results:
        md_content.append(
            f"| `{r['radar_type']}` | `{r['error_level']}` | {r['evaluated_sequences']} | "
            f"**{r[mae_col]:.2f}** | {r[rmse_col]:.2f} | {r['gate_hit_rate_pct']:.1f}% |"
        )
    md_path.write_text("\n".join(md_content), encoding="utf-8")
    print(f"[SAVED] Report Markdown: {md_path}")


def main():
    parser = argparse.ArgumentParser(description="PULSAR: TimesFM 3.0 Evaluation Suite")
    parser.add_argument("--profile-mode", choices=["fixed", "varying"], default="fixed")
    parser.add_argument("--modality", choices=["univariate", "multivariate"], default="univariate")
    parser.add_argument("--target-param", "--target-col", dest="target_param", choices=list(PARAM_SPECS.keys()) + ["Measured_Delta_TOA"], default="PRI", help="Target PDW parameter")
    parser.add_argument("--radar-type", choices=["stable", "jitter", "stagger", "dwell_and_switch", "sliding", "all"], default="all")
    parser.add_argument("--error-level", choices=["clean", "error_lv1", "error_lv2", "error_lv3", "all"], default="all")
    parser.add_argument("--weights-dir", type=Path, default=None, help="Path to fine-tuned LoRA checkpoint directory")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--tolerance", type=float, default=None, help="Tactical acceptance tolerance corridor")
    parser.add_argument("--tolerance-us", type=float, default=None, help="Deprecated alias for --tolerance")
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--no-plots", action="store_true")

    args = parser.parse_args()

    # Map parameter specifications
    param_key = "PRI" if args.target_param == "Measured_Delta_TOA" else args.target_param
    spec = PARAM_SPECS.get(param_key, {"name": param_key, "slug": param_key.lower(), "unit": "units", "default_tol": 1.0, "scale": 1.0})

    param_name = spec["name"]
    param_unit = spec["unit"]
    param_slug = spec["slug"]
    tolerance = args.tolerance or args.tolerance_us or spec["default_tol"]

    regime = "lora_sft" if args.weights_dir is not None else "zero_shot"
    if args.results_dir is None:
        target_dir = PROJECT_ROOT / "results" / "timesfm_3.0" / regime / f"{args.modality}_{args.profile_mode}" / param_slug
    else:
        target_dir = args.results_dir

    plots_dir = None if args.no_plots else target_dir / "plots"

    radar_types = ["stable", "jitter", "stagger", "dwell_and_switch", "sliding"] if args.radar_type == "all" else [args.radar_type]
    error_levels = ["clean", "error_lv1", "error_lv2", "error_lv3"] if args.error_level == "all" else [args.error_level]

    # Load Model (with LoRA fused if weights_dir provided)
    tfm = TimesFMLoRAEngine.load_for_inference(weights_dir=args.weights_dir)

    print("\n" + "=" * 70)
    print(f"Beginning Evaluation [{regime.upper()}] for {param_name} ({param_key}) across {len(radar_types) * len(error_levels)} Datasets...")
    print(f"Target Directory: {target_dir}")
    print(f"Context: {args.context_len} pulses | Horizon: {args.horizon} pulses | Tolerance: ±{tolerance:g} {param_unit}")
    print("=" * 70 + "\n")

    start_time = time.time()
    results = []

    for rtype in radar_types:
        for elevel in error_levels:
            folder_name = f"1000x128_{elevel}"
            dataset_dir = DEFAULT_DATASETS_ROOT / args.profile_mode / rtype / folder_name
            dataset_display = f"{rtype}/{folder_name}"

            res = evaluate_single_dataset(
                tfm=tfm,
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
            )
            if res:
                results.append(res)

    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"Evaluation Complete in {total_time:.1f}s ({total_time / 60:.1f} min)")
    print("=" * 70)

    if results:
        title = f"TimesFM 3.0 {'LoRA Fine-Tuned (SFT)' if regime == 'lora_sft' else 'Zero-Shot'} Benchmark Report [{param_name} {args.profile_mode.capitalize()}]"
        export_benchmark_results(results, target_dir, title=title, unit=param_unit)


if __name__ == "__main__":
    main()
