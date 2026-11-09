"""TimesFM-style adapter wrapper and LoRA engine for t0-gamma."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

import numpy as np
import torch

from t0 import T0Forecaster


class Forecast:
    def __init__(self, forecast: np.ndarray):
        self.forecast = np.asarray(forecast, dtype=np.float32)


class T0GammaForecaster:
    """Thin wrapper exposing the predict_batch interface used by PULSAR evaluators."""

    def __init__(self, model: T0Forecaster, device: str = "cpu"):
        self.model = model
        self.device = device

    @classmethod
    def load_for_inference(
        cls,
        model_id: str = "theforecastingcompany/t0-gamma",
        device: str = "auto",
        weights_dir: Optional[Path | str] = None,
    ) -> "T0GammaForecaster":
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        model = T0Forecaster.from_pretrained(model_id).eval()
        model = model.to(device)
        if weights_dir is not None:
            weights_path = Path(weights_dir)
            if weights_path.exists():
                print(f"[LOAD] Applying LoRA adapter from: {weights_path}")
                from peft import PeftModel
                peft_model = PeftModel.from_pretrained(model, str(weights_path))
                model = peft_model.merge_and_unload()
                print("[MERGED] LoRA weights successfully fused into native t0-gamma backbone.")
            else:
                print(f"[WARN] weights_dir {weights_path} does not exist, using zero-shot model.")
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


class T0GammaLoRAEngine:
    """Manages t0-gamma loading, LoRA parameter adaptation, and fine-tuning."""

    def __init__(
        self,
        model_id: str = "theforecastingcompany/t0-gamma",
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        target_modules: Optional[list[str]] = None,
        device: str = "auto",
    ):
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.model_id = model_id
        self.lora_r = lora_r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        self.target_modules = target_modules or ["wQKV", "wO"]

        # 1. Load base model
        self.base_model = T0Forecaster.from_pretrained(model_id).to(device)

        # 2. Configure PEFT LoRA
        from peft import LoraConfig, get_peft_model
        self.lora_config = LoraConfig(
            r=self.lora_r,
            lora_alpha=self.lora_alpha,
            target_modules=self.target_modules,
            lora_dropout=self.lora_dropout,
            bias="none",
        )
        self.peft_model = get_peft_model(self.base_model, self.lora_config)

    def print_trainable_parameters(self):
        """Prints the parameter reduction summary."""
        self.peft_model.print_trainable_parameters()

    def forward_train(
        self,
        context_tensor: torch.Tensor,
        horizon: int = 32,
        scale: float = 1000.0,
    ) -> torch.Tensor:
        """Differentiable forward pass for univariate sequence."""
        ctx = context_tensor.to(self.device)
        if ctx.ndim == 3 and ctx.shape[1] == 1:
            ctx = ctx.squeeze(1)

        # Flat constant guard
        std_val = ctx.std(dim=-1, keepdim=True)
        is_flat = std_val < 1e-4
        if is_flat.any():
            ctx = torch.where(is_flat, ctx + torch.randn_like(ctx) * 1e-4, ctx)

        series, _, _, _ = self.peft_model._series_from_array(ctx, horizon, None, None, None)
        scaled, loc_scale = self.peft_model.scaler.scale_input(series)
        res = self.peft_model(scaled)
        rescaled = self.peft_model.scaler.rescale_predictions(res, loc_scale, self.peft_model.patch_size)
        patch_idx = (ctx.shape[-1] // self.peft_model.patch_size) - 1
        preds = rescaled[:, patch_idx, :, 10]  # median quantile (index 10)
        return preds / scale

    def forward_train_multivariate(
        self,
        context_tensor: torch.Tensor,
        horizon: int = 32,
        scales: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Differentiable forward pass for 5-channel multivariate PDW context."""
        ctx = context_tensor.to(self.device)
        series, batch_shape, _, _ = self.peft_model._series_from_array(ctx, horizon, None, None, None)
        scaled, loc_scale = self.peft_model.scaler.scale_input(series)
        res = self.peft_model(scaled)
        rescaled = self.peft_model.scaler.rescale_predictions(res, loc_scale, self.peft_model.patch_size)
        patch_idx = (ctx.shape[-1] // self.peft_model.patch_size) - 1
        preds = rescaled[:, patch_idx, :, 10]
        if batch_shape is not None:
            preds = preds.reshape((*batch_shape, horizon))
        if scales is not None:
            scales_dev = scales.view(1, -1, 1).to(self.device)
            return preds / scales_dev
        return preds

    def save_lora_checkpoint(self, save_dir: Path):
        """Saves LoRA adapter weights and config."""
        save_dir.mkdir(parents=True, exist_ok=True)
        self.peft_model.save_pretrained(str(save_dir))
        print(f"[CHECKPOINT] LoRA weights saved to: {save_dir}")

    @classmethod
    def load_for_inference(
        cls,
        weights_dir: Optional[Path | str] = None,
        model_id: str = "theforecastingcompany/t0-gamma",
        device: str = "auto",
    ) -> T0GammaForecaster:
        """Loads t0-gamma, applying and merging trained LoRA weights if provided."""
        return T0GammaForecaster.load_for_inference(model_id=model_id, device=device, weights_dir=weights_dir)
