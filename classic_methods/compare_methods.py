#!/usr/bin/env python3
"""Aggregates benchmark results and renders teammate-compatible forecast plots & comparison charts."""

from __future__ import annotations

from pathlib import Path
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.common import (
    DEFAULT_DATASETS_ROOT,
    ERROR_LEVELS,
    PARAM_SPECS,
    RADAR_TYPES,
    load_dataset_sequences,
    save_forecast_plot,
)
from classic_methods.rolling_median import rolling_median_forecast
from classic_methods.period_estimation import period_estimation_forecast
from classic_methods.hidden_markov_model import hmm_forecast

RESULTS_ROOT = PROJECT_ROOT / "results" / "classic_methods"


def generate_all_diagnostic_plots(
    profile_mode: str = "fixed",
    target_param: str = "PRI",
    context_len: int = 96,
    horizon_len: int = 32,
) -> None:
    """Generates the 20 standard teammate-style PNG plots per method + 20 3-way overlay plots."""
    spec = PARAM_SPECS[target_param]
    param_slug = spec["slug"]
    unit = "μs" if spec["unit"] == "us" else spec["unit"]
    tolerance = spec["default_tol"]

    methods = [
        ("rolling_median", "Rolling Median (W=32)", rolling_median_forecast),
        ("period_estimation", "Period Estimation (P_max=24)", period_estimation_forecast),
        ("hidden_markov_model", "Hidden Markov Model (Baum-Welch + Viterbi)", hmm_forecast),
    ]

    overlay_dir = RESULTS_ROOT / "plots_comparison" / f"{profile_mode}_{param_slug}"
    overlay_dir.mkdir(parents=True, exist_ok=True)

    for rtype in RADAR_TYPES:
        for elevel in ERROR_LEVELS:
            folder_name = f"1000x128_{elevel}"
            dataset_dir = DEFAULT_DATASETS_ROOT / profile_mode / rtype / folder_name
            if not dataset_dir.exists():
                continue

            seqs = load_dataset_sequences(dataset_dir, split="test", max_seqs=1, target_param=target_param)
            if not seqs:
                continue

            seq_id, ctx_vals, tgt_vals, _ = seqs[0]
            if len(ctx_vals) >= context_len + horizon_len:
                ctx = ctx_vals[:context_len]
                gt = tgt_vals[context_len : context_len + horizon_len]
            else:
                split_idx = len(ctx_vals) - horizon_len
                ctx = ctx_vals[:split_idx]
                gt = tgt_vals[split_idx : split_idx + horizon_len]

            preds_dict = {}
            for slug, label, fn in methods:
                preds = fn(ctx, horizon_len, target_param)
                preds_dict[slug] = (label, preds)

                # 1. Teammate-format individual plot: results/classic_methods/<slug>/fixed_pri/plots/<rtype>_<elevel>.png
                indiv_plot_path = RESULTS_ROOT / slug / f"{profile_mode}_{param_slug}" / "plots" / f"{rtype}_{elevel}.png"
                title = f"{label} {spec['name']} Forecast | {rtype}/{folder_name} ({seq_id})"
                save_forecast_plot(
                    plot_path=indiv_plot_path,
                    title=title,
                    context=ctx,
                    ground_truth=gt,
                    predictions=preds,
                    tolerance=tolerance,
                    param_label=spec["name"],
                    unit=unit,
                )

            # 2. Combined 3-Method Overlay Plot for easy thesis comparison
            show_ctx_pts = min(40, len(ctx))
            x_ctx = np.arange(len(ctx) - show_ctx_pts, len(ctx))
            x_horiz = np.arange(len(ctx), len(ctx) + len(gt))

            plt.figure(figsize=(13, 5.2))
            plt.plot(x_ctx, ctx[-show_ctx_pts:], "o-", color="tab:blue", markersize=4, label=f"Observed Context ({spec['name']})")
            plt.plot(x_horiz, gt, "s-", color="tab:green", markersize=4.5, linewidth=2.0, label="Ground Truth (Actual Future)")
            plt.plot(x_horiz, preds_dict["rolling_median"][1], "v:", color="tab:orange", markersize=4.5, label="Rolling Median")
            plt.plot(x_horiz, preds_dict["period_estimation"][1], "^--", color="tab:red", markersize=5, label="Period Estimation")
            plt.plot(x_horiz, preds_dict["hidden_markov_model"][1], "d-.", color="tab:purple", markersize=4.5, label="Hidden Markov Model")

            plt.axvline(x=len(ctx) - 0.5, color="black", linestyle="--", alpha=0.6, label="Forecast Horizon Boundary")
            plt.fill_between(x_horiz, gt - tolerance, gt + tolerance, color="tab:green", alpha=0.15, label=f"Tactical Gate (±{tolerance:g} {unit})")

            all_vis = np.concatenate([ctx[-show_ctx_pts:], gt, preds_dict["rolling_median"][1], preds_dict["period_estimation"][1], preds_dict["hidden_markov_model"][1]])
            y_min, y_max = float(all_vis.min()), float(all_vis.max())
            min_span = max(tolerance * 3.0, 1.0)
            if (y_max - y_min) < min_span:
                y_center = (y_max + y_min) / 2.0
                plt.ylim(y_center - min_span * 0.6, y_center + min_span * 0.6)

            plt.title(f"Classic Methods Comparison | {rtype}/{folder_name} ({seq_id})", fontsize=13, fontweight="bold")
            plt.xlabel("Pulse Index (n)")
            plt.ylabel(f"{spec['name']} ({unit})")
            plt.legend(loc="upper right", frameon=True, ncol=2, fontsize=9)
            plt.grid(True, linestyle=":", alpha=0.6)
            plt.tight_layout()
            plt.savefig(overlay_dir / f"{rtype}_{elevel}.png", dpi=180)
            plt.close()

    print(f"[SAVED] 60 Teammate-format individual forecast PNGs in results/classic_methods/<method>/{profile_mode}_{param_slug}/plots/")
    print(f"[SAVED] 20 3-Method Overlay comparison PNGs in {overlay_dir}")


