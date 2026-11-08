"""Pulse-level scores aggregated once per independent sequence."""

from __future__ import annotations

import numpy as np

from foundation_models.chronos2.data import CHANNELS, TOLERANCES


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
