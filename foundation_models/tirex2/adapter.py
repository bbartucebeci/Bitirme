"""TiRex-2 inference adapter for the shared PDW forecast windows."""

from __future__ import annotations

import numpy as np


MODEL_ID = "NX-AI/TiRex-2"
MEDIAN_QUANTILE_INDEX = 4  # The official nine quantiles run from 0.1 to 0.9.


def load_pipeline(model_id: str = MODEL_ID, device: str = "auto"):
    try:
        import torch
        from tirex2 import load_model
    except ImportError as exc:
        raise RuntimeError(
            "TiRex-2 is unavailable. Install foundation_models/tirex2/requirements.txt "
            "in a separate TiRex-2 environment."
        ) from exc

    chosen_device = ("cuda" if torch.cuda.is_available() else "cpu") if device == "auto" else device
    if chosen_device not in ("cpu", "cuda"):
        raise ValueError("device must be auto, cpu, or cuda")
    if chosen_device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but PyTorch cannot access it")
    return load_model(model_id, device=chosen_device)


def predict_median(model, contexts: list[np.ndarray], horizon: int, batch_size: int) -> list[np.ndarray]:
    """Return one float32 (channels, horizon) median forecast per sequence."""
    if not contexts:
        return []

    import torch
    from tirex2 import TimeseriesType

    series = [
        TimeseriesType(
            target=torch.from_numpy(np.array(context, dtype=np.float32, copy=True)),
            past_covariates=None,
            future_covariates=None,
        )
        for context in contexts
    ]
    with torch.inference_mode():
        forecasts = model.forecast(
            series,
            prediction_length=horizon,
            output_type="numpy",
            batch_size=batch_size,
        )
    if len(forecasts) != len(contexts):
        raise ValueError(f"TiRex-2 returned {len(forecasts)} forecasts for {len(contexts)} contexts")

    medians = []
    for context, forecast in zip(contexts, forecasts, strict=True):
        array = np.asarray(forecast)
        expected_shape = (context.shape[0], 9, horizon)
        if array.shape != expected_shape:
            raise ValueError(f"TiRex-2 returned {array.shape}; expected {expected_shape}")
        median = array[:, MEDIAN_QUANTILE_INDEX, :].astype(np.float32, copy=False)
        if not np.isfinite(median).all():
            raise ValueError("TiRex-2 returned a non-finite median forecast")
        medians.append(median)
    return medians
