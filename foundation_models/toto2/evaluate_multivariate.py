"""PULSAR: Toto 2.0 Joint 5-Channel Multivariate Evaluation Suite."""

from __future__ import annotations

import argparse
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

import numpy as np

from foundation_models.common.dataset import (
    load_multivariate_dataset_sequences,
    MULTIVARIATE_CHANNELS,
    MULTIVARIATE_TOLERANCES,
    MULTIVARIATE_UNITS,
)
from foundation_models.common.metrics import compute_forecast_metrics
from foundation_models.common.plotting import save_multivariate_forecast_plot
from foundation_models.toto2.adapter import Toto2Forecaster

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
DEFAULT_DATASETS_ROOT = PROJECT_ROOT / "datasets" / "single_radar"
DEFAULT_RESULTS_ROOT = PROJECT_ROOT / "results" / "toto2"


def evaluate_single_multivariate_dataset(
    model: Any,
    dataset_dir: Path,
    dataset_display: str,
    radar_type: str,
    error_level: str,
    context_len: int = 96,
    horizon_len: int = 32,
    max_test_seqs: Optional[int] = 200,
    plots_dir: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    if not dataset_dir.exists():
        print(f"[SKIP] Directory not found: {dataset_dir}")
        return None

    try:
        test_seqs = load_multivariate_dataset_sequences(
            dataset_dir, split="test", max_seqs=max_test_seqs
        )
    except Exception as e:
        print(f"[ERROR] Failed to load {dataset_display}: {e}")
        return None

    if not test_seqs:
        print(f"[SKIP] No test sequences in {dataset_display}")
        return None

    valid_items = []
    required_len = context_len + horizon_len
    for seq_id, ctx_full, tgt_full, mask_full in test_seqs:
        if ctx_full.shape[1] >= required_len:
            c = ctx_full[:, :context_len]
            t = tgt_full[:, context_len : context_len + horizon_len]
            m = mask_full[context_len : context_len + horizon_len]
            valid_items.append((seq_id, c, t, m))

    if not valid_items:
        print(f"[SKIP] No sequences meet required length ({required_len}) in {dataset_display}")
        return None

    contexts = [item[1] for item in valid_items]
    try:
        outputs = list(model.predict_batch(contexts=contexts, horizon=horizon_len))
    except Exception as e:
        print(f"[ERROR] Batch inference failed for {dataset_display}: {e}")
        return None

    channel_maes = {ch: [] for ch in MULTIVARIATE_CHANNELS}
    channel_rmses = {ch: [] for ch in MULTIVARIATE_CHANNELS}
    channel_hits = {ch: [] for ch in MULTIVARIATE_CHANNELS}

    for idx, (seq_id, ctx, gt, mask) in enumerate(valid_items):
        preds = np.asarray(outputs[idx].forecast, dtype=np.float32)
        if preds.ndim == 1:
            preds = preds.reshape(1, -1)
        preds = preds[:, :horizon_len]

        for c_idx, ch_name in enumerate(MULTIVARIATE_CHANNELS):
            ch_pred = preds[c_idx]
            ch_gt = gt[c_idx]
            ch_tol = MULTIVARIATE_TOLERANCES[c_idx]
            ch_unit = MULTIVARIATE_UNITS[c_idx]

            met = compute_forecast_metrics(
                ch_pred, ch_gt, tolerance=ch_tol, mask=mask, unit=ch_unit,
            )
            channel_maes[ch_name].append(met["mae"])
            channel_rmses[ch_name].append(met["rmse"])
            channel_hits[ch_name].append(met["hit_rate_pct"])

        if plots_dir is not None and idx == 0:
            plots_dir.mkdir(parents=True, exist_ok=True)
            plot_path = plots_dir / f"{radar_type}_{error_level}.png"
            try:
                save_multivariate_forecast_plot(
                    plot_path,
                    title=f"Toto 2.0 Joint 5-Channel Forecast | {dataset_display} ({seq_id})",
                    context_5xN=ctx,
                    ground_truth_5xN=gt,
                    predictions_5xN=preds,
                    tolerances=MULTIVARIATE_TOLERANCES,
                    param_names=MULTIVARIATE_CHANNELS,
                    units=MULTIVARIATE_UNITS,
                )
            except Exception:
                pass

    row: Dict[str, Any] = {
        "radar_type": radar_type,
        "error_level": error_level,
        "num_sequences": len(valid_items),
    }
    for ch_name in MULTIVARIATE_CHANNELS:
        slug = ch_name.lower()
        row[f"mae_{slug}"] = float(np.mean(channel_maes[ch_name]))
        row[f"rmse_{slug}"] = float(np.mean(channel_rmses[ch_name]))
        row[f"hit_rate_{slug}"] = float(np.mean(channel_hits[ch_name]))

    print(
        f"[EVAL] {dataset_display:32s} | Seqs: {len(valid_items):3d} | "
        f"PRI MAE: {row['mae_pri']:6.2f} us (Hit: {row['hit_rate_pri']:5.1f}%) | "
        f"RF MAE: {row['mae_frequency']:5.2f} MHz | "
        f"PW MAE: {row['mae_pw']:4.2f} us"
    )


def export_multivariate_benchmark_results(
    results: List[Dict[str, Any]],
    output_dir: Path,
    title: str = "Toto 2.0 Joint 5-Channel Benchmark Report",
):
    output_dir.mkdir(parents=True, exist_ok=True)
    import pandas as pd
    df = pd.DataFrame(results)

    csv_path = output_dir / "metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n[SAVED] Metrics CSV: {csv_path}")

    md_lines = [
        f"# {title}\n",
        f"**Generated on**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        "## Joint 5-Channel Forecast Metrics Summary\n",
        "| Radar Type | Error Level | PRI MAE (μs) | PRI Hit (%) | RF MAE (MHz) | RF Hit (%) | PW MAE (μs) | AOA MAE (°) | Amp MAE (dBm) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        md_lines.append(
            f"| `{r['radar_type']}` | `{r['error_level']}` | "
            f"{r['mae_pri']:.2f} | {r['hit_rate_pri']:.1f}% | "
            f"{r['mae_frequency']:.2f} | {r['hit_rate_frequency']:.1f}% | "
            f"{r['mae_pw']:.2f} | {r['mae_aoa']:.2f} | {r['mae_amplitude']:.2f} |"
        )

    md_path = output_dir / "report.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[SAVED] Report Markdown: {md_path}")


