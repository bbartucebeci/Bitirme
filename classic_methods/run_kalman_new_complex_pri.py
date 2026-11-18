#!/usr/bin/env python3
"""Kalman filter bank on the new_complex_pri (C1024_H32) benchmark, reported per radar type.

new_complex_pri is the consecutive_future_v2 schema (see DATA_LAYOUT.md). Windows follow its
boundary contract (dataset_generator/CONSECUTIVE_FUTURE.md): after the
anchor, context = selected_rows[C-L:C] (Measured_Delta_TOA) and target = selected_rows[C:C+H]
(source PRI), so every context length L scores the same 32 consecutive future pulses.
Metrics use classic_methods.common.compute_metrics with emitter-only masking.

Outputs (under --out-dir):
  raw/<profile>_<radar>_<level>_L<L>.csv      per-sequence metrics (resumable)
  by_radar/<radar>/metrics.csv                 profile x error level x L means
  by_radar/<radar>/summary.md                  MAE / RMSE / hit-rate tables
  by_radar/<radar>/new_complex_pri_<radar>_mae_vs_error_level.png   MAE vs error level, one line per L
  overview_mae.csv / overview.md               radar x level MAE at each L (all radars)
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from pathlib import Path
import sys
import time

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np
import pandas as pd
import yaml

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.common import PARAM_SPECS, compute_metrics
from dataset_generator.catalog import ERROR_LEVELS, NEW_COMPLEX_DATASETS_ROOT, NEW_COMPLEX_PRI, RADAR_TYPES
from dataset_generator.sequence_io import boundary_start, is_boundary_dataset, read_sequence_frame

DEFAULT_ROOT = NEW_COMPLEX_DATASETS_ROOT / "production" / "C1024_H32" / "single_radar"
DEFAULT_OUT = PROJECT_ROOT / "results" / "classic_methods" / NEW_COMPLEX_PRI / "kalman_filter"


def run_job(profile, rtype, level, context_lens, H, dataset_size, root, raw_dir, max_test_seqs, max_period=24):
    from classic_methods.kalman_filter import kalman_forecast

    ddir = Path(root) / profile / rtype / f"{dataset_size}_{level}"
    meta = yaml.safe_load((ddir / "metadata.yaml").read_text(encoding="utf-8"))
    if not is_boundary_dataset(meta):
        raise ValueError(f"{ddir}: not a {NEW_COMPLEX_PRI} (consecutive_future_v2) dataset")
    C = int(meta["context_intervals"])
    files = sorted((ddir / "test").glob("seq_*.csv"))[:max_test_seqs]
    if len(files) != min(max_test_seqs, int(meta["split"]["test"]["sequence_count"])):
        raise ValueError(f"{ddir}: unexpected test sequence count {len(files)}")
    tol = PARAM_SPECS["PRI"]["default_tol"]
    rows = {L: [] for L in context_lens}
    t_job = time.perf_counter()
    for f in files:
        frame = read_sequence_frame(f).iloc[1:].reset_index(drop=True)  # drop anchor
        ctx_all = frame["Measured_Delta_TOA"].to_numpy(np.float64)
        tgt_all = frame["PRI"].to_numpy(np.float64)
        mask_all = frame["Radar_ID"].eq("R_SINGLE").to_numpy(bool)
        gt, mask = tgt_all[C:C + H], mask_all[C:C + H]
        if len(gt) != H:
            raise ValueError(f"{f}: stored horizon shorter than H={H}")
        for L in context_lens:
            start = boundary_start(meta, L, H, "boundary")
            t0 = time.perf_counter()
            preds = kalman_forecast(ctx_all[start:C], H, "PRI", max_period=max_period)
            dt = time.perf_counter() - t0
            m = compute_metrics(preds, gt, tolerance=tol, mask=mask)
            rows[L].append({
                "method": "kalman_filter", "profile": profile, "radar_type": rtype, "error_level": level,
                "context_len": L, "sequence_id": f.stem, "start": start,
                "rmse_us": m["rmse"], "mae_us": m["mae"], "medae_us": m["medae"],
                "hit_rate_pct": m["hit_rate_pct"], "valid_pulses": m["valid_pulses"], "latency_s": dt,
            })
    for L, r in rows.items():
        out = Path(raw_dir) / f"{profile}_{rtype}_{level}_L{L}.csv"
        tmp = out.with_suffix(".tmp")
        pd.DataFrame(r).to_csv(tmp, index=False)
        os.replace(tmp, out)
    return profile, rtype, level, len(files), time.perf_counter() - t_job


def summarize(out_dir: Path, context_lens):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    raw = pd.concat([pd.read_csv(p) for p in sorted((out_dir / "raw").glob("*.csv"))], ignore_index=True)
    agg = (raw.groupby(["radar_type", "profile", "error_level", "context_len"])
              .agg(n_seqs=("mae_us", "size"), mae_us=("mae_us", "mean"), rmse_us=("rmse_us", "mean"),
                   medae_us=("medae_us", "mean"), hit_rate_pct=("hit_rate_pct", "mean"),
                   latency_ms=("latency_s", lambda s: 1e3 * s.mean()))
              .reset_index())
    lvl_order = {l: i for i, l in enumerate(ERROR_LEVELS)}
    agg = agg.sort_values(["radar_type", "profile", "error_level", "context_len"],
                          key=lambda c: c.map(lvl_order) if c.name == "error_level" else c)

    def table(df, value, fmt):
        t = df.pivot_table(index="error_level", columns="context_len", values=value)
        t = t.reindex([l for l in ERROR_LEVELS if l in t.index])
        t.columns = [f"L={c}" for c in t.columns]
        return t.to_markdown(floatfmt=fmt)

    for rtype in RADAR_TYPES:
        sub = agg[agg.radar_type == rtype]
        if sub.empty:
            continue
        d = out_dir / "by_radar" / rtype
        d.mkdir(parents=True, exist_ok=True)
        sub.drop(columns="radar_type").to_csv(d / "metrics.csv", index=False)
        md = [f"# Kalman filter bank: `{rtype}` ({NEW_COMPLEX_PRI}, C=1024, H=32)", "",
              f"Test split, {int(sub.n_seqs.max())} sequences per condition. PRI target, ±10 µs hit gate, "
              "emitter-only masking. Mean over sequences of per-sequence metrics.", ""]
        for prof in ("fixed", "varying"):
            ps = sub[sub.profile == prof]
            if ps.empty:
                continue
            md += [f"## {prof} profile", "", "### MAE (µs)", "", table(ps, "mae_us", ".2f"), "",
                   "### RMSE (µs)", "", table(ps, "rmse_us", ".2f"), "",
                   "### Hit rate ±10 µs (%)", "", table(ps, "hit_rate_pct", ".1f"), ""]
        (d / "summary.md").write_text("\n".join(md), encoding="utf-8")

        fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=False)
        for ax, prof in zip(axes, ("fixed", "varying")):
            ps = sub[sub.profile == prof]
            for L in context_lens:
                s = ps[ps.context_len == L].set_index("error_level").reindex(ERROR_LEVELS)
                ax.plot(range(len(ERROR_LEVELS)), s.mae_us.to_numpy(), marker="o", label=f"L={L}")
            ax.set_xticks(range(len(ERROR_LEVELS)), [l.replace("error_", "") for l in ERROR_LEVELS], rotation=30)
            ax.set_title(f"{rtype} — {prof}")
            ax.set_xlabel("error level")
            ax.set_ylabel("MAE (µs)")
            ax.grid(alpha=0.3)
        axes[0].legend(title="context")
        fig.suptitle(f"Kalman filter bank, PRI MAE, H=32 ({NEW_COMPLEX_PRI})")
        fig.tight_layout()
        fig.savefig(d / f"{NEW_COMPLEX_PRI}_{rtype}_mae_vs_error_level.png", dpi=130)
        plt.close(fig)

    agg.to_csv(out_dir / "metrics_all.csv", index=False)
    md = [f"# Kalman filter bank on {NEW_COMPLEX_PRI} — overview", "",
          "PRI MAE (µs), mean over 200 test sequences, H=32. Per-radar detail in `by_radar/<type>/summary.md`.", ""]
    for prof in ("fixed", "varying"):
        for L in context_lens:
            s = agg[(agg.profile == prof) & (agg.context_len == L)]
            if s.empty:
                continue
            t = s.pivot_table(index="radar_type", columns="error_level", values="mae_us")
            t = t.reindex(index=[r for r in RADAR_TYPES if r in t.index],
                          columns=[l for l in ERROR_LEVELS if l in t.columns])
            md += [f"## {prof}, L={L}", "", t.to_markdown(floatfmt=".2f"), ""]
    (out_dir / "overview.md").write_text("\n".join(md), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--datasets-root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--dataset-size", default="1000x1056")
    ap.add_argument("--profiles", nargs="+", default=["fixed", "varying"])
    ap.add_argument("--radar-types", nargs="+", default=list(RADAR_TYPES))
    ap.add_argument("--error-levels", nargs="+", default=list(ERROR_LEVELS))
    ap.add_argument("--context-lens", type=int, nargs="+", default=[96, 256, 512, 992, 1024])
    ap.add_argument("--horizon", type=int, default=32)
    ap.add_argument("--max-test-seqs", type=int, default=200)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--max-period", type=int, default=24, help="largest periodic-model period in the bank")
    ap.add_argument("--summary-only", action="store_true")
    args = ap.parse_args()

    raw_dir = args.out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    if not args.summary_only:
        jobs = [(p, r, l) for p in args.profiles for r in args.radar_types for l in args.error_levels
                if not all((raw_dir / f"{p}_{r}_{l}_L{L}.csv").exists() for L in args.context_lens)]
        print(f"{len(jobs)} conditions to run on {args.workers} workers", flush=True)
        t_all = time.perf_counter()
        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            futs = [ex.submit(run_job, p, r, l, args.context_lens, args.horizon, args.dataset_size,
                              str(args.datasets_root), str(raw_dir), args.max_test_seqs, args.max_period) for p, r, l in jobs]
            for i, fut in enumerate(as_completed(futs), 1):
                p, r, l, n, dt = fut.result()
                print(f"[{i}/{len(jobs)}] {p:<7} {r:<18} {l:<10} {n} seqs in {dt:6.1f}s "
                      f"| elapsed {time.perf_counter() - t_all:6.0f}s", flush=True)
    summarize(args.out_dir, args.context_lens)
    print(f"Summaries written under {args.out_dir}")


if __name__ == "__main__":
    main()
