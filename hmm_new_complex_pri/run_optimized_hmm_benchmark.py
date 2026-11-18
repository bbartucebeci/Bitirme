#!/usr/bin/env python3
"""16-core parallel Optimized Hidden Markov Model context-length sweep
on the new_complex_pri (1000x1056, consecutive_future_v2) PRI benchmark.

Evaluates `hmm_new_complex_pri.optimized_hmm.optimized_hmm_forecast` across:
- Profiles: fixed, varying
- Radar types: all 8 laws
- Error levels: clean, error_lv1..error_lv7
- Context lengths: L = 96, 256, 512, 992 (boundary mode: C=1024, H=32)

Writes outputs exclusively to `hmm_new_complex_pri/results_optimized_hmm/`.
"""

from __future__ import annotations

import os

for _env_var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_env_var, "1")

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.common import PARAM_SPECS, clean_pri_context, compute_metrics
from dataset_generator.catalog import ERROR_LEVELS, NEW_COMPLEX_DATASETS_ROOT, RADAR_TYPES, SCHEMA_V2
from dataset_generator.sequence_io import boundary_start, is_boundary_dataset, read_sequence_frame
from hmm_new_complex_pri.optimized_hmm import optimized_hmm_forecast

RADAR_COST = {
    "stagger": 4.0,
    "sinusoidal": 3.5,
    "markov_agile": 3.5,
    "triangular_sliding": 3.0,
    "dwell_and_switch": 2.5,
    "sliding": 2.5,
    "jitter": 1.0,
    "stable": 1.0,
}


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _atomic_write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


def _is_raw_job_complete(raw_csv: Path, example_json: Path, horizon_json: Path, expected_seqs: int) -> bool:
    if not raw_csv.is_file() or not example_json.is_file() or not horizon_json.is_file():
        return False
    try:
        df = pd.read_csv(raw_csv)
        required_cols = {"mae_us", "ctx_median_mae_us", "ctx_last_mae_us", "cleaned_len", "true_source_pulses", "acf_gated"}
        if not required_cols.issubset(df.columns):
            return False
        return len(df) == expected_seqs and not df["mae_us"].isna().any()
    except Exception:
        return False


