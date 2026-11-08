"""TimesFM-style adapter wrapper for t0-gamma."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

import numpy as np
import torch

class Forecast:
    def __init__(self, forecast: np.ndarray):
        self.forecast = np.asarray(forecast, dtype=np.float32)


class T0GammaForecaster:
    """Thin wrapper exposing the predict_batch interface used by PULSAR evaluators."""

    def __init__(self, model: Any, device: str = "cpu"):
        self.model = model
        self.device = device

    @classmethod
    def load_for_inference(
        cls,
        model_id: str = "theforecastingcompany/t0-gamma",
        device: str = "auto",
        weights_dir: Optional[Path | str] = None,
    ) -> "T0GammaForecaster":
        try:
            from t0 import T0Forecaster
        except ImportError as exc:
            raise ImportError(
                "t0-gamma is not installed. Please install it with: "
                "pip install 'tfc-t0[torch]>=0.6.0' rotary-embedding-torch"
            ) from exc

        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        model = T0Forecaster.from_pretrained(model_id).eval()
        model = model.to(device)
        if weights_dir is not None:
            # t0-gamma fine-tuning is not implemented in PULSAR yet.
            pass
        return cls(model=model, device=device)

    def _to_tensor(self, contexts: List[Any]) -> torch.Tensor:
        arr = np.stack(contexts)
        return torch.from_numpy(arr).float().to(self.device)

    def predict_batch(self, contexts: List[Any], horizon: int) -> List[Forecast]:
        tensor = self._to_tensor(contexts)
        with torch.no_grad():
            out = self.model.predict(tensor, horizon=horizon, quantile_levels=[0.5])
        median = out.median.detach().cpu().numpy()

        if tensor.ndim == 2:
            # (B, H)
            return [Forecast(median[i]) for i in range(len(contexts))]
        if tensor.ndim == 3:
            # (B, V, H)
            return [Forecast(median[i]) for i in range(len(contexts))]
        raise ValueError(f"Unsupported context tensor shape: {tuple(tensor.shape)}")

    def predict_batch_covariate(
        self,
        contexts: List[Any],
        future_covariates: List[Any],
        horizon: int,
    ) -> List[Forecast]:
        ctx = self._to_tensor(contexts)
        fc = self._to_tensor(future_covariates)
        with torch.no_grad():
            out = self.model.predict(
                ctx,
                horizon=horizon,
                quantile_levels=[0.5],
                future_covariates=fc,
            )
        median = out.median.detach().cpu().numpy()
        return [Forecast(median[i]) for i in range(len(contexts))]