"""Comprehensive Evaluation Benchmark for Multi-Radar Deinterleaving Algorithms.

Evaluates:
  1. DBSCAN (Batch Offline Spatial-Spectral Clustering)
  2. SDIF (Sequential Difference Histogram on TOA)
  3. Hybrid Cascade (DBSCAN + SDIF Fallback)
  4. Online Stream (FPGA FIFO Gated Track Association)

Across 4 Noise Regimes: clean, error_lv1, error_lv2, error_lv3.
Outputs:
  - Metric CSVs and Markdown comparison leaderboards
  - Multi-panel EW diagnostic visualization plots
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .dbscan_deinterleaver import DBSCANDeinterleaver
from .sdif_deinterleaver import SDIFDeinterleaver
from .hybrid_cascade_deinterleaver import HybridCascadeDeinterleaver
from .online_stream_deinterleaver import OnlineStreamDeinterleaver
from .metrics import evaluate_clustering_quality, DeinterleavingResult

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
DEFAULT_DATASETS_DIR = PROJECT_ROOT / "datasets" / "interleaved"
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results" / "deinterleaving"

ERROR_LEVELS = ["clean", "error_lv1", "error_lv2", "error_lv3"]
ALGORITHM_CHOICES = ["dbscan", "sdif", "hybrid", "online_stream", "all"]


def get_deinterleaver(algo_name: str) -> Any:
    if algo_name == "dbscan":
        return DBSCANDeinterleaver(eps=2.0, min_samples=6, include_amplitude=True)
    elif algo_name == "sdif":
        return SDIFDeinterleaver(max_order=4, threshold_factor=0.015, min_pulses_per_train=8)
    elif algo_name == "hybrid":
        return HybridCascadeDeinterleaver(dbscan_eps=2.0, dbscan_min_samples=6, use_amplitude=True)
    elif algo_name == "online_stream":
        return OnlineStreamDeinterleaver(gate_threshold=2.5, alpha=0.15, min_confirm_pulses=5, use_amplitude=True)
    else:
        raise ValueError(f"Unknown algorithm: {algo_name}")


def plot_deinterleaving_diagnostics(
    df_pulses: pd.DataFrame,
    pred_labels: np.ndarray,
    algo_name: str,
    error_level: str,
    save_path: Path,
) -> None:
    """Generates an EW diagnostic plot (2340x900) comparing raw interleaved input,
    ground-truth emitter tracks, and predicted deinterleaving tracks.
    """
    fig, axes = plt.subplots(1, 3, figsize=(23.4, 8.5), dpi=100)
    fig.patch.set_facecolor("#121417")

    for ax in axes:
        ax.set_facecolor("#181b20")
        ax.grid(True, linestyle="--", alpha=0.25, color="#555555")
        ax.tick_params(colors="#CCCCCC", labelsize=10)
        for spine in ax.spines.values():
            spine.set_color("#444444")

    toas = df_pulses["TOA"].to_numpy() / 1000.0  # Convert to ms
    rfs = df_pulses["Frequency"].to_numpy()
    aoas = df_pulses["AOA"].to_numpy()
    true_ids = df_pulses["Radar_ID"].to_numpy()

    # Panel 1: Raw Interleaved Pulses (Spatial vs Spectral)
    scatter1 = axes[0].scatter(
        rfs, aoas, c="#4da6ff", alpha=0.7, edgecolors="none", s=25
    )
    axes[0].set_title(f"Raw Interleaved Input ({error_level})", color="#E0E0E0", fontsize=13, fontweight="bold", pad=12)
    axes[0].set_xlabel("Carrier Frequency (MHz)", color="#CCCCCC", fontsize=11)
    axes[0].set_ylabel("Angle of Arrival (deg)", color="#CCCCCC", fontsize=11)
    axes[0].set_ylim(-10, 370)

    # Panel 2: Ground Truth Emitters
    unique_true = np.unique(true_ids)
    cmap_true = matplotlib.colormaps.get_cmap("tab10")
    for idx, e_id in enumerate(unique_true):
        mask = true_ids == e_id
        axes[1].scatter(
            rfs[mask], aoas[mask], label=e_id, color=cmap_true(idx % 10), alpha=0.8, edgecolors="none", s=25
        )
    axes[1].set_title("Ground Truth Emitters", color="#E0E0E0", fontsize=13, fontweight="bold", pad=12)
    axes[1].set_xlabel("Carrier Frequency (MHz)", color="#CCCCCC", fontsize=11)
    axes[1].set_ylim(-10, 370)
    leg1 = axes[1].legend(loc="upper right", facecolor="#22252a", edgecolor="#444444", labelcolor="#FFFFFF", fontsize=9)

    # Panel 3: Deinterleaved Emitter Tracks (Algorithm Output)
    unique_pred = np.unique(pred_labels)
    cmap_pred = matplotlib.colormaps.get_cmap("Set1")
    
    for idx, c_id in enumerate(unique_pred):
        mask = pred_labels == c_id
        if c_id == -1:
            lbl = "Noise / Dropped"
            col = "#777777"
            marker = "x"
            edgecolors = None
            size = 15
        else:
            lbl = f"Track {c_id}"
            col = cmap_pred(idx % 8)
            marker = "o"
            edgecolors = "none"
            size = 25
        axes[2].scatter(
            rfs[mask], aoas[mask], label=lbl, color=col, marker=marker, alpha=0.8, edgecolors=edgecolors, s=size
        )
    axes[2].set_title(f"Deinterleaved Output: {algo_name.upper()}", color="#E0E0E0", fontsize=13, fontweight="bold", pad=12)
    axes[2].set_xlabel("Carrier Frequency (MHz)", color="#CCCCCC", fontsize=11)
    axes[2].set_ylim(-10, 370)
    leg2 = axes[2].legend(loc="upper right", facecolor="#22252a", edgecolor="#444444", labelcolor="#FFFFFF", fontsize=9)

    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=100, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close()


def evaluate_dataset(
    dataset_dir: Path,
    algorithm: Any,
    algo_name: str,
    error_level: str,
    max_sequences: int = 50,
    save_plot_first: bool = True,
    output_dir: Path = DEFAULT_RESULTS_DIR,
) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    """Evaluates a deinterleaving algorithm over test sequences in a dataset folder."""
    test_dir = dataset_dir / "test"
    if not test_dir.exists():
        raise FileNotFoundError(f"Test directory missing: {test_dir}")

    # Gather individual sequence CSVs
    seq_files = sorted(test_dir.glob("seq_*.csv"))
    if not seq_files:
        raise FileNotFoundError(f"No sequence files found in {test_dir}")

    eval_files = seq_files[:max_sequences]
    results_list: List[DeinterleavingResult] = []
    rows: List[Dict[str, Any]] = []

    for idx, sfile in enumerate(eval_files):
        df_seq = pd.read_csv(sfile)
        if df_seq.empty:
            continue

        true_labels = df_seq["Radar_ID"].to_numpy()
        pred_labels, tracks, elapsed_ms = algorithm.deinterleave(df_seq)

        res = evaluate_clustering_quality(true_labels, pred_labels, latency_ms=elapsed_ms)
        results_list.append(res)
        
        row_dict = res.to_dict()
        row_dict["sequence_id"] = sfile.stem
        rows.append(row_dict)

        # Generate diagnostic plot for sequence 0
        if idx == 0 and save_plot_first:
            plot_path = output_dir / "plots" / f"{algo_name}_{error_level}.png"
            plot_deinterleaving_diagnostics(df_seq, pred_labels, algo_name, error_level, plot_path)

    if not results_list:
        return {}, []

    # Compute macro-averages
    macro_metrics = {
        "algorithm": algo_name,
        "error_level": error_level,
        "sequences_evaluated": len(results_list),
        "cluster_purity_pct": round(float(np.mean([r.cluster_purity for r in results_list])) * 100.0, 2),
        "v_measure_pct": round(float(np.mean([r.v_measure for r in results_list])) * 100.0, 2),
        "homogeneity_pct": round(float(np.mean([r.homogeneity for r in results_list])) * 100.0, 2),
        "completeness_pct": round(float(np.mean([r.completeness for r in results_list])) * 100.0, 2),
        "ari_pct": round(float(np.mean([r.ari for r in results_list])) * 100.0, 2),
        "nmi_pct": round(float(np.mean([r.nmi for r in results_list])) * 100.0, 2),
        "track_recovery_yield_pct": round(float(np.mean([r.track_recovery_yield for r in results_list])) * 100.0, 2),
        "false_association_rate_pct": round(float(np.mean([r.false_association_rate for r in results_list])) * 100.0, 2),
        "noise_ratio_pct": round(float(np.mean([r.noise_ratio for r in results_list])) * 100.0, 2),
        "avg_latency_ms": round(float(np.mean([r.latency_ms for r in results_list])), 3),
    }

    return macro_metrics, rows


def run_benchmark(
    algorithms: List[str],
    error_levels: List[str],
    max_sequences: int = 50,
    datasets_dir: Path = DEFAULT_DATASETS_DIR,
    output_dir: Path = DEFAULT_RESULTS_DIR,
) -> pd.DataFrame:
    """Runs the full benchmark suite across all requested algorithms and error levels."""
    output_dir.mkdir(parents=True, exist_ok=True)
    macro_rows: List[Dict[str, Any]] = []

    print("=" * 80)
    print("PULSAR MULTI-RADAR DEINTERLEAVING BENCHMARK (WBS 3.3)")
    print(f"Algorithms:   {', '.join(algorithms)}")
    print(f"Error Levels: {', '.join(error_levels)}")
    print(f"Sequences:    {max_sequences} per condition")
    print("=" * 80)

    for algo_name in algorithms:
        deinterleaver = get_deinterleaver(algo_name)
        for elevel in error_levels:
            ds_folder = datasets_dir / f"5radars_1000x128_{elevel}"
            if not ds_folder.exists():
                print(f"[WARN] Dataset folder not found: {ds_folder}. Skipping...")
                continue

            print(f"\n--> Running {algo_name.upper()} on {elevel} (up to {max_sequences} seqs)...")
            macro, seq_rows = evaluate_dataset(
                dataset_dir=ds_folder,
                algorithm=deinterleaver,
                algo_name=algo_name,
                error_level=elevel,
                max_sequences=max_sequences,
                save_plot_first=True,
                output_dir=output_dir,
            )

            if macro:
                macro_rows.append(macro)
                print(f"    Purity: {macro['cluster_purity_pct']}% | ARI: {macro['ari_pct']}% | "
                      f"Yield: {macro['track_recovery_yield_pct']}% | Latency: {macro['avg_latency_ms']} ms")

                # Save per-sequence detailed CSV
                seq_df = pd.DataFrame(seq_rows)
                seq_csv = output_dir / f"details_{algo_name}_{elevel}.csv"
                seq_df.to_csv(seq_csv, index=False)

    df_summary = pd.DataFrame(macro_rows)
    summary_csv = output_dir / "deinterleaving_summary.csv"
    df_summary.to_csv(summary_csv, index=False)
    print(f"\n[SUCCESS] Benchmark summary saved to: {summary_csv}")

    # Generate Markdown Leaderboard Table
    md_leaderboard = generate_markdown_leaderboard(df_summary)
    md_path = output_dir / "deinterleaving_leaderboard.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_leaderboard)
    print(f"[SUCCESS] Markdown leaderboard saved to: {md_path}")

    return df_summary


def generate_markdown_leaderboard(df: pd.DataFrame) -> str:
    """Formats benchmark results into a clean GitHub Flavored Markdown table."""
    if df.empty:
        return "No results generated."

    lines = [
        "# PULSAR Multi-Radar Deinterleaving Benchmark Results",
        "",
        "| Algorithm | Noise Level | Purity (%) | ARI (%) | V-Measure (%) | Track Yield (%) | False Assoc (%) | Latency (ms) |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for _, row in df.iterrows():
        algo = str(row["algorithm"]).upper()
        lvl = str(row["error_level"])
        purity = f"{row['cluster_purity_pct']:.1f}%"
        ari = f"{row['ari_pct']:.1f}%"
        v_meas = f"{row['v_measure_pct']:.1f}%"
        yield_rate = f"{row['track_recovery_yield_pct']:.1f}%"
        false_assoc = f"{row['false_association_rate_pct']:.1f}%"
        lat = f"{row['avg_latency_ms']:.2f}"

        # Bold highlight top scores
        if row["cluster_purity_pct"] >= 99.0:
            purity = f"**{purity}**"
        if row["ari_pct"] >= 99.0:
            ari = f"**{ari}**"

        lines.append(
            f"| {algo} | {lvl} | {purity} | {ari} | {v_meas} | {yield_rate} | {false_assoc} | {lat} |"
        )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="PULSAR Multi-Radar Deinterleaving Evaluation")
    parser.add_argument(
        "--algorithms",
        nargs="+",
        default=["dbscan", "hybrid", "online_stream"],
        choices=ALGORITHM_CHOICES,
        help="Deinterleaving algorithms to evaluate",
    )
    parser.add_argument(
        "--error-levels",
        nargs="+",
        default=ERROR_LEVELS,
        help="Noise/error levels to test",
    )
    parser.add_argument(
        "--max-sequences",
        type=int,
        default=50,
        help="Number of test sequences to evaluate per condition (default 50, max 200)",
    )
    parser.add_argument(
        "--datasets-dir",
        type=str,
        default=str(DEFAULT_DATASETS_DIR),
        help="Directory containing interleaved datasets",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_RESULTS_DIR),
        help="Directory to save deinterleaving results and plots",
    )

    args = parser.parse_args()
    algos = ["dbscan", "sdif", "hybrid", "online_stream"] if "all" in args.algorithms else args.algorithms

    run_benchmark(
        algorithms=algos,
        error_levels=args.error_levels,
        max_sequences=args.max_sequences,
        datasets_dir=Path(args.datasets_dir),
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    main()