def _audit_cleaner_and_gate(ctx: np.ndarray) -> Tuple[int, bool]:
    cleaned = clean_pri_context(ctx)
    x_zero = cleaned - np.mean(cleaned)
    var = float(np.dot(x_zero, x_zero))
    max_acf = 0.0
    if var > 1e-6 and len(cleaned) > 6:
        acfs = [abs(float(np.dot(x_zero[:-lag], x_zero[lag:]) / var)) for lag in range(1, min(17, len(cleaned) // 2))]
        max_acf = max(acfs) if acfs else 0.0
    return int(len(cleaned)), bool(max_acf < 0.15)


def _run_one_job(task: Tuple[Any, ...]) -> Tuple[str, str, str, int, str, int, float]:
    (
        datasets_root_str,
        out_dir_str,
        profile,
        radar_type,
        error_level,
        context_len,
        horizon,
        dataset_size,
        max_test_seqs,
        plot_seq_id,
    ) = task

    datasets_root = Path(datasets_root_str)
    out_dir = Path(out_dir_str)
    tag = f"{profile}_{radar_type}_{error_level}_L{context_len}"
    raw_csv = out_dir / "raw" / "optimized_hmm" / f"{tag}.csv"
    example_json = out_dir / "examples" / f"{tag}_{plot_seq_id}.json"
    horizon_json = out_dir / "horizon_profiles" / f"{tag}.json"

    dataset_dir = datasets_root / profile / radar_type / f"{dataset_size}_{error_level}"
    metadata = yaml.safe_load((dataset_dir / "metadata.yaml").read_text(encoding="utf-8"))
    if not is_boundary_dataset(metadata):
        raise ValueError(f"{dataset_dir}: expected {SCHEMA_V2} dataset")

    expected_intervals = int(metadata["expected_pulses_per_sequence"])
    expected_test = min(int(metadata["split"]["test"]["sequence_count"]), max_test_seqs or 10**9)

    if _is_raw_job_complete(raw_csv, example_json, horizon_json, expected_test):
        return profile, radar_type, error_level, context_len, "skipped", expected_test, 0.0

    start = boundary_start(metadata, context_len, horizon, "boundary")
    tol = float(PARAM_SPECS["PRI"]["default_tol"])

    test_files = sorted((dataset_dir / "test").glob("seq_*.csv"))
    if max_test_seqs is not None and max_test_seqs > 0:
        test_files = test_files[:max_test_seqs]
    if len(test_files) != expected_test:
        raise ValueError(f"{dataset_dir}: expected {expected_test} test CSVs, found {len(test_files)}")

    rows: List[Dict[str, Any]] = []
    example_payload: Dict[str, Any] | None = None
    step_abs_err_sum = np.zeros(horizon, dtype=np.float64)
    step_count = np.zeros(horizon, dtype=np.int64)
    t_job = time.perf_counter()

    for csv_path in test_files:
        frame_full = read_sequence_frame(csv_path)
        has_anchor = (
            len(frame_full) > 1
            and "Measured_Delta_TOA" in frame_full.columns
            and float(frame_full["Measured_Delta_TOA"].iloc[0]) == 0.0
        )
        frame = frame_full.iloc[1:].reset_index(drop=True) if has_anchor else frame_full
        if len(frame) != expected_intervals:
            raise ValueError(f"{csv_path}: expected {expected_intervals} rows after anchor, found {len(frame)}")

        if has_anchor and "source_pulse_id" in frame_full.columns:
            true_source_pulses = int(
                frame_full["source_pulse_id"].iloc[start + context_len] - frame_full["source_pulse_id"].iloc[start]
            )
        else:
            true_source_pulses = context_len

        ctx_all = frame["Measured_Delta_TOA"].to_numpy(dtype=np.float64)
        tgt_all = frame["PRI"].to_numpy(dtype=np.float64)
        mask_all = (frame["Radar_ID"].astype(str) == "R_SINGLE").to_numpy(dtype=bool)

        ctx = ctx_all[start : start + context_len]
        gt = tgt_all[start + context_len : start + context_len + horizon]
        mask = mask_all[start + context_len : start + context_len + horizon]

        cleaned_len, acf_gated = _audit_cleaner_and_gate(ctx)

        t0 = time.perf_counter()
        preds = optimized_hmm_forecast(ctx, horizon_len=horizon, target_param="PRI")
        elapsed = time.perf_counter() - t0

        metrics = compute_metrics(preds, gt, tolerance=tol, mask=mask)

        valid_gt = gt[mask] if mask.any() else gt
        ctx_med_pred = np.full(len(valid_gt), float(np.median(ctx)), dtype=np.float64)
        ctx_last_pred = np.full(len(valid_gt), float(ctx[-1]), dtype=np.float64)
        ctx_median_mae = float(np.mean(np.abs(ctx_med_pred - valid_gt)))
        ctx_last_mae = float(np.mean(np.abs(ctx_last_pred - valid_gt)))

        abs_err = np.abs(np.asarray(preds, dtype=np.float64) - gt)
        step_abs_err_sum[mask] += abs_err[mask]
        step_count[mask] += 1

        rows.append(
            {
                "method": "optimized_hmm",
                "profile": profile,
                "radar_type": radar_type,
                "error_level": error_level,
                "context_len": context_len,
                "horizon": horizon,
                "sequence_id": csv_path.stem,
                "start": start,
                "ctx_used": len(ctx),
                "cleaned_len": cleaned_len,
                "true_source_pulses": true_source_pulses,
                "acf_gated": int(acf_gated),
                "mae_us": metrics["mae"],
                "rmse_us": metrics["rmse"],
                "medae_us": metrics["medae"],
                "mape_pct": metrics["mape_pct"],
                "hit_rate_pct": metrics["hit_rate_pct"],
                "ctx_median_mae_us": ctx_median_mae,
                "ctx_last_mae_us": ctx_last_mae,
                "valid_pulses": metrics["valid_pulses"],
                "latency_s": elapsed,
            }
        )

        if csv_path.stem == plot_seq_id:
            example_payload = {
                "method": "optimized_hmm",
                "profile": profile,
                "radar_type": radar_type,
                "error_level": error_level,
                "context_len": context_len,
                "horizon": horizon,
                "sequence_id": csv_path.stem,
                "start": start,
                "context": ctx.tolist(),
                "target": gt.tolist(),
                "prediction": np.asarray(preds, dtype=np.float64).tolist(),
                "emitter_mask": mask.tolist(),
                "metrics": metrics,
            }

    if example_payload is not None:
        _atomic_write_json(example_json, example_payload)
    per_step_mae = (step_abs_err_sum / np.maximum(step_count, 1)).tolist()
    _atomic_write_json(
        horizon_json,
        {
            "profile": profile,
            "radar_type": radar_type,
            "error_level": error_level,
            "context_len": context_len,
            "horizon": horizon,
            "per_step_mae_us": per_step_mae,
        },
    )
    _atomic_write_csv(raw_csv, pd.DataFrame(rows))
    return profile, radar_type, error_level, context_len, "evaluated", len(rows), time.perf_counter() - t_job


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--datasets-root",
        type=Path,
        default=NEW_COMPLEX_DATASETS_ROOT / "production" / "C1024_H32" / "single_radar",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "results_optimized_hmm",
    )
    parser.add_argument("--dataset-size", default="1000x1056")
    parser.add_argument("--context-lens", type=int, nargs="+", default=[96, 256, 512, 992])
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--profiles", nargs="+", choices=["fixed", "varying"], default=["fixed", "varying"])
    parser.add_argument("--radar-types", nargs="+", choices=list(RADAR_TYPES), default=list(RADAR_TYPES))
    parser.add_argument("--error-levels", nargs="+", choices=list(ERROR_LEVELS), default=list(ERROR_LEVELS))
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--plot-sequence-id", default="seq_0800")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 16)
    args = parser.parse_args()

    collection_path = args.datasets_root.parent / "collection.json"
    if collection_path.is_file():
        collection = json.loads(collection_path.read_text(encoding="utf-8"))
        if collection.get("status") != "complete":
            raise RuntimeError(f"Dataset collection is not complete: {collection_path} (status={collection.get('status')})")

    jobs: List[Tuple[float, Tuple[Any, ...]]] = []
    for L in args.context_lens:
        for profile in args.profiles:
            for rtype in args.radar_types:
                for elvl in args.error_levels:
                    cost = L * RADAR_COST.get(rtype, 2.0)
                    task = (
                        str(args.datasets_root),
                        str(args.out_dir),
                        profile,
                        rtype,
                        elvl,
                        int(L),
                        int(args.horizon),
                        args.dataset_size,
                        args.max_test_seqs,
                        args.plot_sequence_id,
                    )
                    jobs.append((cost, task))

    jobs.sort(key=lambda item: item[0], reverse=True)
    ordered_tasks = [t for _, t in jobs]

    print(
        f"[START] Parallel Optimized HMM sweep: {len(ordered_tasks)} jobs "
        f"({len(args.profiles)} profiles x {len(args.radar_types)} radars x "
        f"{len(args.error_levels)} levels x {len(args.context_lens)} context_lens), "
        f"workers={args.workers}, out={args.out_dir}",
        flush=True,
    )

    t_start = time.perf_counter()
    done = 0
    evaluated = 0
    skipped = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(_run_one_job, t): t for t in ordered_tasks}
        for future in as_completed(futures):
            prof, rtype, elvl, L, status, n_seqs, elapsed = future.result()
            done += 1
            if status == "evaluated":
                evaluated += 1
            else:
                skipped += 1
            if done % 16 == 0 or done == len(ordered_tasks) or elapsed > 5.0:
                print(
                    f"[{done:3d}/{len(ordered_tasks)}] {status:9s} {prof}/{rtype}/{elvl} L={L:<3d} "
                    f"({n_seqs} seqs, {elapsed:.2f}s) | wall={time.perf_counter() - t_start:.1f}s",
                    flush=True,
                )

    print(
        f"[COMPLETE] All {done} Optimized HMM jobs finished ({evaluated} evaluated, {skipped} skipped) "
        f"in {time.perf_counter() - t_start:.1f}s.",
        flush=True,
    )


if __name__ == "__main__":
    main()
