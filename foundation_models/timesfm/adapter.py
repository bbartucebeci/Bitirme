"""TimesFM 3.0 wrapper for LoRA Supervised Fine-Tuning and Inference."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional, Tuple

import torch
import torch.nn as nn
from peft import LoraConfig, get_peft_model, PeftModel
from timesfm import TimesFM3Forecaster


class TimesFMLoRAEngine:
    """Manages TimesFM 3.0 loading, LoRA parameter adaptation, and inference."""

    def __init__(
        self,
        model_id: str = "google/timesfm-3.0-pytorch",
        per_core_batch_size: int = 32,
        lora_r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        target_modules: Optional[list[str]] = None,
        device: str = "auto",
    ):
        self.model_id = model_id
        self.per_core_batch_size = per_core_batch_size
        self.lora_r = lora_r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        self.target_modules = target_modules or [
            "seq_attn.query_proj",
            "seq_attn.value_proj",
            "ff0",
            "ff1",
        ]

        # 1. Load base forecaster
        self.tfm = TimesFM3Forecaster.from_pretrained(
            self.model_id,
            per_core_batch_size=self.per_core_batch_size,
        )
        self.device = next(self.tfm.model.parameters()).device
        self.base_model = self.tfm.model

        # 2. Configure PEFT LoRA
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
        """Differentiable forward pass with unit scaling and numerical stability guard.

        Args:
            context_tensor: (batch_size, 1, context_len) float tensor.
            horizon: forecast horizon length.
            scale: scale factor (default: 1000.0 us -> 1.0 ms) to keep attention logits well-conditioned.

        Returns:
            Normalized point predictions tensor of shape (batch_size, horizon).
        """
        # 1. Scale from microseconds to unit range
        ctx = (context_tensor / scale).to(self.device)

        # 2. Guard against zero-variance singularity on flat constant signals (e.g. stable clean)
        std_val = ctx.std(dim=-1, keepdim=True)
        is_flat = std_val < 1e-4
        if is_flat.any():
            ctx = torch.where(is_flat, ctx + torch.randn_like(ctx) * 1e-4, ctx)

        # Call unwrapped decode to bypass @torch.no_grad()
        out_logits = self.base_model.decode.__wrapped__(
            self.peft_model,
            ctx,
            horizon=horizon,
        )
        # Median quantile (index 4 out of 9 quantiles)
        preds = out_logits[:, 0, :, 4]
        return preds

    def forward_train_multivariate(
        self,
        context_tensor: torch.Tensor,
        horizon: int = 32,
        scales: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Differentiable forward pass for 5-channel multivariate PDW context.

        Args:
            context_tensor: (batch_size, 5, context_len) float tensor.
            horizon: forecast horizon length.
            scales: (5,) or (1, 5, 1) float tensor for physical normalization.

        Returns:
            Normalized point predictions tensor of shape (batch_size, 5, horizon).
        """
        if scales is None:
            # PRI: 1000us, RF: 10000MHz, PW: 1.0us, AOA: 100.0deg, Amp: 50.0dBm
            scales = torch.tensor([1000.0, 10000.0, 1.0, 100.0, 50.0], dtype=torch.float32)

        scales_dev = scales.view(1, -1, 1).to(self.device)
        ctx = (context_tensor.to(self.device) / scales_dev)

        # Guard against zero-variance singularity on flat channels
        std_val = ctx.std(dim=-1, keepdim=True)
        is_flat = std_val < 1e-4
        if is_flat.any():
            ctx = torch.where(is_flat, ctx + torch.randn_like(ctx) * 1e-4, ctx)

        out_logits = self.base_model.decode.__wrapped__(
            self.peft_model,
            ctx,
            horizon=horizon,
        )
        # Shape: (batch_size, 5, horizon)
        preds = out_logits[:, :, :horizon, 4]
        return preds

    def save_lora_checkpoint(self, save_dir: Path):
        """Saves LoRA adapter weights and config."""
        save_dir.mkdir(parents=True, exist_ok=True)
        self.peft_model.save_pretrained(str(save_dir))
        print(f"[CHECKPOINT] LoRA weights saved to: {save_dir}")

    @classmethod
    def load_for_inference(cls, weights_dir: Optional[Path | str] = None, model_id: str = "google/timesfm-3.0-pytorch") -> TimesFM3Forecaster:
        """Loads TimesFM 3.0, optionally applying and merging trained LoRA weights."""
        tfm = TimesFM3Forecaster.from_pretrained(model_id, per_core_batch_size=32)
        if weights_dir is not None:
            weights_path = Path(weights_dir)
            if weights_path.exists():
                print(f"[LOAD] Applying LoRA adapter from: {weights_path}")
                peft_model = PeftModel.from_pretrained(tfm.model, str(weights_path))
                merged_model = peft_model.merge_and_unload()
                tfm.model = merged_model
                print("[MERGED] LoRA weights successfully fused into native TimesFM backbone.")
        return tfm

