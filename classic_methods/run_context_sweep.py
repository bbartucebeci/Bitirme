#!/usr/bin/env python3
"""Context-length sweep for the Kalman filter bank, exponential smoothing and ARIMA.

Parallel runner over (method, profile, law, level, L). Per-sequence evaluation is the
same as common.evaluate_method_across_benchmarks: the context window comes from the
window manifest (common.extract_window), metrics come from common.compute_metrics with
emitter-only masking (NOISE / ECHO pulses excluded from targets), and a dataset's
metric is the mean over its test sequences.

Per-sequence results are written to <out>/raw/<method>/<profile>_<law>_<level>_L<L>.csv;
a job whose raw file already exists is skipped (resumable). Then use
summarize_context_sweep.py for the tables and plot.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from pathlib import Path
import sys
import time

# One BLAS thread per worker process (the pool provides the parallelism).
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.common import (
    DEFAULT_DATASET_SIZE,
    DEFAULT_DATASETS_ROOT,
    ERROR_LEVELS,
    PARAM_SPECS,
    RADAR_TYPES,
    compute_metrics,
    extract_window,
    load_dataset_sequences,
    load_window_manifest,
    window_key,
)

METHOD_SLUGS = ["kalman_filter", "exponential_smoothing", "arima"]
# Rough relative cost, used only to start the slowest jobs first.
METHOD_COST = {"kalman_filter": 1.0, "exponential_smoothing": 0.3, "arima": 2.5}

_WINDOWS = None


def _predict_fn(slug: str):
    if slug == "kalman_filter":
        from classic_methods.kalman_filter import kalman_forecast as fn
    elif slug == "exponential_smoothing":
        from classic_methods.exponential_smoothing import exponential_smoothing_forecast as fn
    elif slug == "arima":
        from classic_methods.arima import arima_forecast as fn
    else:
        raise ValueError(slug)
    return fn


def _init_worker(manifest_path: str):
    global _WINDOWS
    _WINDOWS = load_window_manifest(Path(manifest_path))


def run_job(slug, profile, rtype, level, L, H, dataset_size, max_test_seqs, out_csv):
    fn = _predict_fn(slug)
    tol = PARAM_SPECS["PRI"]["default_tol"]
    ddir = DEFAULT_DATASETS_ROOT / profile / rtype / f"{dataset_size}_{level}"
    seqs = load_dataset_sequences(ddir, split="test", max_seqs=max_test_seqs, target_param="PRI")
    rows = []
    t_job = time.perf_counter()
    for seq_id, ctx_vals, tgt_vals, mask_vals in seqs:
        if len(ctx_vals) <= H + 8:
            continue
        start = int(_WINDOWS["windows"][window_key(profile, rtype, level, seq_id, L)])
        ctx, gt, mask = extract_window(ctx_vals, tgt_vals, mask_vals, L, H, start)
        t0 = time.perf_counter()
        preds = fn(ctx, H, "PRI")
        elapsed = time.perf_counter() - t0
        m = compute_metrics(preds, gt, tolerance=tol, mask=mask)
        rows.append({
            "method": slug, "profile": profile, "radar_type": rtype, "error_level": level,
            "context_len": L, "sequence_id": seq_id, "start": start, "ctx_used": len(ctx),
            "rmse_us": m["rmse"], "mae_us": m["mae"], "hit_rate_pct": m["hit_rate_pct"],
            "valid_pulses": m["valid_pulses"], "latency_s": elapsed,
        })
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_csv.with_suffix(".tmp")
    pd.DataFrame(rows).to_csv(tmp, index=False)
    os.replace(tmp, out_csv)
    return slug, profile, rtype, level, L, len(rows), time.perf_counter() - t_job


def main():
    parser = argparse.ArgumentParser(description="Classic-method context-length sweep (1024-pulse datasets)")
    parser.add_argument("--methods", nargs="+", choices=METHOD_SLUGS, default=METHOD_SLUGS)
    parser.add_argument("--profiles", nargs="+", default=["fixed", "varying"])
    parser.add_argument("--radar-types", nargs="+", default=RADAR_TYPES)
    parser.add_argument("--error-levels", nargs="+", default=ERROR_LEVELS)
    parser.add_argument("--context-lens", type=int, nargs="+", default=[96, 256, 512, 992])
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--dataset-size", default=DEFAULT_DATASET_SIZE)
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--window-manifest", type=Path, default=PROJECT_ROOT / "results" / "windows_1024.json")
    parser.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "results" / "classic_1024")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    args = parser.parse_args()

    meta = load_window_manifest(args.window_manifest)["meta"]
    assert int(meta["horizon_len"]) == args.horizon, "manifest horizon mismatch"
    assert meta["dataset_size"] == args.dataset_size, "manifest dataset size mismatch"

    jobs = []
    for slug in args.methods:
        for prof in args.profiles:
            for rtype in args.radar_types:
                for level in args.error_levels:
                    for L in args.context_lens:
                        out = args.out_dir / "raw" / slug / f"{prof}_{rtype}_{level}_L{L}.csv"
                        if out.exists():
                            continue
                        jobs.append((slug, prof, rtype, level, L, out))
    jobs.sort(key=lambda j: -METHOD_COST[j[0]] * j[4])
    print(f"{len(jobs)} jobs to run on {args.workers} workers", flush=True)

    t_all = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init_worker,
                             initargs=(str(args.window_manifest),)) as ex:
        futs = [ex.submit(run_job, slug, prof, rtype, level, L, args.horizon, args.dataset_size,
                          args.max_test_seqs, out) for slug, prof, rtype, level, L, out in jobs]
        for i, fut in enumerate(as_completed(futs), 1):
            slug, prof, rtype, level, L, n, dt = fut.result()
            print(f"[{i}/{len(jobs)}] {slug:<22} {prof:<7} {rtype:<17} {level:<10} L={L:<4} "
                  f"{n} seqs in {dt:7.1f}s | elapsed {time.perf_counter() - t_all:7.0f}s", flush=True)
    print(f"DONE in {time.perf_counter() - t_all:.0f}s")


if __name__ == "__main__":
    main()
