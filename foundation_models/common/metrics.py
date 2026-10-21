"""Evaluation metrics for Electronic Warfare pulse sequence forecasting."""

from __future__ import annotations
from typing import Dict
import numpy as np


def compute_forecast_metrics(
    predictions: np.ndarray,
    ground_truth: np.ndarray,
    tolerance_us: float = 10.0,
) -> Dict[str, float]:
    """Computes MAE, RMSE, and Tactical Range-Gate Hit Rate.

    Args:
        predictions: 1D or 2D array of predicted PRI values (microseconds).
        ground_truth: 1D or 2D array of true PRI values (microseconds).
        tolerance_us: Tactical EW range-gate tolerance corridor (default: 10.0 us).

    Returns:
        Dictionary containing:
        - 'mae_us': Mean Absolute Error in microseconds
        - 'rmse_us': Root Mean Squared Error in microseconds
        - 'hit_rate_pct': Percentage of pulse predictions within tolerance
    """
    preds = np.asarray(predictions, dtype=np.float32)
    truth = np.asarray(ground_truth, dtype=np.float32)

    abs_err = np.abs(preds - truth)
    sq_err = (preds - truth) ** 2

    mae = float(np.mean(abs_err))
    rmse = float(np.sqrt(np.mean(sq_err)))
    hit_rate = float(np.mean(abs_err <= tolerance_us) * 100.0)

    return {
        "mae_us": round(mae, 3),
        "rmse_us": round(rmse, 3),
        "hit_rate_pct": round(hit_rate, 2),
    }

