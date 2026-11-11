#!/usr/bin/env python3
"""Hyperparameter tuning of the robust-periodicity methods on the VALIDATION split.

Protocol
--------
  - Same windowing and scoring as the benchmark (96-pulse context, 32-pulse horizon,
    errors on emitter pulses only, target = source PRI), but on `val/` (100 sequences per
    dataset). The test split is never read by this script.
  - Objective: mean MAE over all 40 datasets (5 radar types x 4 error levels x 2 profiles).
    One global value per parameter; nothing is tuned per radar type or per error level.
  - One-at-a-time search: each parameter is varied over its grid with the others at their
    defaults. The winner is written to the report; the defaults in the source files are
    then set to those values by hand. Round 1 (tuning_all) used the initial defaults;
    round 2 (tuning_round2) repeats the search around the round-1 winners with wider grids.

Each (parameter setting, profile, radar type) runs in its own worker process, with the
setting passed through the environment variable PULSAR_ROBUST_PARAMS (see toa_utils.tuned).

Usage:
    python classic_methods/tune_robust_methods.py                 # all methods
    python classic_methods/tune_robust_methods.py --methods sdif cdif --jobs 8
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Dict, List

import numpy as np

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.common import (
    DEFAULT_DATASETS_ROOT,
    ERROR_LEVELS,
    RADAR_TYPES,
    compute_metrics,
    load_dataset_sequences,
)

PROFILES = ["fixed", "varying"]
CONTEXT_LEN, HORIZON_LEN, TOLERANCE = 96, 32, 10.0
OUT_DIR = PROJECT_ROOT / "results" / "classic_methods" / "robust_tuning_val"

# method -> {parameter: grid}. The first-listed method that owns a parameter tunes it.
SEARCH_SPACE: Dict[str, Dict[str, list]] = {
    "sdif": {
        "toa.PHASE_TOL_US": [2.0, 4.0, 8.0],
        "toa.MIN_INLIER_FRACTION": [0.7, 0.8, 0.9],
        "toa.MIN_COVERAGE": [0.5, 0.7, 0.85],
        "toa.FALLBACK_WINDOW": [32, 64, 96],
        "cdif_sdif.BIN_WIDTH_US": [1.0, 2.0, 4.0],
        "cdif_sdif.SDIF_X": [0.08, 0.15, 0.3, 0.5],
        "cdif_sdif.SEARCH_RHO": [0.5, 0.7, 0.85],
    },
    "cdif": {"cdif_sdif.CDIF_GAMMA": [0.3, 0.5, 0.8]},
    "pri_transform": {
        "pri_transform.ALPHA": [0.2, 0.3, 0.5, 0.8],
        "pri_transform.BETA": [0.02, 0.05, 0.1, 0.15, 0.3],
        "pri_transform.MIN_PERIODS": [2.5, 4.0],
    },
    "lomb_scargle": {"lomb_scargle.MIN_POWER": [0.05, 0.1, 0.15, 0.25, 0.4]},
    "toa_grid_fit": {"toa_grid_fit.RANSAC_ITERS": [0, 12, 30]},
    "toa_grid_fit_hedged": {},
    "period_estimation_template_gate": {},
    "kalman_filter_template_gate": {},
    "imm_filter": {
        "imm_filter.P_STAY": [0.9, 0.98, 0.995, 0.999, 0.9999],
        "imm_filter.PROPAGATE_MODES": [False, True],
    },
    "forecast_combination": {"forecast_combination.WEIGHT_POWER": [0.5, 1.0, 2.0, 4.0]},
}

# Existing baselines, evaluated on the same validation windows for reference.
REFERENCE_METHODS = ["period_estimation", "kalman_filter"]


def get_predict_fn(method: str) -> Callable:
    """Imports lazily, so the environment overrides are in place before the import."""
    if method == "cdif":
        from classic_methods.cdif_sdif import cdif_forecast as fn
    elif method == "sdif":
        from classic_methods.cdif_sdif import sdif_forecast as fn
    elif method == "pri_transform":
        from classic_methods.pri_transform import pri_transform_forecast as fn
    elif method == "lomb_scargle":
        from classic_methods.lomb_scargle import lomb_scargle_forecast as fn
    elif method == "toa_grid_fit":
        from classic_methods.toa_grid_fit import toa_grid_forecast as fn
    elif method == "toa_grid_fit_hedged":
        from classic_methods.toa_grid_fit import toa_grid_hedged_forecast as fn
    elif method == "imm_filter":
        from classic_methods.imm_filter import imm_forecast as fn
    elif method == "forecast_combination":
        from classic_methods.forecast_combination import combination_forecast as fn
    elif method == "period_estimation":
        from classic_methods.period_estimation import period_estimation_forecast as fn
    elif method == "kalman_filter":
        from classic_methods.kalman_filter import kalman_forecast as fn
    elif method == "period_estimation_template_gate":
        from classic_methods.period_estimation import period_estimation_forecast as base

        fn = lambda c, h, p: base(c, h, p, gate="template")
    elif method == "kalman_filter_template_gate":
        from classic_methods.kalman_filter import kalman_forecast as base

        fn = lambda c, h, p: base(c, h, p, gate="template")
    else:
        raise ValueError(f"Unknown method: {method}")
    return fn


def evaluate_chunk(method: str, profile: str, radar_type: str, split: str = "val") -> Dict[str, Dict[str, float]]:
    """Benchmark protocol on one (profile, radar type) for all error levels."""
    predict = get_predict_fn(method)
    out = {}
    for level in ERROR_LEVELS:
        dataset_dir = DEFAULT_DATASETS_ROOT / profile / radar_type / f"1000x128_{level}"
        seqs = load_dataset_sequences(dataset_dir, split=split)
        mae, hit, lat = [], [], []
        for _, ctx_vals, tgt_vals, mask_vals in seqs:
            total = len(ctx_vals)
            if total <= HORIZON_LEN + 8:
                continue
            split_idx = CONTEXT_LEN if total >= CONTEXT_LEN + HORIZON_LEN else total - HORIZON_LEN
            ctx = ctx_vals[:split_idx]
            gt = tgt_vals[split_idx:split_idx + HORIZON_LEN]
            mask = mask_vals[split_idx:split_idx + HORIZON_LEN]
            t0 = time.perf_counter()
            preds = predict(ctx, HORIZON_LEN, "PRI")
            lat.append(time.perf_counter() - t0)
            m = compute_metrics(preds, gt, tolerance=TOLERANCE, mask=mask)
            if m["valid_pulses"] > 0:
                mae.append(m["mae"])
                hit.append(m["hit_rate_pct"])
        out[f"{profile}/{radar_type}/{level}"] = {
            "mae": float(np.mean(mae)),
            "hit": float(np.mean(hit)),
            "latency_ms": float(np.mean(lat) * 1e3),
        }
    return out


def _run_worker(method: str, overrides: dict, profile: str, radar_type: str) -> dict:
    env = dict(os.environ)
    env["PULSAR_ROBUST_PARAMS"] = json.dumps(overrides)
    cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", method, profile, radar_type]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    if proc.returncode != 0:
        raise RuntimeError(f"Worker failed ({method}, {overrides}, {profile}/{radar_type}):\n{proc.stderr[-2000:]}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def evaluate_setting(pool: ThreadPoolExecutor, method: str, overrides: dict):
    futures = [
        pool.submit(_run_worker, method, overrides, profile, rtype)
        for profile in PROFILES
        for rtype in RADAR_TYPES
    ]
    return futures


def summarise(per_dataset: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    keys = list(per_dataset)
    noisy = [k for k in keys if not k.endswith("/clean")]
    return {
        "mae_all": float(np.mean([per_dataset[k]["mae"] for k in keys])),
        "mae_noisy": float(np.mean([per_dataset[k]["mae"] for k in noisy])),
        "hit_noisy": float(np.mean([per_dataset[k]["hit"] for k in noisy])),
        "latency_ms": float(np.mean([per_dataset[k]["latency_ms"] for k in keys])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Tune the robust-periodicity methods on the validation split")
    parser.add_argument("--worker", nargs=3, metavar=("METHOD", "PROFILE", "RADAR_TYPE"), help=argparse.SUPPRESS)
    parser.add_argument("--methods", nargs="*", default=list(SEARCH_SPACE) + REFERENCE_METHODS)
    parser.add_argument("--tag", default=None, help="Suffix of the output files (default: derived from --methods)")
    parser.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) - 4))
    args = parser.parse_args()

    if args.worker:
        method, profile, rtype = args.worker
        print(json.dumps(evaluate_chunk(method, profile, rtype)))
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jobs: List[tuple] = []  # (method, parameter, value, futures)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for method in args.methods:
            jobs.append((method, None, None, evaluate_setting(pool, method, {})))
            for param, grid in SEARCH_SPACE.get(method, {}).items():
                for value in grid:
                    jobs.append((method, param, value, evaluate_setting(pool, method, {param: value})))

        rows = []
        for method, param, value, futures in jobs:
            per_dataset: Dict[str, Dict[str, float]] = {}
            for fut in futures:
                per_dataset.update(fut.result())
            row = {"method": method, "parameter": param, "value": value, **summarise(per_dataset),
                   "per_dataset": per_dataset}
            rows.append(row)
            label = "defaults" if param is None else f"{param}={value}"
            print(f"{method:<34} {label:<40} val MAE all {row['mae_all']:7.3f} | "
                  f"noisy {row['mae_noisy']:7.3f} | hit {row['hit_noisy']:5.1f}% | {row['latency_ms']:7.1f} ms/seq",
                  flush=True)

    tag = args.tag or ("_".join(args.methods) if len(args.methods) <= 3 else "all")
    (OUT_DIR / f"tuning_{tag}.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")

    lines = [
        "# Validation-split tuning of the robust-periodicity methods",
        "",
        "Mean over the validation split (100 sequences per dataset, 40 datasets). "
        "`MAE all` is the tuning objective. One parameter is varied at a time; "
        "`defaults` is the setting in the source files.",
        "",
        "| Method | Setting | MAE all (us) | MAE noisy lv1-3 (us) | Hit rate noisy (%) | ms / sequence |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        label = "defaults" if r["parameter"] is None else f"`{r['parameter']}` = {r['value']}"
        lines.append(f"| `{r['method']}` | {label} | {r['mae_all']:.3f} | {r['mae_noisy']:.3f} | "
                     f"{r['hit_noisy']:.1f} | {r['latency_ms']:.1f} |")
    (OUT_DIR / f"tuning_{tag}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[SAVED] {OUT_DIR / f'tuning_{tag}.md'}")


if __name__ == "__main__":
    main()
