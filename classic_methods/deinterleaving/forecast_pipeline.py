"""End-to-End Deinterleave -> Forecast Pipeline (Milestone 3 / WBS 3.3).

Executes the full two-stage radar signal processing chain:
1. Deinterleaving: Segregates multi-radar interleaved PDWs into emitter tracks
   (using Online Streaming / DBSCAN / Oracle).
2. PRI Forecasting: Pipes each recovered track into downstream predictors:
   - Period Estimation (autocorrelation / phase-locked template)
   - Kalman Filter Bank (multiple-model state estimator)
   - Chronos-2 LoRA (Foundation Model fine-tuned on varying dataset)
   - TimesFM LoRA (Foundation Model fine-tuned on varying dataset)
3. Performance Analysis:
   - Computes Tactical Gate Hit Rate (within +/- 10 us corridor) over 32-pulse horizon.
   - Measures the "Deinterleaving Penalty": Single-Radar Isolated vs Oracle Interleaved vs Deinterleaved.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .dbscan_deinterleaver import DBSCANDeinterleaver
from .online_stream_deinterleaver import OnlineStreamDeinterleaver
from .hybrid_cascade_deinterleaver import HybridCascadeDeinterleaver

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.period_estimation import period_estimation_forecast
from classic_methods.kalman_filter import kalman_forecast
from foundation_models.common.plotting import save_forecast_plot

DEFAULT_DATASETS_DIR = PROJECT_ROOT / "datasets" / "interleaved"
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results" / "deinterleaving" / "forecast_pipeline"

ERROR_LEVELS = ["clean", "error_lv1", "error_lv2", "error_lv3"]
RADAR_TYPES = ["stable", "jitter", "stagger", "dwell_and_switch", "sliding"]
PREDICTOR_CHOICES = ["period_estimation", "kalman_filter", "chronos2_lora", "timesfm_lora", "student_gru", "all"]


def deinterleave_oracle(df_pulses: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Perfect deinterleaving using ground-truth Radar_ID for baseline ceiling comparison."""
    tracks = {}
    for r_id in df_pulses["Radar_ID"].unique():
        if r_id == "NOISE":
            continue
        mask = df_pulses["Radar_ID"] == r_id
        trk = df_pulses[mask].copy().sort_values(by="TOA").reset_index(drop=True)
        toas = trk["TOA"].to_numpy()
        intra_pri = np.concatenate([[toas[1] - toas[0]], np.diff(toas)]) if len(toas) > 1 else np.array([0.0])
        trk["Intra_Track_PRI"] = intra_pri
        tracks[str(r_id)] = trk
    return tracks


def run_predictor_forecast(
    predictor_name: str,
    context_pri: np.ndarray,
    horizon_len: int = 32,
    chronos_pipeline: Any = None,
    timesfm_model: Any = None,
    student_model: Any = None,
    **kwargs,
) -> np.ndarray:
    """Dispatches prediction to the chosen predictor."""
    if predictor_name == "period_estimation":
        return period_estimation_forecast(context_pri, horizon_len=horizon_len, target_param="PRI")
    elif predictor_name == "kalman_filter":
        return kalman_forecast(context_pri, horizon_len=horizon_len, target_param="PRI")
    elif predictor_name == "chronos2_lora":
        from foundation_models.chronos2.adapter import predict_median
        # context_pri: 1D array of shape (context_len,)
        ctx_2d = context_pri[np.newaxis, :]  # shape: (1, context_len)
        preds_list = predict_median(chronos_pipeline, contexts=[ctx_2d], horizon=horizon_len, batch_size=1)
        return preds_list[0][0]  # shape: (horizon_len,)
    elif predictor_name == "student_gru":
        import torch
        if student_model is None:
            raise ValueError("student_model must be provided for predictor 'student_gru'")
        with torch.no_grad():
            ctx_t = torch.tensor(context_pri, dtype=torch.float32).unsqueeze(0)
            preds = student_model(ctx_t)
            return preds.squeeze(0).cpu().numpy()
    elif predictor_name == "timesfm_lora":
        # TimesFM forecast wrapper
        res = timesfm_model.forecast(context_pri, horizon_len=horizon_len)
        return res
    else:
        raise ValueError(f"Unknown predictor: {predictor_name}")