def main():
    parser = argparse.ArgumentParser(description="PULSAR: Toto 2.0 Multivariate Evaluation")
    parser.add_argument("--model-id", type=str, default="Datadog/Toto-2.0-22m")
    parser.add_argument("--profile-mode", choices=["fixed", "varying"], default="fixed")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--no-plots", action="store_true")

    args = parser.parse_args()

    regime = "zero_shot"
    if args.results_dir is None:
        target_dir = DEFAULT_RESULTS_ROOT / regime / f"multivariate_{args.profile_mode}"
    else:
        target_dir = args.results_dir

    plots_dir = None if args.no_plots else target_dir / "plots"

    radar_types = ["stable", "jitter", "stagger", "dwell_and_switch", "sliding"]
    error_levels = ["clean", "error_lv1", "error_lv2", "error_lv3"]

    model = Toto2Forecaster.load_for_inference(model_id=args.model_id)

    print("=" * 80)
    print(f"Toto 2.0 Joint 5-Channel Multivariate Evaluation [{regime.upper()}]")
    print(f"Profile: {args.profile_mode} | Context: {args.context_len} | Horizon: {args.horizon}")
    print(f"Channels: {', '.join(MULTIVARIATE_CHANNELS)}")
    print("=" * 80 + "\n")

    results = []
    t_start = time.time()

    for rtype in radar_types:
        for elevel in error_levels:
            # Discover the actual folder name
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

            res = evaluate_single_multivariate_dataset(
                model=model,
                dataset_dir=dataset_dir,
                dataset_display=dataset_display,
                radar_type=rtype,
                error_level=elevel,
                context_len=args.context_len,
                horizon_len=args.horizon,
                max_test_seqs=args.max_test_seqs,
                plots_dir=plots_dir,
            )
            if res:
                results.append(res)

    t_total = time.time() - t_start
    print("\n" + "=" * 80)
    print(f"Evaluation Complete in {t_total:.1f}s ({t_total/60:.1f} min)")
    print("=" * 80)

    if results:
        title = f"Toto 2.0 Zero-Shot Joint 5-Channel Benchmark [{args.profile_mode.capitalize()}]"
        export_multivariate_benchmark_results(results, target_dir, title=title)


if __name__ == "__main__":
    main()