"""Shared dataset loading, outlier pre-filtering, and evaluation metrics for Classic Methods.

Designed to be 100% compatible with the PULSAR TimesFM 3.0 evaluation protocol
(Context = 96 pulses, Forecast Horizon = 32 pulses, Emitter Masking for NOISE/ECHO)
while adding standard EE / statistical forecasting metrics (RMSE, MAE, MAPE, MedAE,
Tactical Gate Hit Rate, and Inference Latency).
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
DEFAULT_DATASETS_ROOT = PROJECT_ROOT / "datasets" / "single_radar"

RADAR_TYPES = ["stable", "jitter", "stagger", "dwell_and_switch", "sliding"]
ERROR_LEVELS = ["clean", "error_lv1", "error_lv2", "error_lv3"]

PARAM_SPECS = {
    "PRI": {"name": "PRI", "slug": "pri", "unit": "us", "default_tol": 10.0},
    "Frequency": {"name": "Carrier Frequency", "slug": "frequency", "unit": "MHz", "default_tol": 2.0},
    "PW": {"name": "Pulse Width", "slug": "pw", "unit": "us", "default_tol": 0.1},
    "AOA": {"name": "Angle of Arrival", "slug": "aoa", "unit": "deg", "default_tol": 2.0},
    "Amplitude": {"name": "Amplitude", "slug": "amplitude", "unit": "dBm", "default_tol": 2.0},
}


def ensure_datasets_exist(
    datasets_root: Path = DEFAULT_DATASETS_ROOT,
    profile_mode: str = "fixed",
    radar_types: List[str] = RADAR_TYPES,
    error_levels: List[str] = ERROR_LEVELS,
    smoke_test: bool = False,
) -> None:
    """Checks if benchmark datasets exist; generates them if missing."""
    seq_count = 10 if smoke_test else 1000
    missing = False
    for rtype in radar_types:
        for elevel in error_levels:
            folder = datasets_root / profile_mode / rtype / f"{seq_count}x128_{elevel}" / "test"
            if not folder.exists():
                missing = True
                break

    if missing:
        print(f"[INFO] Generating missing {profile_mode} benchmark datasets (seq_count={seq_count})...")
        gen_script = PROJECT_ROOT / "dataset_generator" / "generate_datasets.py"
        cmd = [
            sys.executable,
            str(gen_script),
            "--radar-type",
            "all_single",
            "--profile-mode",
            profile_mode,
            "--error-level",
            "all",
        ]
        if smoke_test:
            cmd.append("--smoke-test")
        subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))


def load_sequence_arrays(
    csv_path: Path,
    target_param: str = "PRI",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reads a single PDW CSV file and extracts context, ground-truth, and emitter mask."""
    df = pd.read_csv(csv_path)

    # Drop anchor pulse at index 0 where Measured_Delta_TOA == 0.0
    if len(df) > 1 and "Measured_Delta_TOA" in df.columns and df["Measured_Delta_TOA"].iloc[0] == 0.0:
        df = df.iloc[1:].reset_index(drop=True)

    if "Radar_ID" in df.columns:
        emitter_mask = (df["Radar_ID"].astype(str) == "R_SINGLE").to_numpy(dtype=bool)
    else:
        emitter_mask = np.ones(len(df), dtype=bool)

    param_upper = target_param.upper()
    if param_upper in ["PRI", "MEASURED_DELTA_TOA"]:
        ctx_vals = df["Measured_Delta_TOA"].to_numpy(dtype=np.float64)
        tgt_vals = df["PRI"].to_numpy(dtype=np.float64) if "PRI" in df.columns else ctx_vals.copy()
    elif target_param in df.columns:
        ctx_vals = df[target_param].to_numpy(dtype=np.float64)
        tgt_vals = ctx_vals.copy()
    else:
        raise ValueError(f"Target parameter '{target_param}' not found in {csv_path}")

    return ctx_vals, tgt_vals, emitter_mask


