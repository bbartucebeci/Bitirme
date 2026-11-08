"""TimesFM-style adapter wrapper for Toto 2.0."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

import numpy as np
import torch

from toto2 import Toto2Model


class Forecast:
    def __init__(self, forecast: np.ndarray):
        self.forecast = np.asarray(forecast, dtype=np.float32)


class Toto2Forecaster:
    """Thin wrapper exposing the predict_batch interface used by PULSAR evaluators."""

    def __init__(self, model: Toto2Model, device: str = "cpu"):
        self.model = model
        self.device = device

    @classmethod
    def load_for_inference(
        cls,
        model_id: str = "Datadog/Toto-2.0-22m",
        device: str = "auto",
        weights_dir: Optional[Path | str] = None,
    ) -> "Toto2Forecaster":
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        model = Toto2Model.from_pretrained(model_id)
        model = model.to(device).eval()
        if weights_dir is not None:
            # Toto 2.0 fine-tuning is not supported by the upstream release.
            pass
        return cls(model=model, device=device)

    def predict_batch(self, contexts: List[Any], horizon: int) -> List[Forecast]:
        arr = np.stack(contexts)
        tensor = torch.from_numpy(arr).float().to(self.device)
        if tensor.ndim == 2:
            tensor = tensor.unsqueeze(1)  # (B, 1, T)
        batch, variates, time_steps = tensor.shape
        target_mask = torch.ones_like(tensor, dtype=torch.bool, device=self.device)
        series_ids = torch.zeros(batch, variates, dtype=torch.long, device=self.device)

        decode_block_size = max(768, time_steps + horizon)
        with torch.no_grad():
            quantiles = self.model.forecast(
                {
                    "target": tensor,
                    "target_mask": target_mask,
                    "series_ids": series_ids,
                },
                horizon=horizon,
                decode_block_size=decode_block_size,
                has_missing_values=False,
            )
        # (9, B, V, H) -> median index 4
        median = quantiles[4].detach().cpu().numpy()  # (B, V, H)

        if arr.ndim == 2:
            return [Forecast(median[i, 0]) for i in range(batch)]
        return [Forecast(median[i]) for i in range(batch)]