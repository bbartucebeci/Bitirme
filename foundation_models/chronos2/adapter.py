"""Small Chronos-2 inference adapter; dependencies load only when needed."""

from __future__ import annotations

from pathlib import Path

import numpy as np


MODEL_ID = "amazon/chronos-2"


def load_pipeline(model_id: str = MODEL_ID, device: str = "auto"):
    try:
        import torch
        from chronos import Chronos2Pipeline
    except ImportError as exc:
        raise RuntimeError(
            "Chronos-2 is unavailable. Install foundation_models/chronos2/requirements.txt "
            "in the experiment environment."
        ) from exc
    chosen_device = ("cuda" if torch.cuda.is_available() else "cpu") if device == "auto" else device
    if chosen_device not in ("cpu", "cuda"):
        raise ValueError("device must be auto, cpu, or cuda")
    if chosen_device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but PyTorch cannot access it")
    return Chronos2Pipeline.from_pretrained(model_id, device_map=chosen_device)


def predict_median(pipeline, contexts: list[np.ndarray], horizon: int, batch_size: int) -> list[np.ndarray]:
    """Return physical-unit point forecasts of shape (channels, horizon)."""
    if not contexts:
        return []
    _, medians = pipeline.predict_quantiles(
        inputs=contexts,
        prediction_length=horizon,
        quantile_levels=[0.5],
        batch_size=batch_size,
        context_length=contexts[0].shape[1],
    )
    forecasts = []
    for context, median in zip(contexts, medians, strict=True):
        array = median.detach().cpu().numpy() if hasattr(median, "detach") else np.asarray(median)
        if array.shape != (context.shape[0], horizon):
            raise ValueError(f"Chronos returned {array.shape}; expected {(context.shape[0], horizon)}")
        forecasts.append(array.astype(np.float32, copy=False))
    return forecasts


def checkpoint_path(profile_mode: str, target_param: str) -> Path:
    from foundation_models.chronos2.data import PROJECT_ROOT

    return PROJECT_ROOT / "models" / "chronos2_lora" / profile_mode / target_param.lower() / "best_model"