def load_dataset_sequences(
    dataset_dir: Path,
    split: str = "test",
    max_seqs: Optional[int] = None,
    target_param: str = "PRI",
) -> List[Tuple[str, np.ndarray, np.ndarray, np.ndarray]]:
    """Loads sequences for a dataset directory and split."""
    split_dir = dataset_dir / split
    if not split_dir.exists():
        raise FileNotFoundError(f"Split directory not found: {split_dir}")

    sequences = []
    seq_files = sorted(list(split_dir.glob("seq_*.csv")))
    if seq_files:
        if max_seqs is not None and max_seqs > 0:
            seq_files = seq_files[:max_seqs]
        for f in seq_files:
            ctx, tgt, mask = load_sequence_arrays(f, target_param=target_param)
            sequences.append((f.stem, ctx, tgt, mask))
        return sequences

    comb_file = split_dir / "sequences.csv"
    if comb_file.exists():
        df_all = pd.read_csv(comb_file)
        unique_ids = df_all["sequence_id"].unique()
        if max_seqs is not None and max_seqs > 0:
            unique_ids = unique_ids[:max_seqs]
        for sid in unique_ids:
            df_seq = df_all[df_all["sequence_id"] == sid].sort_values("pulse_index")
            if len(df_seq) > 1 and df_seq["Measured_Delta_TOA"].iloc[0] == 0.0:
                df_seq = df_seq.iloc[1:].reset_index(drop=True)
            mask = (
                (df_seq["Radar_ID"].astype(str) == "R_SINGLE").to_numpy(dtype=bool)
                if "Radar_ID" in df_seq.columns
                else np.ones(len(df_seq), dtype=bool)
            )
            param_upper = target_param.upper()
            if param_upper in ["PRI", "MEASURED_DELTA_TOA"]:
                ctx = df_seq["Measured_Delta_TOA"].to_numpy(dtype=np.float64)
                tgt = df_seq["PRI"].to_numpy(dtype=np.float64) if "PRI" in df_seq.columns else ctx.copy()
            else:
                ctx = df_seq[target_param].to_numpy(dtype=np.float64)
                tgt = ctx.copy()
            sequences.append((str(sid), ctx, tgt, mask))
        return sequences

    raise FileNotFoundError(f"No sequence files found in {split_dir}")


def clean_pri_context(context: np.ndarray) -> np.ndarray:
    """Applies ESM front-end validation gating to Observed Delta-TOA context.

    In real ESM receivers:
    1. False alarms / multipath echoes split a single PRI into two short intervals
       (e.g., t_1 + t_2 approx PRI, where t_1 < 0.55 * median_pri). Merging adjacent
       split intervals restores the true pulse interval.
    2. Missing pulses (POI < 1.0) create integer-multiple spikes (2x or 3x PRI).
       Replacing or subdividing extreme outliers prevents corrupting period/state estimators.
    """
    x = np.asarray(context, dtype=np.float64).copy()
    if len(x) < 4:
        return x

    med = float(np.median(x))
    if med <= 0:
        return x

    # Step 1: Reconstruct split intervals caused by false/multipath pulses
    reconstructed: List[float] = []
    i = 0
    n = len(x)
    while i < n:
        val = x[i]
        if val < 0.55 * med and (i + 1) < n:
            combined = val + x[i + 1]
            # If merging brings it close to 1x or 2x median PRI, merge them
            if abs(combined - med) < abs(x[i + 1] - med) or combined < 1.45 * med:
                reconstructed.append(combined)
                i += 2
                continue
            else:
                # Isolated glitch pulse; skip it
                i += 1
                continue
        reconstructed.append(val)
        i += 1

    if len(reconstructed) < 4:
        reconstructed = list(x)

    arr = np.asarray(reconstructed, dtype=np.float64)
    med = float(np.median(arr))

    # Step 2: Unpack 2x / 3x PRI missing-pulse intervals or clip extreme outliers
    expanded: List[float] = []
    for val in arr:
        ratio = val / med
        if 1.65 <= ratio <= 2.45:
            # 1 missing pulse -> 2 intervals of val / 2
            expanded.extend([val / 2.0, val / 2.0])
        elif 2.45 < ratio <= 3.45:
            # 2 missing pulses -> 3 intervals of val / 3
            expanded.extend([val / 3.0, val / 3.0, val / 3.0])
        elif 0.55 <= ratio < 1.65:
            expanded.append(val)
        else:
            expanded.append(med)

    return np.asarray(expanded, dtype=np.float64)


