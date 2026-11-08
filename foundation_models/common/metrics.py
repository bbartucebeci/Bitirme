"""Evaluation metrics for Electronic Warfare pulse sequence forecasting."""

from __future__ import annotations
from typing import Dict, Optional
import numpy as np


def compute_forecast_metrics(
    predictions: np.ndarray,
    ground_truth: np.ndarray,
    tolerance: float = 10.0,
    mask: Optional[np.ndarray] = None,
    unit: str = "us",
    tolerance_us: Optional[float] = None,
) -> Dict[str, float]:
    """Computes MAE, RMSE, and Tactical Range-Gate Hit Rate over valid emitter pulses.

    Args:
        predictions: 1D or 2D array of predicted values.
        ground_truth: 1D or 2D array of true emitter values.
        tolerance: Tactical EW tolerance corridor (default: 10.0 us).
        mask: Optional boolean array selecting valid emitter pulses (ignoring NOISE and ECHO).
        unit: Parameter unit string for display (us, MHz, deg, dBm).
        tolerance_us: Deprecated alias for tolerance.

    Returns:
        Dictionary containing:
        - 'mae': Mean Absolute Error
        - 'rmse': Root Mean Squared Error
        - 'hit_rate_pct': Percentage of predictions within tactical tolerance
        - 'valid_pulses_evaluated': Number of scored emitter pulses
    """
    if tolerance_us is not None:
        tolerance = tolerance_us

    preds = np.asarray(predictions, dtype=np.float32)
    truth = np.asarray(ground_truth, dtype=np.float32)

    if mask is not None:
        mask_arr = np.asarray(mask, dtype=bool)
        if mask_arr.any():
            preds = preds[mask_arr]
            truth = truth[mask_arr]

    abs_err = np.abs(preds - truth)
    sq_err = (preds - truth) ** 2

    mae = float(np.mean(abs_err)) if len(abs_err) > 0 else 0.0
    rmse = float(np.sqrt(np.mean(sq_err))) if len(sq_err) > 0 else 0.0
    hit_rate = float(np.mean(abs_err <= tolerance) * 100.0) if len(abs_err) > 0 else 0.0

    return {
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "hit_rate_pct": round(hit_rate, 2),
        "mae_us": round(mae, 3),
        "rmse_us": round(rmse, 3),
        f"mae_{unit}": round(mae, 3),
        f"rmse_{unit}": round(rmse, 3),
        "valid_pulses_evaluated": int(len(preds)),
    }

