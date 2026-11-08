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
from classic_methods.kalman_filter import kalman_forecast
from classic_methods.exponential_smoothing import exponential_smoothing_forecast
from classic_methods.arima import arima_forecast

RESULTS_ROOT = PROJECT_ROOT / "results" / "classic"

# (slug, plot label, short table label, forecast fn, colour, marker style)
METHODS = [
    ("rolling_median", "Rolling Median (W=32)", "Rolling Median", rolling_median_forecast, "tab:orange", "v:"),
    ("period_estimation", "Period Estimation (P_max=24)", "Period Est.", period_estimation_forecast, "tab:red", "^--"),
    ("hidden_markov_model", "Hidden Markov Model (Baum-Welch + Viterbi)", "HMM", hmm_forecast, "tab:purple", "d-."),
    ("kalman_filter", "Kalman Filter Bank", "Kalman", kalman_forecast, "tab:blue", "o--"),
    ("exponential_smoothing", "Exponential Smoothing (AICc-selected ETS)", "Exp. Smoothing", exponential_smoothing_forecast, "tab:brown", "x-."),
    ("arima", "ARIMA (Box-Jenkins, AIC-selected)", "ARIMA", arima_forecast, "tab:cyan", "*:"),
]


def generate_all_diagnostic_plots(
    profile_mode: str = "fixed",
    target_param: str = "PRI",
    context_len: int = 96,
    horizon_len: int = 32,
) -> None:
    """Generates the 20 standard teammate-style PNG plots per method + 20 all-method overlay plots."""
    spec = PARAM_SPECS[target_param]
    param_slug = spec["slug"]
    unit = "μs" if spec["unit"] == "us" else spec["unit"]
    tolerance = spec["default_tol"]

    methods = [(slug, label, fn) for slug, label, _, fn, _, _ in METHODS]

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

            # 2. Combined all-method overlay plot for easy thesis comparison
            show_ctx_pts = min(40, len(ctx))
            x_ctx = np.arange(len(ctx) - show_ctx_pts, len(ctx))
            x_horiz = np.arange(len(ctx), len(ctx) + len(gt))

            plt.figure(figsize=(13, 5.2))
            plt.plot(x_ctx, ctx[-show_ctx_pts:], "o-", color="tab:blue", markersize=4, label=f"Observed Context ({spec['name']})")
            plt.plot(x_horiz, gt, "s-", color="tab:green", markersize=4.5, linewidth=2.0, label="Ground Truth (Actual Future)")
            for slug, _, short, _, color, style in METHODS:
                plt.plot(x_horiz, preds_dict[slug][1], style, color=color, markersize=4.5, label=short)

            plt.axvline(x=len(ctx) - 0.5, color="black", linestyle="--", alpha=0.6, label="Forecast Horizon Boundary")
            plt.fill_between(x_horiz, gt - tolerance, gt + tolerance, color="tab:green", alpha=0.15, label=f"Tactical Gate (±{tolerance:g} {unit})")

            all_vis = np.concatenate([ctx[-show_ctx_pts:], gt] + [preds_dict[slug][1] for slug, *_ in METHODS])
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

    print(f"[SAVED] {20 * len(METHODS)} Teammate-format individual forecast PNGs in results/classic_methods/<method>/{profile_mode}_{param_slug}/plots/")
    print(f"[SAVED] 20 {len(METHODS)}-Method Overlay comparison PNGs in {overlay_dir}")