def compute_metrics(
    predictions: np.ndarray,
    ground_truth: np.ndarray,
    tolerance: float = 10.0,
    mask: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """Computes comprehensive error & tactical performance metrics.

    Metrics:
    - RMSE (Root Mean Squared Error): Penalizes large prediction errors / phase slips.
    - MAE (Mean Absolute Error): Average L1 prediction error in physical units.
    - MedAE (Median Absolute Error): Outlier-robust typical error.
    - MAPE_pct (Mean Absolute Percentage Error): Relative error (%).
    - Gate_Hit_Rate_pct: % of predictions within tactical EW tolerance (+/- tolerance).
    """
    preds = np.asarray(predictions, dtype=np.float64)
    truth = np.asarray(ground_truth, dtype=np.float64)

    if mask is not None:
        mask_arr = np.asarray(mask, dtype=bool)
        if mask_arr.any():
            preds = preds[mask_arr]
            truth = truth[mask_arr]

    if len(preds) == 0:
        return {
            "rmse": 0.0,
            "mae": 0.0,
            "medae": 0.0,
            "mape_pct": 0.0,
            "hit_rate_pct": 0.0,
            "valid_pulses": 0,
        }

    err = preds - truth
    abs_err = np.abs(err)
    sq_err = err ** 2

    rmse = float(np.sqrt(np.mean(sq_err)))
    mae = float(np.mean(abs_err))
    medae = float(np.median(abs_err))
    denom = np.maximum(np.abs(truth), 1e-6)
    mape_pct = float(np.mean(abs_err / denom) * 100.0)
    hit_rate_pct = float(np.mean(abs_err <= tolerance) * 100.0)

    return {
        "rmse": rmse,
        "mae": mae,
        "medae": medae,
        "mape_pct": mape_pct,
        "hit_rate_pct": hit_rate_pct,
        "valid_pulses": int(len(preds)),
    }


def save_forecast_plot(
    plot_path: Path,
    title: str,
    context: np.ndarray,
    ground_truth: np.ndarray,
    predictions: np.ndarray,
    tolerance: float = 10.0,
    param_label: str = "PRI",
    unit: str = "μs",
    show_ctx_pts: int = 40,
) -> None:
    """Renders and saves a diagnostic parameter forecast plot matching the TimesFM 3.0 style.

    Includes:
    - Observed context pulses (tab:blue, 'o-')
    - Ground truth future pulses (tab:green, 's-')
    - Model forecast curve (tab:red, '^--')
    - Tactical Tolerance corridor (+/- tolerance around ground truth)
    - Shaded prediction error gap
    - Protected y-axis span to prevent deceptive auto-zoom on flat signals
    """
    context_len = len(context)
    horizon_len = len(ground_truth)

    plt.figure(figsize=(13, 5))

    actual_ctx_pts = min(show_ctx_pts, context_len)
    x_ctx = np.arange(context_len - actual_ctx_pts, context_len)
    x_horiz = np.arange(context_len, context_len + horizon_len)

    # 1. Observed history
    plt.plot(
        x_ctx,
        context[-actual_ctx_pts:],
        "o-",
        color="tab:blue",
        markersize=4,
        label=f"Observed Context ({param_label})",
    )

    # 2. Ground truth
    plt.plot(
        x_horiz,
        ground_truth,
        "s-",
        color="tab:green",
        markersize=4,
        label="Ground Truth (Actual Future)",
    )

    # 3. Model prediction
    plt.plot(
        x_horiz,
        predictions,
        "^--",
        color="tab:red",
        markersize=5,
        label="Model Forecast",
    )

    # 4. Forecast boundary
    plt.axvline(
        x=context_len - 0.5,
        color="black",
        linestyle="--",
        alpha=0.6,
        label="Forecast Horizon Boundary",
    )

    # 5. Tactical Tolerance Corridor (shaded green)
    plt.fill_between(
        x_horiz,
        ground_truth - tolerance,
        ground_truth + tolerance,
        color="tab:green",
        alpha=0.18,
        label=f"Tactical Gate (±{tolerance:g} {unit})",
    )

    # 6. Prediction Error Gap (shaded red)
    plt.fill_between(
        x_horiz,
        ground_truth,
        predictions,
        color="tab:red",
        alpha=0.15,
        label="Prediction Error Gap",
    )

    # Prevent micro-scale auto-zoom illusion on flat signals (e.g. stable radar)
    all_visible = np.concatenate([context[-actual_ctx_pts:], ground_truth, predictions])
    y_min, y_max = float(all_visible.min()), float(all_visible.max())
    min_span = max(tolerance * 3.0, 1.0)
    if (y_max - y_min) < min_span:
        y_center = (y_max + y_min) / 2.0
        plt.ylim(y_center - min_span * 0.6, y_center + min_span * 0.6)

    plt.title(title, fontsize=13, fontweight="bold")
    plt.xlabel("Pulse Index (n)")
    plt.ylabel(f"{param_label} ({unit})")
    plt.legend(loc="upper right", frameon=True)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()

    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=180)
    plt.close()


