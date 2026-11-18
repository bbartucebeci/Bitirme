#!/usr/bin/env python3
"""Aggregates run_context_sweep.py raw results into tables and the MAE-vs-L plot."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.common import ERROR_LEVELS, RADAR_TYPES

METHOD_LABELS = {
    "kalman_filter": "Kalman bank",
    "exponential_smoothing": "Exp. smoothing",
    "arima": "ARIMA",
}
NOISY = ["error_lv1", "error_lv2", "error_lv3"]
# CM1 reference (128-pulse data, L = 96, varying profile, mean noisy MAE over lv1-3), in us.
CM1_VARYING_L96 = {"kalman_filter": 29.3, "arima": 33.3, "exponential_smoothing": 33.3}
# Categorical slots 1-5 of the validated dataviz palette (fixed order by law) + markers.
LAW_STYLE = {
    "stable": ("#2a78d6", "o"),
    "jitter": ("#eb6834", "s"),
    "stagger": ("#1baf7a", "^"),
    "dwell_and_switch": ("#eda100", "D"),
    "sliding": ("#e87ba4", "v"),
}


def aggregate(raw_dir: Path) -> pd.DataFrame:
    frames = [pd.read_csv(f) for f in sorted(raw_dir.glob("*/*.csv"))]
    df = pd.concat(frames, ignore_index=True)
    df = df[df["valid_pulses"] > 0]
    df["fallback"] = df["ctx_used"] < df["context_len"]
    g = df.groupby(["method", "profile", "radar_type", "error_level", "context_len"])
    out = g.agg(
        sequences=("sequence_id", "count"),
        mae_us=("mae_us", "mean"),
        rmse_us=("rmse_us", "mean"),
        gate_hit_pct=("hit_rate_pct", "mean"),
        fallback_windows=("fallback", "sum"),
        latency_ms_per_seq=("latency_s", lambda x: 1e3 * float(np.mean(x))),
        cpu_s_total=("latency_s", "sum"),
    ).reset_index()
    return out


def fmt(v, nd=2):
    return f"{v:.{nd}f}"


def write_tables(agg: pd.DataFrame, out_dir: Path, Ls) -> None:
    agg.round(4).to_csv(out_dir / "metrics_by_dataset.csv", index=False)

    noisy = agg[agg["error_level"].isin(NOISY)]
    summ = noisy.groupby(["profile", "method", "context_len"])["mae_us"].mean().reset_index()
    summ.round(4).to_csv(out_dir / "summary_mean_noisy_mae.csv", index=False)

    lines = ["# Context-length sweep - classical methods on 1000x1024 datasets", "",
             "Horizon H = 32, random context start from `results/windows_1024.json` (seed 20261116), "
             "200 test sequences per dataset, emitter-only targets, gate +/-10 us.", "",
             "## Mean noisy MAE (us), mean over 5 laws x lv1-3", ""]
    for prof in ["fixed", "varying"]:
        lines += [f"### {prof} profile", "", "| Method | " + " | ".join(f"L={L}" for L in Ls) + " |",
                  "|---|" + "---:|" * len(Ls)]
        for m in METHOD_LABELS:
            vals = [summ[(summ.profile == prof) & (summ.method == m) & (summ.context_len == L)]["mae_us"]
                    for L in Ls]
            lines.append(f"| {METHOD_LABELS[m]} | " + " | ".join(fmt(v.iloc[0]) if len(v) else "-" for v in vals) + " |")
        lines.append("")

    lines += ["## Sanity check vs CM1 (varying profile, L = 96, mean noisy MAE)", "",
              "| Method | CM1 (128-pulse, s=0) | This run (1024-pulse, random s) | Deviation |", "|---|---:|---:|---:|"]
    for m, ref in CM1_VARYING_L96.items():
        v = summ[(summ.profile == "varying") & (summ.method == m) & (summ.context_len == 96)]["mae_us"]
        if len(v):
            dev = 100.0 * (v.iloc[0] - ref) / ref
            flag = "" if abs(dev) <= 10 else " **(> +/-10%)**"
            lines.append(f"| {METHOD_LABELS[m]} | {ref:.1f} | {v.iloc[0]:.1f} | {dev:+.1f}%{flag} |")
    lines.append("")

    lines += ["## Mean noisy MAE (us) per law", ""]
    for prof in ["fixed", "varying"]:
        lines += [f"### {prof} profile", "", "| Method | Law | " + " | ".join(f"L={L}" for L in Ls) + " |",
                  "|---|---|" + "---:|" * len(Ls)]
        pl = noisy[noisy.profile == prof].groupby(["method", "radar_type", "context_len"])["mae_us"].mean()
        for m in METHOD_LABELS:
            for r in RADAR_TYPES:
                lines.append(f"| {METHOD_LABELS[m]} | {r} | " +
                             " | ".join(fmt(pl.get((m, r, L), np.nan)) for L in Ls) + " |")
        lines.append("")

    lines += ["## Run time (sum of per-sequence fit+forecast CPU time, all 20 datasets x 200 seqs)", "",
              "| Method | Profile | " + " | ".join(f"L={L}" for L in Ls) + " |", "|---|---|" + "---:|" * len(Ls)]
    rt = agg.groupby(["method", "profile", "context_len"])["cpu_s_total"].sum()
    for m in METHOD_LABELS:
        for prof in ["fixed", "varying"]:
            lines.append(f"| {METHOD_LABELS[m]} | {prof} | " +
                         " | ".join(f"{rt.get((m, prof, L), np.nan) / 60:.1f} min" for L in Ls) + " |")
    lines.append("")
    fb = agg.groupby("context_len")["fallback_windows"].sum()
    lines += ["Fallback windows (sequence shorter than L + H, context shortened to n - H, s = 0), "
              "summed over methods x datasets: " + ", ".join(f"L={L}: {int(fb.get(L, 0))}" for L in Ls), ""]
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    # Full per-dataset table: MAE / RMSE / gate hit per method x law x level x L
    full = ["# MAE / RMSE / gate hit (+/-10 us) per method x law x level x L", "",
            "Cell = MAE / RMSE (us) / gate hit (%). Mean over 200 test sequences.", ""]
    for prof in ["fixed", "varying"]:
        for m in METHOD_LABELS:
            full += [f"## {METHOD_LABELS[m]} - {prof} profile", "",
                     "| Law | Level | " + " | ".join(f"L={L}" for L in Ls) + " |", "|---|---|" + "---|" * len(Ls)]
            sub = agg[(agg.profile == prof) & (agg.method == m)].set_index(["radar_type", "error_level", "context_len"])
            for r in RADAR_TYPES:
                for lv in ERROR_LEVELS:
                    cells = []
                    for L in Ls:
                        if (r, lv, L) in sub.index:
                            row = sub.loc[(r, lv, L)]
                            cells.append(f"{row.mae_us:.2f} / {row.rmse_us:.2f} / {row.gate_hit_pct:.1f}")
                        else:
                            cells.append("-")
                    full.append(f"| {r} | {lv} | " + " | ".join(cells) + " |")
            full.append("")
    (out_dir / "metrics_by_dataset.md").write_text("\n".join(full), encoding="utf-8")


def plot(agg: pd.DataFrame, out_dir: Path, Ls) -> None:
    noisy = agg[agg["error_level"].isin(NOISY)]
    pl = noisy.groupby(["profile", "method", "radar_type", "context_len"])["mae_us"].mean()
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.5), sharex=True, sharey=True)
    ink, muted = "#2b2b2b", "#6b6b6b"
    for i, prof in enumerate(["fixed", "varying"]):
        for j, m in enumerate(METHOD_LABELS):
            ax = axes[i, j]
            for r in RADAR_TYPES:
                if r not in set(agg.radar_type):
                    continue
                color, marker = LAW_STYLE[r]
                y = [pl.get((prof, m, r, L), np.nan) for L in Ls]
                ax.plot(Ls, y, color=color, marker=marker, linewidth=2, markersize=8,
                        markeredgecolor="white", markeredgewidth=1.5, label=r)
            ax.set_xscale("log", base=2)
            ax.set_yscale("log")
            ax.set_xticks(Ls)
            ax.set_xticklabels([str(L) for L in Ls])
            ax.minorticks_off()
            ax.grid(True, which="major", color="#e6e6e6", linewidth=0.8)
            for s in ("top", "right"):
                ax.spines[s].set_visible(False)
            for s in ("left", "bottom"):
                ax.spines[s].set_color("#bdbdbd")
            ax.tick_params(colors=muted)
            ax.set_title(f"{METHOD_LABELS[m]} - {prof} profile", color=ink, fontsize=12)
            if j == 0:
                ax.set_ylabel("Mean noisy MAE, lv1-3 (us, log)", color=ink)
            if i == 1:
                ax.set_xlabel("Context length L (pulses)", color=ink)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.suptitle("PRI forecast MAE vs context length (H = 32, 1000x1024 datasets)", y=0.99, color=ink, fontsize=13)
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.955), ncol=5, frameon=False, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(out_dir / "mae_vs_context_len.png", dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "results" / "classic_1024")
    parser.add_argument("--context-lens", type=int, nargs="+", default=[96, 256, 512, 992])
    parser.add_argument("--legacy-overview", action="store_true", help="Use the old cross-radar overview for historical results only")
    args = parser.parse_args()
    agg = aggregate(args.out_dir / "raw")
    if not args.legacy_overview:
        write_radar_reports(agg, args.out_dir)
        return
    write_tables(agg, args.out_dir, args.context_lens)
    plot(agg, args.out_dir, args.context_lens)
    print((args.out_dir / "summary.md").read_text(encoding="utf-8"))


def write_radar_reports(agg: pd.DataFrame, out_dir: Path) -> None:
    """Keep each radar and error level separate; never average across radar laws."""
    for law, data in agg.groupby("radar_type", sort=False):
        target = out_dir / "by_radar" / law
        target.mkdir(parents=True, exist_ok=True)
        data.round(4).to_csv(target / "metrics.csv", index=False)
        lines = [f"# Context-length comparison: {law}", "",
                 "Each row is a separate profile, error level, method and context length. No cross-radar or cross-error averaging.", "",
                 data.to_markdown(index=False), ""]
        (target / "report.md").write_text("\n".join(lines), encoding="utf-8")
        for profile, profile_data in data.groupby("profile"):
            levels = [level for level in ERROR_LEVELS if level in set(profile_data.error_level)]
            fig, axes = plt.subplots(2, 4, figsize=(17, 8), squeeze=False)
            for ax, level in zip(axes.flat, levels):
                subset = profile_data[profile_data.error_level == level]
                for method, values in subset.groupby("method"):
                    values = values.sort_values("context_len")
                    ax.plot(values.context_len, values.mae_us, marker="o", label=METHOD_LABELS.get(method, method))
                ax.set_title(level); ax.set_xlabel("Context length"); ax.set_ylabel("MAE (µs)")
                ax.grid(alpha=.25); ax.legend(fontsize=8)
            for ax in list(axes.flat)[len(levels):]:ax.set_visible(False)
            fig.suptitle(f"{law}: {profile} profile")
            fig.tight_layout()
            fig.savefig(target / f"{profile}.png", dpi=130)
            plt.close(fig)
    print(f"[SAVED] Per-radar reports: {out_dir / 'by_radar'}")


if __name__ == "__main__":
    main()
