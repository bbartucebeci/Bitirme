#!/usr/bin/env python3
"""Effect of context length on a fixed forecast horizon, one figure per radar law.

For every test sequence the horizon is fixed to the LAST H pulses (n-H .. n-1) and the
context is the L pulses immediately before it (n-H-L .. n-H-1), so all context lengths
forecast exactly the same target pulses and only the amount of history changes.

Each figure has three forecast panels (Kalman bank, exponential smoothing, ARIMA) for one
example test sequence, with one forecast line per L, and a fourth panel with the MAE vs L
averaged over all test sequences of that dataset (emitter-only targets).
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import os
from pathlib import Path
import sys

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.common import DEFAULT_DATASETS_ROOT, RADAR_TYPES, compute_metrics, load_dataset_sequences

METHODS = {
    "kalman_filter": "Kalman bank",
    "exponential_smoothing": "Exp. smoothing",
    "arima": "ARIMA",
}
# Context length is ordinal -> one-hue sequential ramp (light = short, dark = long).
L_COLORS = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
METHOD_COLORS = {"kalman_filter": "#eb6834", "exponential_smoothing": "#1baf7a", "arima": "#6250d6"}
METHOD_MARKERS = {"kalman_filter": "o", "exponential_smoothing": "s", "arima": "^"}
INK, MUTED, GRID = "#2b2b2b", "#6b6b6b", "#e6e6e6"


def _fn(slug):
    if slug == "kalman_filter":
        from classic_methods.kalman_filter import kalman_forecast as f
    elif slug == "exponential_smoothing":
        from classic_methods.exponential_smoothing import exponential_smoothing_forecast as f
    else:
        from classic_methods.arima import arima_forecast as f
    return f


def fixed_window(ctx_vals, tgt_vals, mask_vals, L, H):
    n = len(ctx_vals)
    o = n - H  # forecast origin: first horizon pulse
    return ctx_vals[o - L : o], tgt_vals[o:], mask_vals[o:]


def run_job(slug, ddir, L, H, max_seqs, example_id):
    fn = _fn(slug)
    rows, example = [], None
    for sid, c, t, m in load_dataset_sequences(Path(ddir), split="test", max_seqs=max_seqs):
        ctx, gt, mask = fixed_window(c, t, m, L, H)
        preds = fn(ctx, H, "PRI")
        mt = compute_metrics(preds, gt, tolerance=10.0, mask=mask)
        if mt["valid_pulses"] > 0:
            rows.append({"sequence_id": sid, "mae_us": mt["mae"], "rmse_us": mt["rmse"], "hit_rate_pct": mt["hit_rate_pct"]})
        if sid == example_id:
            example = preds
    return slug, L, rows, example


def plot_law(law, profile, level, Ls, H, ex, results, summary, out_path, show_ctx):
    sid, c, t, m = ex
    n = len(c)
    o = n - H
    x_ctx = np.arange(o - show_ctx, o)
    x_h = np.arange(o, n)
    gt, mask = t[o:], m[o:]

    fig, axes = plt.subplots(2, 2, figsize=(15, 9.5))
    panels = [axes[0, 0], axes[0, 1], axes[1, 0]]
    truth_vals = gt[mask]
    lo, hi = float(np.min(truth_vals)), float(np.max(truth_vals))
    for ax, (slug, label) in zip(panels, METHODS.items()):
        ax.plot(x_ctx, c[o - show_ctx : o], "-", color="#a3a3a3", linewidth=1.2, marker="o", markersize=3,
                label=f"Observed context (last {show_ctx} pulses)")
        ax.plot(x_h[mask], gt[mask], "-", color=INK, linewidth=2.2, marker="s", markersize=4.5, label="Ground truth (emitter PRI)")
        for L, col in zip(Ls, L_COLORS):
            p = results[(slug, L)]
            mae = compute_metrics(p, gt, tolerance=10.0, mask=mask)["mae"]
            ax.plot(x_h, p, "-", color=col, linewidth=2, label=f"L = {L}  (MAE {mae:.1f} µs)")
            lo, hi = min(lo, float(np.min(p))), max(hi, float(np.max(p)))
        ax.axvline(o - 0.5, color=MUTED, linestyle="--", linewidth=1)
        ax.set_title(f"{label} - forecasts of the same 32 pulses", color=INK, fontsize=12)
        ax.set_xlabel("Pulse index", color=INK)
        ax.set_ylabel("PRI (µs)", color=INK)
        ax.legend(loc="upper left", fontsize=8.5, frameon=False)
    # Shared y-range: forecasts + truth (context spikes from missed / false pulses are clipped).
    span = max(hi - lo, 8.0)
    for ax in panels:
        ax.set_ylim(lo - 0.15 * span, hi + 0.9 * span)

    ax = axes[1, 1]
    ends = []
    for slug, label in METHODS.items():
        y = [summary[(slug, L)] for L in Ls]
        ax.plot(Ls, y, "-", color=METHOD_COLORS[slug], marker=METHOD_MARKERS[slug], linewidth=2, markersize=8,
                markeredgecolor="white", markeredgewidth=1.5, label=label)
        ends.append(y[-1])
    # End-of-line value labels, nudged apart so close values do not overlap.
    all_y = [summary[k] for k in summary]
    gap = 0.06 * (max(all_y) - min(all_y) or 1.0)
    placed = []
    for v in sorted(ends):
        pos = max(v, placed[-1] + gap) if placed else v
        placed.append(pos)
        ax.annotate(f"{v:.2f}" if v < 1 else f"{v:.1f}", (Ls[-1], v), xytext=(Ls[-1] * 1.04, pos),
                    textcoords="data", va="center", fontsize=9, color=INK)
    ax.set_xscale("log", base=2)
    ax.set_xticks(Ls)
    ax.set_xticklabels([str(L) for L in Ls])
    ax.minorticks_off()
    ax.set_xlim(Ls[0] * 0.85, Ls[-1] * 1.25)
    ax.set_title("Mean MAE over all test sequences (same horizon for every L)", color=INK, fontsize=12)
    ax.set_xlabel("Context length L (pulses)", color=INK)
    ax.set_ylabel("MAE (µs)", color=INK)
    ax.legend(frameon=False, fontsize=10)

    for a in axes.flat:
        a.grid(True, color=GRID, linewidth=0.8)
        for s in ("top", "right"):
            a.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            a.spines[s].set_color("#bdbdbd")
        a.tick_params(colors=MUTED)
    fig.suptitle(f"Context length vs a fixed 32-pulse horizon - {law} | {profile} profile, {level} "
                 f"(example: {sid}; horizon = pulses {o}-{n - 1})", color=INK, fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile-mode", default="varying")
    parser.add_argument("--error-level", default="error_lv2")
    parser.add_argument("--dataset-size", default="1000x1024")
    parser.add_argument("--context-lens", type=int, nargs="+", default=[96, 256, 512, 992])
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--example", default="seq_0800", help="Test sequence shown in the forecast panels")
    parser.add_argument("--show-ctx", type=int, default=48)
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()

    out_dir = args.out_dir or (PROJECT_ROOT / "results" / "classic_1024" /
                               f"context_effect_{args.profile_mode}_{args.error_level}")
    Ls, H = args.context_lens, args.horizon
    ddirs = {law: DEFAULT_DATASETS_ROOT / args.profile_mode / law / f"{args.dataset_size}_{args.error_level}"
             for law in RADAR_TYPES}

    jobs = [(slug, law, L) for law in RADAR_TYPES for slug in METHODS for L in Ls]
    jobs.sort(key=lambda j: -j[2] * (2.5 if j[0] == "arima" else 1.0))
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_job, slug, str(ddirs[law]), L, H, args.max_test_seqs, args.example): (slug, law, L)
                for slug, law, L in jobs}
        out = {}
        for f, (slug, law, L) in futs.items():
            out[(law, slug, L)] = f.result()
            print(f"done {law:<17} {slug:<22} L={L}", flush=True)

    all_rows = []
    for law in RADAR_TYPES:
        results, summary = {}, {}
        for slug in METHODS:
            for L in Ls:
                _, _, rows, example = out[(law, slug, L)]
                results[(slug, L)] = example
                summary[(slug, L)] = float(np.mean([r["mae_us"] for r in rows]))
                for r in rows:
                    all_rows.append({"radar_type": law, "method": slug, "context_len": L, **r})
        ex_seq = [s for s in load_dataset_sequences(ddirs[law], split="test", max_seqs=args.max_test_seqs)
                  if s[0] == args.example][0]
        plot_law(law, args.profile_mode, args.error_level, Ls, H, ex_seq, results, summary,
                 out_dir / f"{law}.png", args.show_ctx)
        print(f"[SAVED] {out_dir / f'{law}.png'}")

    df = pd.DataFrame(all_rows)
    df.round(4).to_csv(out_dir / "per_sequence.csv", index=False)
    summ = df.groupby(["radar_type", "method", "context_len"])[["mae_us", "rmse_us", "hit_rate_pct"]].mean().round(3)
    summ.to_csv(out_dir / "summary.csv")
    print(summ.unstack("context_len")["mae_us"].to_string())


if __name__ == "__main__":
    main()