def evaluate_method_across_benchmarks(
    method_name: str,
    method_slug: str,
    predict_fn: Callable[[np.ndarray, int, str], np.ndarray],
    profile_mode: str = "fixed",
    target_param: str = "PRI",
    radar_types: List[str] = RADAR_TYPES,
    error_levels: List[str] = ERROR_LEVELS,
    context_len: int = 96,
    horizon_len: int = 32,
    max_test_seqs: int = 200,
    smoke_test: bool = False,
    results_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """Runs a classic forecasting method across all radar types and error levels."""
    ensure_datasets_exist(
        datasets_root=DEFAULT_DATASETS_ROOT,
        profile_mode=profile_mode,
        radar_types=radar_types,
        error_levels=error_levels,
        smoke_test=smoke_test,
    )

    spec = PARAM_SPECS.get(target_param, PARAM_SPECS["PRI"])
    unit = spec["unit"]
    tolerance = spec["default_tol"]
    seq_count = 10 if smoke_test else 1000

    if results_dir is None:
        results_dir = PROJECT_ROOT / "results" / "classic_methods" / method_slug / f"{profile_mode}_{spec['slug']}"
    results_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = results_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    print("=" * 88)
    print(f"BENCHMARKING: {method_name} | Target: {target_param} ({unit}) | Mode: {profile_mode}")
    print(f"Context: up to {context_len} pulses | Horizon: {horizon_len} pulses | Gate Tolerance: +/-{tolerance:g} {unit}")
    print("=" * 88)

    for rtype in radar_types:
        for elevel in error_levels:
            folder_name = f"{seq_count}x128_{elevel}"
            dataset_dir = DEFAULT_DATASETS_ROOT / profile_mode / rtype / folder_name
            if not dataset_dir.exists():
                print(f"[SKIP] Missing dataset: {dataset_dir}")
                continue

            test_seqs = load_dataset_sequences(
                dataset_dir=dataset_dir,
                split="test",
                max_seqs=max_test_seqs,
                target_param=target_param,
            )

            rmse_list, mae_list, medae_list, mape_list, hit_list, latency_us_list = [], [], [], [], [], []

            for idx, (seq_id, ctx_vals, tgt_vals, mask_vals) in enumerate(test_seqs):
                total_len = len(ctx_vals)
                if total_len <= horizon_len + 8:
                    continue

                if total_len >= context_len + horizon_len:
                    ctx = ctx_vals[:context_len]
                    gt = tgt_vals[context_len : context_len + horizon_len]
                    mask = mask_vals[context_len : context_len + horizon_len]
                else:
                    # Fallback when POI drops reduce sequence length slightly below 128
                    split_idx = total_len - horizon_len
                    ctx = ctx_vals[:split_idx]
                    gt = tgt_vals[split_idx : split_idx + horizon_len]
                    mask = mask_vals[split_idx : split_idx + horizon_len]

                t0 = time.perf_counter()
                preds = predict_fn(ctx, horizon_len, target_param)
                elapsed_us = (time.perf_counter() - t0) * 1e6

                # Save diagnostic forecast plot for the first test sequence (matching TimesFM evaluate.py)
                if idx == 0:
                    plot_path = plots_dir / f"{rtype}_{elevel}.png"
                    display_unit = "μs" if unit == "us" else unit
                    plot_title = f"{method_name} {spec['name']} Forecast | {rtype}/{folder_name} ({seq_id})"
                    save_forecast_plot(
                        plot_path=plot_path,
                        title=plot_title,
                        context=ctx,
                        ground_truth=gt,
                        predictions=preds,
                        tolerance=tolerance,
                        param_label=spec["name"],
                        unit=display_unit,
                    )

                m = compute_metrics(preds, gt, tolerance=tolerance, mask=mask)
                if m["valid_pulses"] > 0:
                    rmse_list.append(m["rmse"])
                    mae_list.append(m["mae"])
                    medae_list.append(m["medae"])
                    mape_list.append(m["mape_pct"])
                    hit_list.append(m["hit_rate_pct"])
                    latency_us_list.append(elapsed_us)

            if not rmse_list:
                continue

            row = {
                "method": method_name,
                "radar_type": rtype,
                "error_level": elevel,
                "evaluated_sequences": len(rmse_list),
                f"rmse_{unit}": round(float(np.mean(rmse_list)), 3),
                f"mae_{unit}": round(float(np.mean(mae_list)), 3),
                f"medae_{unit}": round(float(np.median(medae_list)), 3),
                "mape_pct": round(float(np.mean(mape_list)), 3),
                "gate_hit_rate_pct": round(float(np.mean(hit_list)), 2),
                "latency_us_per_seq": round(float(np.mean(latency_us_list)), 2),
            }
            rows.append(row)
            print(
                f"  {rtype:<18} | {elevel:<10} | "
                f"RMSE: {row[f'rmse_{unit}']:>7.2f} {unit} | "
                f"MAE: {row[f'mae_{unit}']:>7.2f} {unit} | "
                f"MAPE: {row['mape_pct']:>5.2f}% | "
                f"HitRate: {row['gate_hit_rate_pct']:>6.1f}% | "
                f"Time: {row['latency_us_per_seq']:>6.1f} us"
            )

    df_res = pd.DataFrame(rows)
    csv_path = results_dir / "metrics.csv"
    df_res.to_csv(csv_path, index=False)

    md_path = results_dir / "report.md"
    lines = [
        f"# {method_name} Benchmark Report [{spec['name']} - {profile_mode.capitalize()}]",
        "",
        f"- **Context Window**: {context_len} pulses | **Forecast Horizon**: {horizon_len} pulses",
        f"- **Tactical Gate Tolerance**: +/-{tolerance:g} {unit}",
        "",
        f"| Radar Type | Error Level | Seqs | RMSE ({unit}) | MAE ({unit}) | MedAE ({unit}) | MAPE (%) | Gate Hit Rate (+/-{tolerance:g} {unit}) | Latency (us/seq) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['radar_type']}` | `{r['error_level']}` | {r['evaluated_sequences']} | "
            f"**{r[f'rmse_{unit}']:.2f}** | {r[f'mae_{unit}']:.2f} | {r[f'medae_{unit}']:.2f} | "
            f"{r['mape_pct']:.2f}% | {r['gate_hit_rate_pct']:.1f}% | {r['latency_us_per_seq']:.1f} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[SAVED] CSV: {csv_path}")
    print(f"[SAVED] Markdown Report: {md_path}\n")
    return df_res