def evaluate_forecast_track(
    pred_pri: np.ndarray,
    target_pri: np.ndarray,
    tol_us: float = 10.0,
) -> Dict[str, float]:
    """Computes Tactical Gate Hit Rate, MAE, and RMSE for a single track forecast."""
    errors = np.abs(pred_pri - target_pri)
    hit_mask = errors <= tol_us
    hit_rate = float(np.mean(hit_mask)) * 100.0
    mae = float(np.mean(errors))
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    medae = float(np.median(errors))

    return {
        "hit_rate_pct": round(hit_rate, 2),
        "mae_us": round(mae, 3),
        "rmse_us": round(rmse, 3),
        "medae_us": round(medae, 3),
    }


def run_end_to_end_benchmark(
    deinterleaver_name: str = "online_stream",
    predictor_name: str = "period_estimation",
    error_levels: List[str] = ERROR_LEVELS,
    max_sequences: int = 20,
    datasets_dir: Path = DEFAULT_DATASETS_DIR,
    output_dir: Path = DEFAULT_RESULTS_DIR,
    chronos_pipeline: Any = None,
    timesfm_model: Any = None,
    student_model: Any = None,
    **kwargs,
) -> pd.DataFrame:
    """Evaluates the full Deinterleave -> Forecast pipeline across test sequences."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize deinterleaver
    if deinterleaver_name == "online_stream":
        deinterleaver = OnlineStreamDeinterleaver(gate_threshold=2.5, alpha=0.15, min_confirm_pulses=5)
    elif deinterleaver_name == "dbscan":
        deinterleaver = DBSCANDeinterleaver(eps=2.0, min_samples=6)
    elif deinterleaver_name == "hybrid":
        deinterleaver = HybridCascadeDeinterleaver(dbscan_eps=2.0, dbscan_min_samples=6)
    elif deinterleaver_name == "oracle":
        deinterleaver = None
    else:
        raise ValueError(f"Unknown deinterleaver: {deinterleaver_name}")

    summary_rows: List[Dict[str, Any]] = []

    print("=" * 80)
    print("PULSAR END-TO-END DEINTERLEAVE -> FORECAST PIPELINE (MILESTONE 3)")
    print(f"Deinterleaver: {deinterleaver_name.upper()}")
    print(f"Predictor:     {predictor_name.upper()}")
    print(f"Error Levels:  {', '.join(error_levels)}")
    print(f"Sequences:     {max_sequences} per condition")
    print("=" * 80)

    for elevel in error_levels:
        ds_folder = datasets_dir / f"5radars_1000x128_{elevel}" / "test"
        if not ds_folder.exists():
            continue

        seq_files = sorted(ds_folder.glob("seq_*.csv"))[:max_sequences]
        track_results: List[Dict[str, Any]] = []

        for sfile in seq_files:
            df_seq = pd.read_csv(sfile)
            if df_seq.empty:
                continue

            # 1. Deinterleave into tracks
            if deinterleaver_name == "oracle":
                tracks_dict = deinterleave_oracle(df_seq)
            else:
                _, tracks_dict, _ = deinterleaver.deinterleave(df_seq)

            # 2. Forecast PRI for each extracted track
            for trk_id, trk_df in tracks_dict.items():
                if len(trk_df) < 64:  # Minimum pulses: at least 32 context + 32 horizon
                    continue

                dominant_radar = trk_df["Radar_ID"].mode()[0] if "Radar_ID" in trk_df.columns else "UNKNOWN"
                if dominant_radar == "NOISE":
                    continue

                # Ground truth intra-emitter PRI
                pri_vals = trk_df["Intra_Track_PRI"].to_numpy()
                horiz_len = 32
                if len(pri_vals) < horiz_len + 32:
                    continue

                # Take the final 32 pulses as forecast horizon
                target_pri = pri_vals[-horiz_len:]
                # Take up to 96 preceding pulses as context (FIFO window)
                available_ctx = len(pri_vals) - horiz_len
                ctx_window = min(96, available_ctx)
                context_pri = pri_vals[available_ctx - ctx_window : available_ctx]

                # 3. Forecast
                t_pred_start = time.perf_counter()
                pred_pri = run_predictor_forecast(
                    predictor_name,
                    context_pri,
                    horizon_len=horiz_len,
                    chronos_pipeline=chronos_pipeline,
                    timesfm_model=timesfm_model,
                    student_model=student_model,
                )
                pred_ms = (time.perf_counter() - t_pred_start) * 1000.0

                metrics = evaluate_forecast_track(pred_pri, target_pri, tol_us=10.0)
                metrics["radar_id"] = dominant_radar
                metrics["sequence_id"] = sfile.stem
                metrics["error_level"] = elevel
                metrics["latency_ms"] = round(pred_ms, 3)
                track_results.append(metrics)

        if not track_results:
            continue

        # Aggregate metrics across all tracks in this error level
        avg_hit_rate = float(np.mean([r["hit_rate_pct"] for r in track_results]))
        avg_mae = float(np.mean([r["mae_us"] for r in track_results]))
        avg_rmse = float(np.mean([r["rmse_us"] for r in track_results]))
        avg_lat = float(np.mean([r["latency_ms"] for r in track_results]))

        row_summary = {
            "deinterleaver": deinterleaver_name,
            "predictor": predictor_name,
            "error_level": elevel,
            "tracks_evaluated": len(track_results),
            "hit_rate_pct": round(avg_hit_rate, 2),
            "mae_us": round(avg_mae, 3),
            "rmse_us": round(avg_rmse, 3),
            "avg_latency_ms": round(avg_lat, 3),
        }
        summary_rows.append(row_summary)

        print(f"--> [{elevel}] Tracks: {len(track_results)} | Hit Rate: {avg_hit_rate:.1f}% | MAE: {avg_mae:.2f} us | Latency: {avg_lat:.2f} ms")

        # Breakdown by radar type
        df_tr = pd.DataFrame(track_results)
        for r_id, grp in df_tr.groupby("radar_id"):
            print(f"      {r_id:12s} -> Hit Rate: {grp['hit_rate_pct'].mean():.1f}% | MAE: {grp['mae_us'].mean():.2f} us")

    df_out = pd.DataFrame(summary_rows)
    out_csv = output_dir / f"pipeline_{deinterleaver_name}_{predictor_name}.csv"
    df_out.to_csv(out_csv, index=False)
    print(f"\n[SUCCESS] Pipeline evaluation saved to: {out_csv}")
    return df_out


def main():
    parser = argparse.ArgumentParser(description="PULSAR End-to-End Deinterleave -> Forecast Benchmark")
    parser.add_argument("--deinterleaver", type=str, default="online_stream", choices=["online_stream", "dbscan", "hybrid", "oracle"])
    parser.add_argument("--predictor", type=str, default="period_estimation", choices=PREDICTOR_CHOICES)
    parser.add_argument("--error-levels", nargs="+", default=ERROR_LEVELS)
    parser.add_argument("--max-sequences", type=int, default=20)
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_RESULTS_DIR))

    args = parser.parse_args()

    chronos_p = None
    if args.predictor in ["chronos2_lora", "all"]:
        from foundation_models.chronos2.adapter import load_pipeline
        chronos_weights = (PROJECT_ROOT / "models" / "lora_sft" / "chronos2" / "varying" / "pri" / "best_model").resolve()
        print(f"[INFO] Loading Chronos-2 LoRA checkpoint: {chronos_weights}...")
        chronos_p = load_pipeline(chronos_weights)

    student_m = None
    if args.predictor in ["student_gru", "all"]:
        import torch
        from models.distillation.student_models import CompactGRUStudent
        student_m = CompactGRUStudent(input_dim=1, hidden_dim=48, num_layers=2, horizon_len=32)
        model_path = PROJECT_ROOT / "models" / "distillation" / "student_gru_fp32.pt"
        if model_path.exists():
            student_m.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
            print(f"[INFO] Loaded trained Student GRU weights from: {model_path}")
        student_m.eval()

    run_end_to_end_benchmark(
        deinterleaver_name=args.deinterleaver,
        predictor_name=args.predictor,
        error_levels=args.error_levels,
        max_sequences=args.max_sequences,
        output_dir=Path(args.output_dir),
        chronos_pipeline=chronos_p,
        student_model=student_m,
    )


if __name__ == "__main__":
    main()