def generate_comparison_report(profile_mode: str = "fixed", param_slug: str = "pri", unit: str = "us") -> None:
    dfs = {}
    for slug, *_ in METHODS:
        csv_path = RESULTS_ROOT / slug / f"{profile_mode}_{param_slug}" / "metrics.csv"
        if csv_path.exists():
            dfs[slug] = pd.read_csv(csv_path)

    if len(dfs) < len(METHODS):
        print(f"[WARN] Not all {len(METHODS)} method CSVs found yet ({list(dfs.keys())}).")
        return

    keys = ["radar_type", "error_level"]
    merged = dfs[METHODS[0][0]][keys + ["evaluated_sequences"]].copy()
    for slug, *_ in METHODS:
        df = dfs[slug].set_index(keys)
        idx = merged.set_index(keys).index
        merged[f"{slug}_rmse"] = df.loc[idx, f"rmse_{unit}"].to_numpy()
        merged[f"{slug}_mae"] = df.loc[idx, f"mae_{unit}"].to_numpy()
        merged[f"{slug}_mape"] = df.loc[idx, "mape_pct"].to_numpy()
        merged[f"{slug}_hit"] = df.loc[idx, "gate_hit_rate_pct"].to_numpy()
        merged[f"{slug}_lat"] = df.loc[idx, "latency_us_per_seq"].to_numpy()

    out_csv = RESULTS_ROOT / f"comparison_{profile_mode}_{param_slug}.csv"
    merged.to_csv(out_csv, index=False)

    # Render summary bar chart (RMSE & Gate Hit Rate by Radar Type & Error Level)
    fig, axes = plt.subplots(2, 1, figsize=(17, 10))
    labels = [f"{r['radar_type']}\n({r['error_level']})" for _, r in merged.iterrows()]
    x = np.arange(len(labels))
    w = 0.8 / len(METHODS)
    for i, (slug, _, short, _, color, _) in enumerate(METHODS):
        off = (i - (len(METHODS) - 1) / 2) * w
        axes[0].bar(x + off, merged[f"{slug}_rmse"], width=w, label=short, color=color)
        axes[1].bar(x + off, merged[f"{slug}_hit"], width=w, label=short, color=color)

    axes[0].set_title("RMSE by Radar Type & Error Level (Lower is Better)", fontweight="bold")
    axes[0].set_ylabel(f"RMSE ({unit})")
    axes[1].set_title("Tactical Gate Hit Rate (±10 μs) (Higher is Better)", fontweight="bold")
    axes[1].set_ylabel("Hit Rate (%)")
    axes[1].set_ylim(0, 108)
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=75, fontsize=7.5)
        ax.legend(ncol=len(METHODS), fontsize=8)
        ax.grid(axis="y", linestyle=":", alpha=0.6)

    plt.tight_layout()
    summary_plot_path = RESULTS_ROOT / "plots_comparison" / f"{profile_mode}_{param_slug}" / "summary_metrics_bar_chart.png"
    summary_plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(summary_plot_path, dpi=180)
    plt.close()

    shorts = [short for _, _, short, *_ in METHODS]
    slugs = [slug for slug, *_ in METHODS]
    sep = "|---|---|" + "---:|" * len(METHODS)

    def table(metric: str, fmt: str, best: str) -> list:
        rows = []
        for _, r in merged.iterrows():
            vals = [r[f"{s}_{metric}"] for s in slugs]
            target = min(vals) if best == "min" else max(vals)
            cells = [f"**{format(v, fmt)}**" if np.isclose(v, target) else format(v, fmt) for v in vals]
            rows.append(f"| `{r['radar_type']}` | `{r['error_level']}` | " + " | ".join(cells) + " |")
        return rows

    head = "| Radar Type | Error Level | " + " | ".join(shorts) + " |"
    n_seq = int(merged["evaluated_sequences"].max())
    md_lines = [
        f"# Classic Methods Side-by-Side Comparison [{param_slug.upper()} - {profile_mode.capitalize()}]",
        "",
        f"All methods evaluated on the same {n_seq} test sequences per dataset "
        "(context = 96 pulses, horizon = 32 pulses). Best value per row in **bold**.",
        "",
        f"## 1. Root Mean Squared Error (RMSE, {unit})",
        "",
        head,
        sep,
        *table("rmse", ".2f", "min"),
        "",
        f"## 2. Mean Absolute Error (MAE, {unit})",
        "",
        head,
        sep,
        *table("mae", ".2f", "min"),
        "",
        "## 3. Tactical Gate Hit Rate (+/-10 us, %)",
        "",
        head,
        sep,
        *table("hit", ".1f", "max"),
        "",
        "## 4. Inference Latency (us per sequence, Python, single core)",
        "",
        head,
        sep,
        *table("lat", ".0f", "min"),
    ]

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
