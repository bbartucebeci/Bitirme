#!/usr/bin/env python3
"""Automated Zero-Shot Benchmark Evaluation Suite for Google TimesFM 3.0.

Evaluates TimesFM 3.0 on single-radar fixed-profile PDW datasets across:
- 5 Radar types: stable, jitter, stagger, dwell_and_switch, sliding
- 4 Error levels: clean, error_lv1, error_lv2, error_lv3
- Metrics: MAE (us), RMSE (us), EW Range-Gate Hit Rate (% within tolerance)
- Output formats: CSV metrics table, LaTeX thesis table, Markdown summary, diagnostic plots
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch

# Path resolution
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
DATASETS_ROOT = PROJECT_ROOT / "datasets" / "single_radar" / "fixed"
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results"

# ---------------------------------------------------------------------------
# TimesFM 3.0 Loader Helper
# ---------------------------------------------------------------------------

def load_timesfm_model(device: str = "auto"):
    """Loads TimesFM 3.0 with PyTorch backend."""
    print("=" * 70)
    print("Loading Google TimesFM 3.0 (PyTorch)...")
    
    cuda_available = torch.cuda.is_available()
    print(f"CUDA Available: {cuda_available}")
    if cuda_available:
        print(f"GPU Device: {torch.cuda.get_device_name(0)}")

    try:
        from timesfm import TimesFM3Forecaster
    except ImportError:
        try:
            from timesfm3.pytorch import TimesFM3Forecaster
        except ImportError as e:
            raise ImportError(
                "Could not import TimesFM3Forecaster. Ensure 'timesfm[torch]' is installed: "
                "pip install timesfm[torch]"
            ) from e

    tfm = TimesFM3Forecaster.from_pretrained(
        "google/timesfm-3.0-pytorch",
        per_core_batch_size=32,
    )
    print(f"TimesFM 3.0 loaded successfully on: {tfm.device}")
    print("=" * 70)
    return tfm


# ---------------------------------------------------------------------------
# Dataset Sequence Loader
# ---------------------------------------------------------------------------

def load_test_sequences(dataset_dir: Path, max_seqs: Optional[int] = None) -> List[Tuple[str, np.ndarray]]:
    """Loads sequence PRI arrays from the test split of a dataset."""
    test_dir = dataset_dir / "test"
    if not test_dir.exists():
        raise FileNotFoundError(f"Test directory not found at: {test_dir}")

    sequences = []
    
    # 1. Try reading from individual seq_XXXX.csv files
    seq_files = sorted(list(test_dir.glob("seq_*.csv")))
    if seq_files:
        if max_seqs is not None:
            seq_files = seq_files[:max_seqs]
        for f in seq_files:
            df = pd.read_csv(f)
            if "Measured_Delta_TOA" in df.columns:
                pri_arr = df["Measured_Delta_TOA"].to_numpy(dtype=np.float32)
                sequences.append((f.stem, pri_arr))
        return sequences

    # 2. Fallback to combined sequences.csv
    comb_file = test_dir / "sequences.csv"
    if comb_file.exists():
        df_all = pd.read_csv(comb_file)
        unique_ids = df_all["sequence_id"].unique()
        if max_seqs is not None:
            unique_ids = unique_ids[:max_seqs]
        for sid in unique_ids:
            df_seq = df_all[df_all["sequence_id"] == sid].sort_values("pulse_index")
            pri_arr = df_seq["Measured_Delta_TOA"].to_numpy(dtype=np.float32)
            sequences.append((sid, pri_arr))
        return sequences

    raise FileNotFoundError(f"No test sequences found in {test_dir}")


# ---------------------------------------------------------------------------
# Plotting Helper
# ---------------------------------------------------------------------------

def save_diagnostic_plot(
    plot_path: Path,
    dataset_name: str,
    sequence_id: str,
    context: np.ndarray,
    ground_truth: np.ndarray,
    predictions: np.ndarray,
):
    """Renders and saves a diagnostic forecast figure."""
    context_len = len(context)
    horizon_len = len(ground_truth)

    plt.figure(figsize=(13, 5))
    
    # Show last 40 context points for clarity
    show_ctx_pts = min(40, context_len)
    x_ctx = np.arange(context_len - show_ctx_pts, context_len)
    x_horiz = np.arange(context_len, context_len + horizon_len)

    plt.plot(x_ctx, context[-show_ctx_pts:], "o-", color="tab:blue", markersize=4, label="Observed Context (PRI)")
    plt.plot(x_horiz, ground_truth, "s-", color="tab:green", markersize=4, label="Ground Truth (Actual Future)")
    plt.plot(x_horiz, predictions, "^--", color="tab:red", markersize=5, label="TimesFM 3.0 Zero-Shot Forecast")

    plt.axvline(x=context_len - 0.5, color="black", linestyle="--", alpha=0.6, label="Forecast Horizon Boundary")
    
    # Error band
    plt.fill_between(x_horiz, ground_truth, predictions, color="tab:red", alpha=0.15, label="Prediction Error Gap")

    plt.title(f"TimesFM 3.0 Zero-Shot PRI Forecast | {dataset_name} ({sequence_id})", fontsize=13, fontweight="bold")
    plt.xlabel("Pulse Index (n)")
    plt.ylabel(r"PRI / Measured $\Delta$TOA ($\mu$s)")
    plt.legend(loc="upper right", frameon=True)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()

    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=180)
    plt.close()


# ---------------------------------------------------------------------------
# Single Dataset Evaluation Runner
# ---------------------------------------------------------------------------

def evaluate_dataset(
    tfm: Any,
    radar_type: str,
    error_level: str,
    context_len: int,
    horizon_len: int,
    max_test_seqs: Optional[int],
    tolerance_us: float,
    results_dir: Path,
    save_plot: bool = True,
) -> Optional[Dict[str, Any]]:
    """Evaluates TimesFM 3.0 on a specific radar dataset."""
    folder_name = f"1000x128_{error_level}"
    dataset_dir = DATASETS_ROOT / radar_type / folder_name
    dataset_display = f"{radar_type}/{folder_name}"

    if not dataset_dir.exists():
        print(f"[SKIP] Dataset directory not found: {dataset_dir}")
        return None

    try:
        test_seqs = load_test_sequences(dataset_dir, max_seqs=max_test_seqs)
    except Exception as e:
        print(f"[ERROR] Failed to load {dataset_display}: {e}")
        return None

    if not test_seqs:
        print(f"[SKIP] No sequences loaded for {dataset_display}")
        return None

    valid_items = []
    for seq_id, pri_series in test_seqs:
        if len(pri_series) < (context_len + horizon_len):
            continue
        context = pri_series[:context_len]
        ground_truth = pri_series[context_len : context_len + horizon_len]
        valid_items.append((seq_id, context, ground_truth))

    if not valid_items:
        print(f"[SKIP] No sequences with sufficient length in {dataset_display}")
        return None

    contexts = [item[1] for item in valid_items]
    try:
        forecast_outputs = list(tfm.predict_batch(contexts=contexts, horizon=horizon_len))
    except Exception as e:
        print(f"[ERROR] Batch inference failed for {dataset_display}: {e}")
        return None

    mae_list = []
    rmse_list = []
    hit_rate_list = []

    for idx, (seq_id, context, ground_truth) in enumerate(valid_items):
        preds = np.asarray(forecast_outputs[idx].forecast, dtype=np.float32).squeeze()[:horizon_len]
        abs_err = np.abs(preds - ground_truth)
        sq_err = (preds - ground_truth) ** 2

        mae_list.append(float(np.mean(abs_err)))
        rmse_list.append(float(np.sqrt(np.mean(sq_err))))
        hit_rate_list.append(float(np.mean(abs_err <= tolerance_us) * 100.0))

        if save_plot and idx == 0:
            plot_file = results_dir / "plots" / f"{radar_type}_{error_level}.png"
            save_diagnostic_plot(
                plot_file,
                dataset_display,
                seq_id,
                context,
                ground_truth,
                preds,
            )

    if not mae_list:
        print(f"[WARNING] No valid evaluations completed for {dataset_display}")
        return None

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


# ---------------------------------------------------------------------------
# Output Exporters (CSV, Markdown, LaTeX)
# ---------------------------------------------------------------------------

def export_results(results: List[Dict[str, Any]], results_dir: Path):
    """Saves structured results to CSV, Markdown, and LaTeX."""
    results_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(results)

    # 1. Save CSV
    csv_path = results_dir / "timesfm_zero_shot_metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n[SAVED] CSV Metrics: {csv_path}")

    # 2. Save Markdown Summary Table
    md_path = results_dir / "timesfm_zero_shot_summary.md"
    md_content = [
        "# TimesFM 3.0 Zero-Shot Benchmark Results\n",
        f"**Evaluated on**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"**Context Length**: {results[0]['context_length']} pulses | **Forecast Horizon**: {results[0]['horizon_length']} pulses\n",
        "\n| Radar Type | Error Level | Seqs | MAE (μs) | RMSE (μs) | Gate Hit Rate (±10μs) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in results:
        md_content.append(
            f"| `{r['radar_type']}` | `{r['error_level']}` | {r['evaluated_sequences']} | "
            f"**{r['mae_us']:.2f}** | {r['rmse_us']:.2f} | {r['gate_hit_rate_pct']:.1f}% |"
        )
    md_path.write_text("\n".join(md_content), encoding="utf-8")
    print(f"[SAVED] Markdown Summary: {md_path}")

    # 3. Save LaTeX Table for Thesis
    tex_path = results_dir / "timesfm_zero_shot_table.tex"
    tex_lines = [
        "% --- TimesFM 3.0 Zero-Shot Evaluation Table for PULSAR Graduation Thesis ---",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Zero-Shot TimesFM 3.0 PRI Forecasting Performance on PULSAR Benchmark}",
        "\\label{tab:timesfm_zero_shot}",
        "\\begin{tabular}{llcccc}",
        "\\hline",
        "\\textbf{Radar Type} & \\textbf{Error Level} & \\textbf{Test Seqs} & \\textbf{MAE ($\\mu$s)} & \\textbf{RMSE ($\\mu$s)} & \\textbf{Hit Rate (\\%)} \\\\",
        "\\hline",
    ]
    for r in results:
        rtype = r["radar_type"].replace("_", "\\_")
        elevel = r["error_level"].replace("_", "\\_")
        tex_lines.append(
            f"{rtype} & {elevel} & {r['evaluated_sequences']} & "
            f"{r['mae_us']:.2f} & {r['rmse_us']:.2f} & {r['gate_hit_rate_pct']:.1f}\\% \\\\"
        )
    tex_lines.extend([
        "\\hline",
        "\\end{tabular}",
        "\\end{table}",
    ])
    tex_path.write_text("\n".join(tex_lines), encoding="utf-8")
    print(f"[SAVED] LaTeX Table: {tex_path}")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="PULSAR: TimesFM 3.0 Zero-Shot Benchmark Evaluator")
    parser.add_argument(
        "--radar-type",
        choices=["stable", "jitter", "stagger", "dwell_and_switch", "sliding", "all"],
        default="all",
        help="Radar type to evaluate (default: all)",
    )
    parser.add_argument(
        "--error-level",
        choices=["clean", "error_lv1", "error_lv2", "error_lv3", "all"],
        default="all",
        help="Error level to evaluate (default: all)",
    )
    parser.add_argument(
        "--context-len",
        type=int,
        default=96,
        help="Context history window in pulses (default: 96)",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=32,
        help="Forward prediction horizon in pulses (default: 32)",
    )
    parser.add_argument(
        "--max-test-seqs",
        type=int,
        default=50,
        help="Maximum test sequences per dataset to evaluate (default: 50, use 0 or 200 for all)",
    )
    parser.add_argument(
        "--tolerance-us",
        type=float,
        default=10.0,
        help="Tolerance in microseconds for Tactical Gate Hit Rate (default: 10.0)",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="Output directory for metrics and plots",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Disable saving diagnostic forecast plots",
    )

    args = parser.parse_args()

    max_seqs = None if (args.max_test_seqs is None or args.max_test_seqs <= 0 or args.max_test_seqs >= 200) else args.max_test_seqs

    radar_types = ["stable", "jitter", "stagger", "dwell_and_switch", "sliding"] if args.radar_type == "all" else [args.radar_type]
    error_levels = ["clean", "error_lv1", "error_lv2", "error_lv3"] if args.error_level == "all" else [args.error_level]

    # Load Model
    tfm = load_timesfm_model()

    results = []
    print("\n" + "=" * 70)
    print(f"Beginning Evaluation across {len(radar_types) * len(error_levels)} Datasets...")
    print(f"Context: {args.context_len} pulses | Horizon: {args.horizon} pulses | Max Seqs/Dataset: {max_seqs or 200}")
    print("=" * 70 + "\n")

    start_time = time.time()

    for rtype in radar_types:
        for elevel in error_levels:
            res = evaluate_dataset(
                tfm=tfm,
                radar_type=rtype,
                error_level=elevel,
                context_len=args.context_len,
                horizon_len=args.horizon,
                max_test_seqs=max_seqs,
                tolerance_us=args.tolerance_us,
                results_dir=args.results_dir,
                save_plot=not args.no_plots,
            )
            if res:
                results.append(res)

    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"Evaluation Complete in {total_time:.1f}s ({total_time / 60:.1f} min)")
    print("=" * 70)

    if results:
        export_results(results, args.results_dir)


if __name__ == "__main__":
    main()

