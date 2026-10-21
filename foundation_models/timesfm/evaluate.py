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


def evaluate_single_dataset(
    tfm: Any,
    dataset_dir: Path,
    dataset_display: str,
    radar_type: str,
    error_level: str,
    context_len: int,
    horizon_len: int,
    max_test_seqs: Optional[int],
    tolerance_us: float,
    plots_dir: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Evaluates TimesFM on one dataset using batched GPU prediction."""
    if not dataset_dir.exists():
        print(f"[SKIP] Directory not found: {dataset_dir}")
        return None

    try:
        test_seqs = load_dataset_sequences(dataset_dir, split="test", max_seqs=max_test_seqs)
    except Exception as e:
        print(f"[ERROR] Failed to load {dataset_display}: {e}")
        return None

    if not test_seqs:
        print(f"[SKIP] No test sequences in {dataset_display}")
        return None

    valid_items = []
    required_len = context_len + horizon_len
    for seq_id, pri in test_seqs:
        if len(pri) >= required_len:
            ctx = pri[:context_len]
            gt = pri[context_len : context_len + horizon_len]
            valid_items.append((seq_id, ctx, gt))

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

    for idx, (seq_id, ctx, gt) in enumerate(valid_items):
        preds = np.asarray(outputs[idx].forecast, dtype=np.float32).squeeze()[:horizon_len]
        metrics = compute_forecast_metrics(preds, gt, tolerance_us=tolerance_us)

        mae_list.append(metrics["mae_us"])
        rmse_list.append(metrics["rmse_us"])
        hit_rate_list.append(metrics["hit_rate_pct"])

        # Diagnostic plot for the first sequence
        if plots_dir is not None and idx == 0:
            plots_dir.mkdir(parents=True, exist_ok=True)
            plot_path = plots_dir / f"{radar_type}_{error_level}.png"
            title = f"TimesFM 3.0 PRI Forecast | {dataset_display} ({seq_id})"
            save_forecast_plot(
                plot_path=plot_path,
                title=title,
                context=ctx,
                ground_truth=gt,
                predictions=preds,
                tolerance_us=tolerance_us,
            )

    mean_mae = float(np.mean(mae_list))
    mean_rmse = float(np.mean(rmse_list))
    mean_hit_rate = float(np.mean(hit_rate_list))

    print(
        f"[EVAL] {dataset_display:32s} | "
        f"Seqs: {len(mae_list):3d} | "
        f"MAE: {mean_mae:7.2f} us | "
        f"RMSE: {mean_rmse:7.2f} us | "
        f"Hit Rate (±{tolerance_us:.0f}us): {mean_hit_rate:5.1f}%"
    )

    return {
        "radar_type": radar_type,
        "error_level": error_level,
        "evaluated_sequences": len(mae_list),
        "context_length": context_len,
        "horizon_length": horizon_len,
        "mae_us": round(mean_mae, 3),
        "rmse_us": round(mean_rmse, 3),
        "gate_hit_rate_pct": round(mean_hit_rate, 2),
    }


def export_benchmark_results(results: List[Dict[str, Any]], results_dir: Path, title: str):
    """Saves metrics CSV and readable report Markdown."""
    results_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(results)

    csv_path = results_dir / "metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n[SAVED] Metrics CSV: {csv_path}")

    md_path = results_dir / "report.md"
    md_content = [
        f"# {title}\n",
        f"**Evaluated on**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"**Context History**: {results[0]['context_length']} pulses | **Forecast Horizon**: {results[0]['horizon_length']} pulses\n",
        "\n| Radar Type | Error Level | Seqs | MAE (us) | RMSE (us) | Gate Hit Rate (+/-10us) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in results:
        md_content.append(
            f"| `{r['radar_type']}` | `{r['error_level']}` | {r['evaluated_sequences']} | "
            f"**{r['mae_us']:.2f}** | {r['rmse_us']:.2f} | {r['gate_hit_rate_pct']:.1f}% |"
        )
    md_path.write_text("\n".join(md_content), encoding="utf-8")
    print(f"[SAVED] Report Markdown: {md_path}")


def main():
    parser = argparse.ArgumentParser(description="PULSAR: TimesFM 3.0 Evaluation Suite")
    parser.add_argument("--profile-mode", choices=["fixed", "varying"], default="fixed")
    parser.add_argument("--modality", choices=["univariate", "multivariate"], default="univariate")
    parser.add_argument("--radar-type", choices=["stable", "jitter", "stagger", "dwell_and_switch", "sliding", "all"], default="all")
    parser.add_argument("--error-level", choices=["clean", "error_lv1", "error_lv2", "error_lv3", "all"], default="all")
    parser.add_argument("--weights-dir", type=Path, default=None, help="Path to fine-tuned LoRA checkpoint directory")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--tolerance-us", type=float, default=10.0)
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--no-plots", action="store_true")

    args = parser.parse_args()

    regime = "lora_sft" if args.weights_dir is not None else "zero_shot"
    if args.results_dir is None:
        target_dir = PROJECT_ROOT / "results" / "timesfm_3.0" / regime / f"{args.modality}_{args.profile_mode}"
    else:
        target_dir = args.results_dir

    plots_dir = None if args.no_plots else target_dir / "plots"

    radar_types = ["stable", "jitter", "stagger", "dwell_and_switch", "sliding"] if args.radar_type == "all" else [args.radar_type]
    error_levels = ["clean", "error_lv1", "error_lv2", "error_lv3"] if args.error_level == "all" else [args.error_level]

    # Load Model (with LoRA fused if weights_dir provided)
    tfm = TimesFMLoRAEngine.load_for_inference(weights_dir=args.weights_dir)

    print("\n" + "=" * 70)
    print(f"Beginning Evaluation [{regime.upper()}] across {len(radar_types) * len(error_levels)} Datasets...")
    print(f"Target Directory: {target_dir}")
    print(f"Context: {args.context_len} pulses | Horizon: {args.horizon} pulses")
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
                tolerance_us=args.tolerance_us,
                plots_dir=plots_dir,
            )
            if res:
                results.append(res)

    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"Evaluation Complete in {total_time:.1f}s ({total_time / 60:.1f} min)")
    print("=" * 70)

    if results:
        title = f"TimesFM 3.0 {'LoRA Fine-Tuned (SFT)' if regime == 'lora_sft' else 'Zero-Shot'} Benchmark Report"
        export_benchmark_results(results, target_dir, title=title)


if __name__ == "__main__":
    main()