def generate_comparison_report(profile_mode: str = "fixed", param_slug: str = "pri", unit: str = "us") -> None:
    methods = [
        ("rolling_median", "Rolling Median"),
        ("period_estimation", "Period Estimation"),
        ("hidden_markov_model", "Hidden Markov Model"),
    ]

    dfs = {}
    for slug, label in methods:
        csv_path = RESULTS_ROOT / slug / f"{profile_mode}_{param_slug}" / "metrics.csv"
        if csv_path.exists():
            dfs[slug] = pd.read_csv(csv_path)

    if len(dfs) < 3:
        print(f"[WARN] Not all 3 method CSVs found yet ({list(dfs.keys())}).")
        return

    rm_df = dfs["rolling_median"]
    merged = rm_df[["radar_type", "error_level", "evaluated_sequences"]].copy()
    for slug, prefix in [("rolling_median", "rm"), ("period_estimation", "pe"), ("hidden_markov_model", "hmm")]:
        df = dfs[slug]
        merged[f"{prefix}_rmse"] = df[f"rmse_{unit}"]
        merged[f"{prefix}_mae"] = df[f"mae_{unit}"]
        merged[f"{prefix}_mape"] = df["mape_pct"]
        merged[f"{prefix}_hit"] = df["gate_hit_rate_pct"]
        merged[f"{prefix}_lat"] = df["latency_us_per_seq"]

    out_csv = RESULTS_ROOT / f"comparison_{profile_mode}_{param_slug}.csv"
    merged.to_csv(out_csv, index=False)

    # Render summary bar chart (RMSE & Gate Hit Rate by Radar Type & Error Level)
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    labels = [f"{r['radar_type']}\n({r['error_level']})" for _, r in merged.iterrows()]
    x = np.arange(len(labels))
    w = 0.27

    axes[0].bar(x - w, merged["rm_rmse"], width=w, label="Rolling Median", color="tab:orange")
    axes[0].bar(x, merged["pe_rmse"], width=w, label="Period Estimation", color="tab:red")
    axes[0].bar(x + w, merged["hmm_rmse"], width=w, label="Hidden Markov Model", color="tab:purple")
    axes[0].set_title("RMSE by Radar Type & Error Level (Lower is Better)", fontweight="bold")
    axes[0].set_ylabel(f"RMSE ({unit})")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, rotation=75, fontsize=7.5)
    axes[0].legend()
    axes[0].grid(axis="y", linestyle=":", alpha=0.6)

    axes[1].bar(x - w, merged["rm_hit"], width=w, label="Rolling Median", color="tab:orange")
    axes[1].bar(x, merged["pe_hit"], width=w, label="Period Estimation", color="tab:red")
    axes[1].bar(x + w, merged["hmm_hit"], width=w, label="Hidden Markov Model", color="tab:purple")
    axes[1].set_title("Tactical Gate Hit Rate (±10 μs) (Higher is Better)", fontweight="bold")
    axes[1].set_ylabel("Hit Rate (%)")
    axes[1].set_ylim(0, 108)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=75, fontsize=7.5)
    axes[1].legend()
    axes[1].grid(axis="y", linestyle=":", alpha=0.6)

    plt.tight_layout()
    summary_plot_path = RESULTS_ROOT / "plots_comparison" / f"{profile_mode}_{param_slug}" / "summary_metrics_bar_chart.png"
    summary_plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(summary_plot_path, dpi=180)
    plt.close()

    md_lines = [
        f"# Classic Methods Side-by-Side Comparison [{param_slug.upper()} - {profile_mode.capitalize()}]",
        "",
        "## 1. Root Mean Squared Error (RMSE) & Mean Absolute Error (MAE)",
        "",
        f"| Radar Type | Error Level | Rolling Median RMSE ({unit}) | Period Est. RMSE ({unit}) | HMM RMSE ({unit}) | Rolling Median MAE ({unit}) | Period Est. MAE ({unit}) | HMM MAE ({unit}) |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in merged.iterrows():
        md_lines.append(
            f"| `{r['radar_type']}` | `{r['error_level']}` | "
            f"{r['rm_rmse']:.2f} | {r['pe_rmse']:.2f} | {r['hmm_rmse']:.2f} | "
            f"{r['rm_mae']:.2f} | {r['pe_mae']:.2f} | {r['hmm_mae']:.2f} |"
        )

    md_lines.extend([
        "",
        "## 2. Tactical Gate Hit Rate (+/-10 us) & Inference Latency",
        "",
        "| Radar Type | Error Level | Rolling Median Hit Rate | Period Est. Hit Rate | HMM Hit Rate | Rolling Median Latency (us) | Period Est. Latency (us) | HMM Latency (us) |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ])
    for _, r in merged.iterrows():
        md_lines.append(
            f"| `{r['radar_type']}` | `{r['error_level']}` | "
            f"{r['rm_hit']:.1f}% | {r['pe_hit']:.1f}% | {r['hmm_hit']:.1f}% | "
            f"{r['rm_lat']:.1f} | {r['pe_lat']:.1f} | {r['hmm_lat']:.1f} |"
        )

    out_md = RESULTS_ROOT / f"comparison_{profile_mode}_{param_slug}.md"
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"[SAVED] Unified Comparison CSV: {out_csv}")
    print(f"[SAVED] Unified Comparison Markdown: {out_md}")
    print(f"[SAVED] Summary Bar Chart: {summary_plot_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate Classic Methods Comparison Reports & Plots")
    parser.add_argument("--profile-mode", choices=["fixed", "varying", "both"], default="both")
    parser.add_argument("--target-param", choices=list(PARAM_SPECS.keys()), default="PRI")
    args = parser.parse_args()

    modes = ["fixed", "varying"] if args.profile_mode == "both" else [args.profile_mode]
    spec = PARAM_SPECS[args.target_param]
    for mode in modes:
        generate_all_diagnostic_plots(profile_mode=mode, target_param=args.target_param)
        generate_comparison_report(profile_mode=mode, param_slug=spec["slug"], unit=spec["unit"])
