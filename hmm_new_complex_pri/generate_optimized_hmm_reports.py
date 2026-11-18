#!/usr/bin/env python3
"""Aggregate Optimized HMM new_complex_pri results, run parity assertions,
build tables/plots, and generate a 3-way comparison against Baseline HMM and Chronos-2."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.common import save_forecast_plot
from dataset_generator.catalog import ERROR_LEVELS, NEW_COMPLEX_PRI, RADAR_TYPES

CONTEXTS = (96, 256, 512, 992)
RADAR_LABELS = {
    "stable": "Stable",
    "jitter": "Gaussian jitter",
    "stagger": "Stagger",
    "dwell_and_switch": "Dwell and switch",
    "sliding": "Sliding",
    "sinusoidal": "Sinusoidal",
    "triangular_sliding": "Triangular sliding",
    "markov_agile": "Markov agile",
}


def load_and_validate_raw(raw_dir: Path, expected_seqs: int = 200) -> tuple[pd.DataFrame, pd.DataFrame]:
    files = sorted(raw_dir.glob("*.csv"))
    if len(files) != 512:
        raise RuntimeError(f"Expected 512 raw condition-L CSVs in {raw_dir}, found {len(files)}")
    frames = [pd.read_csv(f) for f in files]
    df = pd.concat(frames, ignore_index=True)

    if len(df) != 512 * expected_seqs:
        raise RuntimeError(f"Expected {512 * expected_seqs} rows, got {len(df)}")
    if df[["mae_us", "rmse_us", "medae_us", "hit_rate_pct", "ctx_median_mae_us"]].isna().any().any():
        raise RuntimeError("NaN detected in raw Optimized HMM per-sequence metrics")
    if not (df["valid_pulses"] == 32).all():
        raise RuntimeError("Found sequence with valid_pulses != 32")
    if not (df["start"] == 1024 - df["context_len"]).all():
        raise RuntimeError("Boundary window assertion failed: start != 1024 - context_len")
    expected_sids = {f"seq_{i:04d}" for i in range(800, 1000)}
    for (p, r, e, L), grp in df.groupby(["profile", "radar_type", "error_level", "context_len"]):
        if len(grp) != expected_seqs or set(grp["sequence_id"]) != expected_sids:
            raise RuntimeError(f"Incomplete or mismatched sequence IDs in {p}/{r}/{e}/L{L}")

    df["cleaner_ratio"] = df["cleaned_len"] / np.maximum(df["true_source_pulses"], 1)

    agg = (
        df.groupby(["profile", "radar_type", "error_level", "context_len"], sort=False)
        .agg(
            horizon=("horizon", "first"),
            num_sequences=("sequence_id", "count"),
            valid_pulses_evaluated=("valid_pulses", "sum"),
            mae_us=("mae_us", "mean"),
            rmse_us=("rmse_us", "mean"),
            medae_mean_us=("medae_us", "mean"),
            seq_median_mae_us=("mae_us", "median"),
            mape_pct=("mape_pct", "mean"),
            hit_rate_pct=("hit_rate_pct", "mean"),
            ctx_median_mae_us=("ctx_median_mae_us", "mean"),
            ctx_last_mae_us=("ctx_last_mae_us", "mean"),
            acf_gated_frac=("acf_gated", "mean"),
            cleaner_count_ratio=("cleaner_ratio", "mean"),
            mean_latency_ms=("latency_s", lambda s: 1000.0 * float(np.mean(s))),
            total_cpu_s=("latency_s", "sum"),
        )
        .reset_index()
    )
    agg["skill_vs_median"] = np.where(
        agg["ctx_median_mae_us"] > 0,
        1.0 - agg["mae_us"] / agg["ctx_median_mae_us"],
        np.where(agg["mae_us"] == 0, 1.0, 0.0),
    )

    expected_keys = {
        (p, r, e, L)
        for p in ("fixed", "varying")
        for r in RADAR_TYPES
        for e in ERROR_LEVELS
        for L in CONTEXTS
    }
    actual_keys = {
        (row.profile, row.radar_type, row.error_level, int(row.context_len))
        for row in agg.itertuples(index=False)
    }
    missing = expected_keys - actual_keys
    if missing:
        raise RuntimeError(f"Missing {len(missing)} condition-context cells; e.g. {sorted(missing)[:5]}")

    prof_order = {"fixed": 0, "varying": 1}
    radar_order = {r: i for i, r in enumerate(RADAR_TYPES)}
    err_order = {e: i for i, e in enumerate(ERROR_LEVELS)}
    agg["_p"] = agg["profile"].map(prof_order)
    agg["_r"] = agg["radar_type"].map(radar_order)
    agg["_e"] = agg["error_level"].map(err_order)
    agg = agg.sort_values(["_p", "_r", "_e", "context_len"]).drop(columns=["_p", "_r", "_e"]).reset_index(drop=True)
    return agg, df


def _df_to_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---:" if pd.api.types.is_numeric_dtype(df[c]) else "---" for c in cols) + " |"
    rows = []
    for row in df.itertuples(index=False, name=None):
        cells = [f"{v:.4f}" if isinstance(v, float) else str(v) for v in row]
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep, *rows])


def write_mae_tables_and_pngs(agg: pd.DataFrame, out_dir: Path) -> None:
    lookup: Dict[tuple, float] = {
        (row.profile, row.radar_type, row.error_level, int(row.context_len)): float(row.mae_us)
        for row in agg.itertuples(index=False)
    }

    md_lines = [
        f"# {NEW_COMPLEX_PRI}: Optimized 1st-Order Hidden Markov Model PRI MAE Comparison",
        "",
        "Protocol: `consecutive_future_v2` (`window_mode=boundary`, `C=1024`, `H=32`, 200 test sequences per condition).",
        "L = 96, 256, 512, 992. Target = source `PRI` (µs). Lowest MAE per row is bold.",
        "",
    ]

    png_dir = out_dir / "png"
    png_dir.mkdir(parents=True, exist_ok=True)

    for profile in ("fixed", "varying"):
        rows: List[list] = []
        md_lines.extend(
            [
                f"## {profile.capitalize()} — Univariate — PRI MAE (µs)",
                "",
                "| Radar type | Error level | L=96 | L=256 | L=512 | L=992 |",
                "|---|---|---:|---:|---:|---:|",
            ]
        )
        for radar in RADAR_TYPES:
            for level in ERROR_LEVELS:
                vals = [lookup[(profile, radar, level, L)] for L in CONTEXTS]
                rows.append([radar, level, *vals])
                best = min(vals)
                cells = [f"**{v:.6f}**" if v == best else f"{v:.6f}" for v in vals]
                md_lines.append("| " + " | ".join([radar, level, *cells]) + " |")
        md_lines.append("")

        name = f"{NEW_COMPLEX_PRI}_{profile}_univariate_pri_optimized_hmm"
        with (out_dir / f"{name}.csv").open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.writer(stream)
            writer.writerow(["radar_type", "error_level", *[f"MAE_L{L}_µs" for L in CONTEXTS]])
            writer.writerows(rows)

        fig, ax = plt.subplots(figsize=(13.8, 20.8))
        ax.axis("off")
        fig.suptitle(
            f"Optimized 1st-Order HMM [{NEW_COMPLEX_PRI}]: {profile}, univariate, PRI",
            fontsize=17,
            fontweight="bold",
            x=0.04,
            ha="left",
            y=0.99,
        )
        ax.set_title(
            "MAE (µs)   H=32   200 test sequences per row   Green: lowest MAE in row",
            fontsize=11,
            loc="left",
            pad=15,
        )
        table = ax.table(
            cellText=[[r, e, *[f"{v:.6f}" for v in vals]] for r, e, *vals in rows],
            colLabels=["Radar type", "Error level", *[f"L={L}" for L in CONTEXTS]],
            colWidths=[0.24, 0.14, 0.155, 0.155, 0.155, 0.155],
            cellLoc="right",
            bbox=[0, 0, 1, 1],
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        for (i, j), cell in table.get_celld().items():
            cell.set_linewidth(0.3)
            cell.set_edgecolor("#DCE2EA")
            if i == 0:
                cell.set_facecolor("#1C304D")
                cell.set_text_props(color="white", weight="bold")
            else:
                vals = rows[i - 1][2:]
                cell.set_facecolor("#F1F5F9" if ((i - 1) // 8) % 2 else "white")
                if j < 2:
                    cell.set_text_props(ha="left")
                elif vals[j - 2] == min(vals):
                    cell.set_facecolor("#DDEEDC")
                    cell.set_text_props(weight="bold", color="#174A26")
        fig.subplots_adjust(top=0.95, bottom=0.015, left=0.04, right=0.98)
        fig.savefig(png_dir / f"{name}.png", dpi=140)
        plt.close(fig)

    (out_dir / "MAE_comparison.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")


def write_hitrate_and_rmse_tables(agg: pd.DataFrame, out_dir: Path) -> None:
    hit_lkp = {
        (r.profile, r.radar_type, r.error_level, int(r.context_len)): float(r.hit_rate_pct)
        for r in agg.itertuples(index=False)
    }
    rmse_lkp = {
        (r.profile, r.radar_type, r.error_level, int(r.context_len)): float(r.rmse_us)
        for r in agg.itertuples(index=False)
    }

    lines = [
        f"# {NEW_COMPLEX_PRI}: Optimized HMM Gate Hit Rate (±10 µs) & RMSE",
        "",
        "Each cell shows `HitRate% / RMSE(µs)` averaged across 200 test sequences (H=32).",
        "",
    ]
    for profile in ("fixed", "varying"):
        lines.extend(
            [
                f"## {profile.capitalize()} Profile",
                "",
                "| Radar type | Error level | L=96 | L=256 | L=512 | L=992 |",
                "|---|---|---:|---:|---:|---:|",
            ]
        )
        for radar in RADAR_TYPES:
            for level in ERROR_LEVELS:
                cells = [
                    f"{hit_lkp[(profile, radar, level, L)]:.1f}% / {rmse_lkp[(profile, radar, level, L)]:.2f}"
                    for L in CONTEXTS
                ]
                lines.append("| " + " | ".join([radar, level, *cells]) + " |")
        lines.append("")

    (out_dir / "HitRate_and_RMSE_tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_by_radar_reports(agg: pd.DataFrame, out_dir: Path) -> None:
    for law in RADAR_TYPES:
        data = agg[agg["radar_type"] == law].copy()
        target = out_dir / "by_radar" / law
        target.mkdir(parents=True, exist_ok=True)
        data.round(4).to_csv(target / "metrics.csv", index=False)
        lines = [
            f"# Optimized HMM Context-Length Sweep: {law}",
            "",
            "Each row is a separate profile, error level, and context length (200 test sequences, H=32).",
            "",
            _df_to_markdown(data),
            "",
        ]
        (target / "report.md").write_text("\n".join(lines), encoding="utf-8")

        for profile in ("fixed", "varying"):
            pdata = data[data["profile"] == profile]
            fig, axes = plt.subplots(2, 4, figsize=(17, 8), squeeze=False)
            for ax, level in zip(axes.flat, ERROR_LEVELS):
                sub = pdata[pdata["error_level"] == level].sort_values("context_len")
                ax.plot(sub["context_len"], sub["mae_us"], marker="o", color="#16a34a", linewidth=2, label="Optimized HMM")
                ax.plot(
                    sub["context_len"],
                    sub["ctx_median_mae_us"],
                    linestyle=":",
                    color="#64748b",
                    linewidth=1.5,
                    label="Ctx median",
                )
                ax.set_title(level)
                ax.set_xlabel("Context length L")
                ax.set_ylabel("MAE (µs)")
                ax.set_xticks(list(CONTEXTS))
                ax.grid(alpha=0.25)
                ax.legend(fontsize=8)
            fig.suptitle(
                f"Optimized HMM PRI MAE vs Context Length: {RADAR_LABELS[law]} ({profile} profile)",
                fontsize=14,
                fontweight="bold",
            )
            fig.tight_layout()
            fig.savefig(target / f"{profile}.png", dpi=130)
            plt.close(fig)


def plot_8panel_three_way(path: Path, rows: List[dict], title: str, subtitle: str) -> None:
    fig, axes = plt.subplots(2, 4, figsize=(19.2, 9.4), sharex=True)
    x = np.arange(len(ERROR_LEVELS))
    for axis, radar in zip(axes.flat, RADAR_TYPES, strict=True):
        panel = {r["error_level"]: r for r in rows if r["radar_type"] == radar}
        y_base = [panel[level]["baseline"] for level in ERROR_LEVELS]
        y_opt = [panel[level]["optimized"] for level in ERROR_LEVELS]
        y_chr = [panel[level]["chronos2"] for level in ERROR_LEVELS]
        y_med = [panel[level]["median_floor"] for level in ERROR_LEVELS]

        axis.plot(x, y_base, "o--", color="#2563eb", linewidth=1.5, markersize=4.0, alpha=0.85, label="Baseline HMM (K={1,2,3,4,6})")
        axis.plot(x, y_opt, "^-", color="#16a34a", linewidth=2.0, markersize=4.8, label="Optimized HMM (1st-order K<=6)")
        axis.plot(x, y_chr, "s-", color="#dc2626", linewidth=1.7, markersize=4.2, label="Chronos-2 Zero-Shot (Univariate PRI)")
        axis.plot(x, y_med, ":", color="#6b7280", linewidth=1.2, label="Context median floor")

        maximum = max(*y_base, *y_opt, *y_chr, *y_med)
        axis.set_ylim(0, maximum * 1.13 if maximum > 0 else 1.0)
        axis.set_xticks(x, ["Clean", *[f"Lv{i}" for i in range(1, 8)]])
        axis.tick_params(axis="both", labelsize=9)
        axis.tick_params(axis="x", labelbottom=True)
        axis.yaxis.set_major_locator(MaxNLocator(nbins=5))
        axis.ticklabel_format(axis="y", style="plain", useOffset=False)
        axis.set_title(RADAR_LABELS[radar], fontsize=12, fontweight="bold")
        axis.set_ylabel("MAE (µs)", fontsize=10)
        axis.set_xlabel("Error level", fontsize=10)
        axis.grid(axis="both", linestyle=":", alpha=0.3)

    fig.suptitle(title, fontsize=17, fontweight="bold", y=0.985)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.915),
        ncol=4,
        frameon=False,
        fontsize=10.5,
    )
    fig.text(0.5, 0.862, subtitle, ha="center", fontsize=10)
    fig.subplots_adjust(left=0.055, right=0.985, bottom=0.075, top=0.815, wspace=0.3, hspace=0.43)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def build_three_way_comparison(
    opt_agg: pd.DataFrame,
    out_dir: Path,
    baseline_dir: Path,
    chronos_mae_dir: Path,
) -> None:
    base_csv = baseline_dir / "metrics_by_condition.csv"
    if not base_csv.is_file():
        raise FileNotFoundError(f"Baseline HMM metrics not found: {base_csv}")
    base_df = pd.read_csv(base_csv)

    base_lkp = {
        (r.profile, r.radar_type, r.error_level, int(r.context_len)): r
        for r in base_df.itertuples(index=False)
    }
    opt_lkp = {
        (r.profile, r.radar_type, r.error_level, int(r.context_len)): r
        for r in opt_agg.itertuples(index=False)
    }

    chronos_lkp: Dict[tuple, float] = {}
    for profile in ("fixed", "varying"):
        c_csv = chronos_mae_dir / f"new_complex_pri_{profile}_univariate_pri.csv"
        cdf = pd.read_csv(c_csv, encoding="utf-8-sig")
        for row in cdf.itertuples(index=False):
            for L in CONTEXTS:
                chronos_lkp[(profile, row.radar_type, row.error_level, L)] = float(getattr(row, f"MAE_L{L}_µs"))

    comp_rows: List[dict] = []
    for profile in ("fixed", "varying"):
        for radar in RADAR_TYPES:
            for level in ERROR_LEVELS:
                for L in CONTEXTS:
                    b_rec = base_lkp[(profile, radar, level, L)]
                    o_rec = opt_lkp[(profile, radar, level, L)]
                    c_mae = chronos_lkp[(profile, radar, level, L)]
                    b_mae = float(b_rec.mae_us)
                    o_mae = float(o_rec.mae_us)
                    med_floor = float(o_rec.ctx_median_mae_us)

                    best_val = min(b_mae, o_mae, c_mae)
                    if abs(o_mae - c_mae) < 1e-9 and o_mae == best_val:
                        best_model = "Tie (OptHMM/Chr-2)"
                    elif o_mae == best_val:
                        best_model = "Optimized HMM"
                    elif c_mae == best_val:
                        best_model = "Chronos-2"
                    else:
                        best_model = "Baseline HMM"

                    hmm_vs_chr_winner = "Optimized HMM" if o_mae < c_mae - 1e-9 else ("Tie" if abs(o_mae - c_mae) <= 1e-9 else "Chronos-2")
                    comp_rows.append(
                        {
                            "profile": profile,
                            "radar_type": radar,
                            "error_level": level,
                            "context_len": L,
                            "baseline_hmm_mae_us": b_mae,
                            "optimized_hmm_mae_us": o_mae,
                            "chronos2_mae_us": c_mae,
                            "ctx_median_floor_us": med_floor,
                            "delta_opt_minus_base_us": o_mae - b_mae,
                            "delta_opt_minus_chronos2_us": o_mae - c_mae,
                            "baseline_hit_rate_pct": float(b_rec.hit_rate_pct),
                            "optimized_hit_rate_pct": float(o_rec.hit_rate_pct),
                            "baseline_acf_gated_frac": float(b_rec.acf_gated_frac),
                            "optimized_acf_gated_frac": float(o_rec.acf_gated_frac),
                            "best_overall": best_model,
                            "opt_hmm_vs_chronos2_winner": hmm_vs_chr_winner,
                        }
                    )

    comp_df = pd.DataFrame(comp_rows)
    comp_df.to_csv(out_dir / "baseline_vs_optimized_hmm_vs_chronos2.csv", index=False)

    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    for profile in ("fixed", "varying"):
        for L in CONTEXTS:
            sub = [
                {
                    "radar_type": r,
                    "error_level": e,
                    "baseline": float(base_lkp[(profile, r, e, L)].mae_us),
                    "optimized": float(opt_lkp[(profile, r, e, L)].mae_us),
                    "chronos2": chronos_lkp[(profile, r, e, L)],
                    "median_floor": float(opt_lkp[(profile, r, e, L)].ctx_median_mae_us),
                }
                for r in RADAR_TYPES
                for e in ERROR_LEVELS
            ]
            plot_8panel_three_way(
                plots_dir / f"baseline_vs_optimized_vs_chronos2_{profile}_L{L}.png",
                sub,
                title=f"{NEW_COMPLEX_PRI}: Baseline HMM vs Optimized HMM vs Chronos-2 Zero-Shot\n{profile.capitalize()} Profile · L={L}, H=32",
                subtitle="Principled 1st-order K<=6 HMM (fixes dwell_and_switch & markov_agile; retains theoretical failures on high-order/continuous laws).",
            )

    # Summary Markdown
    md = [
        f"# 3-Way Benchmark: Baseline HMM vs Optimized 1st-Order HMM vs Chronos-2 Zero-Shot (`{NEW_COMPLEX_PRI}`)",
        "",
        "## Design Scope",
        "The Optimized HMM strictly preserves the **1st-order discrete-state HMM boundary ($K \\le 6$)** without adding ad-hoc hacks for high-order stagger (`K=16..32`) or continuous/up-down waveforms (`sinusoidal`, `triangular_sliding`, `sliding`). It fixes only the genuine HMM implementation flaws on discrete-state laws:",
        "1. Restores $K=5$ in candidate set `(1, 2, 3, 4, 5, 6)` + 1D K-Medians local-variance init (`init_params='st'`) for `dwell_and_switch`.",
        "2. Lowers the white-noise ACF gate (`0.22 -> 0.15`) + replaces greedy deterministic path rollout with probabilistic forward distribution propagation ($p_{T+h} = p_T A^h$) for `markov_agile`.",
        "3. Adds isolated 1-pulse Viterbi despiking + `0.985` dwell cap for multi-pulse burst-dwell laws.",
        "",
        "## Overall Wins Across All 512 Conditions (Opt HMM vs Chronos-2)",
        "",
        f"- **Optimized HMM beats Chronos-2**: {int((comp_df['opt_hmm_vs_chronos2_winner'] == 'Optimized HMM').sum())} / 512 (was {int((comp_df['baseline_hmm_mae_us'] < comp_df['chronos2_mae_us']).sum())} / 512 for Baseline HMM)",
        f"- **Chronos-2 beats Optimized HMM**: {int((comp_df['opt_hmm_vs_chronos2_winner'] == 'Chronos-2').sum())} / 512",
        "",
        "## Mean MAE (µs) Comparison at L = 992 by Radar Type (Averaged Across Clean..Lv7)",
        "",
        "| Profile | Radar type | Baseline HMM | Optimized HMM | Δ (Opt − Base) | Chronos-2 Zero-Shot | Ctx Median Floor |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    l992 = comp_df[comp_df["context_len"] == 992]
    summary_l992 = l992.groupby(["profile", "radar_type"], sort=False)[
        ["baseline_hmm_mae_us", "optimized_hmm_mae_us", "delta_opt_minus_base_us", "chronos2_mae_us", "ctx_median_floor_us"]
    ].mean()
    for (prof, rad), row in summary_l992.iterrows():
        md.append(
            f"| {prof} | {rad} | {row.baseline_hmm_mae_us:.3f} | {row.optimized_hmm_mae_us:.3f} | "
            f"{row.delta_opt_minus_base_us:+.3f} | {row.chronos2_mae_us:.3f} | {row.ctx_median_floor_us:.3f} |"
        )
    md.append("")

    for profile in ("fixed", "varying"):
        sub = l992[l992["profile"] == profile]
        md.extend(
            [
                f"## {profile.capitalize()} Profile Full Table at L = 992",
                "",
                "| Radar type | Error level | Baseline HMM | Optimized HMM | Δ (Opt−Base) | Chronos-2 | Opt Hit% | Best Overall |",
                "|---|---|---:|---:|---:|---:|---:|---|",
            ]
        )
        for r in sub.itertuples(index=False):
            md.append(
                f"| {r.radar_type} | {r.error_level} | {r.baseline_hmm_mae_us:.3f} | {r.optimized_hmm_mae_us:.3f} | "
                f"{r.delta_opt_minus_base_us:+.3f} | {r.chronos2_mae_us:.3f} | {r.optimized_hit_rate_pct:.1f}% | **{r.best_overall}** |"
            )
        md.append("")

    (out_dir / "Baseline_vs_Optimized_HMM_vs_Chronos2.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def render_per_step_horizon_curves(out_dir: Path) -> None:
    hp_dir = out_dir / "horizon_profiles"
    if not hp_dir.is_dir():
        return
    plots_dir = out_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    steps = np.arange(1, 33)
    for profile in ("fixed", "varying"):
        fig, axes = plt.subplots(2, 4, figsize=(19.2, 9.0), sharex=True)
        for ax, radar in zip(axes.flat, RADAR_TYPES, strict=True):
            for level, color, ls in (
                ("clean", "#16a34a", "-"),
                ("error_lv2", "#2563eb", "--"),
                ("error_lv7", "#dc2626", "-."),
            ):
                p = hp_dir / f"{profile}_{radar}_{level}_L992.json"
                if not p.is_file():
                    continue
                vals = json.loads(p.read_text(encoding="utf-8"))["per_step_mae_us"]
                ax.plot(steps, vals, linestyle=ls, color=color, linewidth=1.8, label=level)
            ax.set_title(RADAR_LABELS[radar], fontsize=12, fontweight="bold")
            ax.set_xlabel("Forecast horizon step h (1..32)", fontsize=10)
            ax.set_ylabel("Mean MAE (µs)", fontsize=10)
            ax.set_ylim(bottom=0)
            ax.grid(alpha=0.25)
        handles, labels = axes.flat[0].get_legend_handles_labels()
        fig.suptitle(
            f"{NEW_COMPLEX_PRI}: Optimized HMM Per-Step Horizon MAE (h=1..32) · {profile.capitalize()} Profile · L=992",
            fontsize=16,
            fontweight="bold",
            y=0.985,
        )
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.92), ncol=3, frameon=False, fontsize=11)
        fig.subplots_adjust(left=0.055, right=0.985, bottom=0.075, top=0.84, wspace=0.28, hspace=0.38)
        fig.savefig(plots_dir / f"per_step_horizon_mae_{profile}_L992.png", dpi=160)
        plt.close(fig)


def render_example_forecasts(out_dir: Path) -> None:
    examples_dir = out_dir / "examples"
    ex_plot_dir = out_dir / "plots" / "example_forecasts"
    ex_plot_dir.mkdir(parents=True, exist_ok=True)
    for profile in ("fixed", "varying"):
        for radar in RADAR_TYPES:
            for level in ("clean", "error_lv2", "error_lv7"):
                ex_file = examples_dir / f"{profile}_{radar}_{level}_L992_seq_0800.json"
                if not ex_file.is_file():
                    continue
                payload = json.loads(ex_file.read_text(encoding="utf-8"))
                m = payload["metrics"]
                title = (
                    f"Optimized HMM [{NEW_COMPLEX_PRI}] | {profile}/{radar}/{level} | L=992, H=32 | seq_0800 "
                    f"(MAE={m['mae']:.2f} µs, Hit={m['hit_rate_pct']:.1f}%)"
                )
                save_forecast_plot(
                    ex_plot_dir / f"{profile}_{radar}_{level}_L992_seq_0800.png",
                    title=title,
                    context=np.asarray(payload["context"], dtype=np.float64),
                    ground_truth=np.asarray(payload["target"], dtype=np.float64),
                    predictions=np.asarray(payload["prediction"], dtype=np.float64),
                    tolerance=10.0,
                    param_label="PRI",
                    unit="µs",
                    show_ctx_pts=96,
                )


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=base_dir / "results_optimized_hmm")
    parser.add_argument("--baseline-dir", type=Path, default=base_dir / "results_baseline_hmm")
    parser.add_argument(
        "--chronos-mae-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "new_complex_pri" / "mae_comparison" / "run_20261118_151924",
    )
    args = parser.parse_args()

    agg, _ = load_and_validate_raw(args.out_dir / "raw" / "optimized_hmm")
    agg.to_csv(args.out_dir / "metrics_by_condition.csv", index=False)

    write_mae_tables_and_pngs(agg, args.out_dir)
    write_hitrate_and_rmse_tables(agg, args.out_dir)
    write_by_radar_reports(agg, args.out_dir)
    build_three_way_comparison(agg, args.out_dir, args.baseline_dir, args.chronos_mae_dir)
    render_per_step_horizon_curves(args.out_dir)
    render_example_forecasts(args.out_dir)

    print(f"[DONE] Optimized HMM reports and 3-way comparisons saved under {args.out_dir}")


if __name__ == "__main__":
    main()
