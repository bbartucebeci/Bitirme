"""Evaluation metrics for Electronic Warfare pulse sequence forecasting."""

from __future__ import annotations
from typing import Dict, List, Optional
import numpy as np

from foundation_models.common.dataset import CHANNELS, TOLERANCES


def compute_forecast_metrics(
    predictions: np.ndarray,
    ground_truth: np.ndarray,
    tolerance: float = 10.0,
    mask: Optional[np.ndarray] = None,
    unit: str = "us",
    tolerance_us: Optional[float] = None,
    is_angular: bool = False,
) -> Dict[str, float]:
    """Computes MAE, RMSE, and Tactical Range-Gate Hit Rate over valid emitter pulses.

    Supports circular modular angular distance for Angle-of-Arrival (AOA) bearing
    measurements, resolving 0°/360° phase wrap-around.

    Args:
        predictions: 1D or 2D array of predicted values.
        ground_truth: 1D or 2D array of true emitter values.
        tolerance: Tactical EW tolerance corridor (default: 10.0 us).
        mask: Optional boolean array selecting valid emitter pulses (ignoring NOISE and ECHO).
        unit: Parameter unit string for display (us, MHz, deg, dBm).
        tolerance_us: Deprecated alias for tolerance.
        is_angular: If True, enforces circular modular angular error.

    Returns:
        Dictionary containing:
        - 'mae': Mean Absolute Error
        - 'rmse': Root Mean Squared Error
        - 'hit_rate_pct': Percentage of predictions within tactical tolerance
        - 'valid_pulses_evaluated': Number of scored emitter pulses
        - 'circular_mae': Circular modular MAE for AOA
        - 'circular_hit_rate_pct': Circular modular gate hit rate for AOA
    """
    if tolerance_us is not None:
        tolerance = tolerance_us

    preds = np.asarray(predictions, dtype=np.float32)
    truth = np.asarray(ground_truth, dtype=np.float32)

    if mask is not None:
        mask_arr = np.asarray(mask, dtype=bool)
        preds = preds[mask_arr]
        truth = truth[mask_arr]

    if len(preds) == 0:
        return {
            "mae": 0.0,
            "rmse": 0.0,
            "hit_rate_pct": 0.0,
            "mae_us": 0.0,
            "rmse_us": 0.0,
            f"mae_{unit}": 0.0,
            f"rmse_{unit}": 0.0,
            "valid_pulses_evaluated": 0,
            "circular_mae": 0.0,
            "circular_hit_rate_pct": 0.0,
        }

    raw_diff = preds - truth
    abs_err = np.abs(raw_diff)

    is_aoa = is_angular or unit.lower() in ["deg", "degree", "degrees"]
    if is_aoa:
        # Circular angular difference on the circle [0, 360)
        eval_err = np.minimum(abs_err % 360.0, 360.0 - (abs_err % 360.0))
        circular_mae = float(np.mean(eval_err))
        circular_hit = float(np.mean(eval_err <= tolerance) * 100.0)
    else:
        eval_err = abs_err
        circular_mae = float(np.mean(abs_err))
        circular_hit = float(np.mean(abs_err <= tolerance) * 100.0)

    sq_err = eval_err ** 2
    mae = float(np.mean(eval_err))
    rmse = float(np.sqrt(np.mean(sq_err)))
    hit_rate = float(np.mean(eval_err <= tolerance) * 100.0)

    return {
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "hit_rate_pct": round(hit_rate, 2),
        "mae_us": round(mae, 3),
        "rmse_us": round(rmse, 3),
        f"mae_{unit}": round(mae, 3),
        f"rmse_{unit}": round(rmse, 3),
        "valid_pulses_evaluated": int(len(preds)),
        "circular_mae": round(circular_mae, 3),
        "circular_hit_rate_pct": round(circular_hit, 2),
    }


def score_window(prediction: np.ndarray, target: np.ndarray, mask: np.ndarray) -> dict[str, float] | None:
    """Score emitter pulses only; an all-noise horizon has no valid score."""
    if prediction.shape != target.shape or prediction.shape[0] != len(CHANNELS):
        raise ValueError(f"Expected matching 5-channel forecasts, got {prediction.shape} and {target.shape}")
    if mask.shape != (target.shape[1],):
        raise ValueError("Emitter mask and forecast horizon differ")
    if not mask.any():
        return None
    result: dict[str, float] = {"valid_pulses_evaluated": int(mask.sum())}
    for channel_idx, name in enumerate(CHANNELS):
        errors = np.abs(prediction[channel_idx, mask] - target[channel_idx, mask])
        if not np.isfinite(errors).all():
            raise ValueError(f"Non-finite {name} forecast or target")
        slug = name.lower()
        result[f"mae_{slug}"] = round(float(errors.mean()), 3)
        result[f"rmse_{slug}"] = round(float(np.sqrt(np.mean(errors**2))), 3)
        result[f"hit_rate_{slug}"] = round(float(np.mean(errors <= TOLERANCES[name]) * 100.0), 2)
        if name == "AOA":
            angular_errors = np.minimum(errors % 360.0, 360.0 - errors % 360.0)
            result["circular_mae_aoa"] = round(float(angular_errors.mean()), 3)
            result["circular_hit_rate_aoa"] = round(
                float(np.mean(angular_errors <= TOLERANCES[name]) * 100.0), 2
            )
    return result


def score_single(prediction: np.ndarray, target: np.ndarray, mask: np.ndarray, name: str) -> dict[str, float] | None:
    """Keep the TimesFM MAE/RMSE/hit-rate definitions for one parameter."""
    if prediction.shape != target.shape or prediction.shape != (len(mask),):
        raise ValueError("Prediction, target, and emitter mask lengths differ")
    if not mask.any():
        return None
    errors = np.abs(prediction[mask] - target[mask])
    if not np.isfinite(errors).all():
        raise ValueError(f"Non-finite {name} forecast or target")
    result = {
        "mae": round(float(errors.mean()), 3),
        "rmse": round(float(np.sqrt(np.mean(errors**2))), 3),
        "hit_rate_pct": round(float(np.mean(errors <= TOLERANCES[name]) * 100.0), 2),
        "valid_pulses_evaluated": int(mask.sum()),
    }
    if name == "AOA":
        angular_errors = np.minimum(errors % 360.0, 360.0 - errors % 360.0)
        result["circular_mae"] = round(float(angular_errors.mean()), 3)
        result["circular_hit_rate_pct"] = round(
            float(np.mean(angular_errors <= TOLERANCES[name]) * 100.0), 2
        )
    return result


def aggregate(sequence_scores: list[dict[str, float]]) -> dict[str, float]:
    if not sequence_scores:
        raise ValueError("No sequences with genuine emitter targets were scored")
    keys = [key for key in sequence_scores[0] if key != "valid_pulses_evaluated"]
    return {
        **{key: float(np.mean([row[key] for row in sequence_scores])) for key in keys},
        "valid_pulses_evaluated": sum(int(row["valid_pulses_evaluated"]) for row in sequence_scores),
    }
