"""PULSAR: TimesFM 3.0 Joint 5-Channel Multivariate Supervised Fine-Tuning (LoRA SFT).

Trains a unified LoRA adapter targeting Attention and MLP projections using a
tactical priority weighted Huber loss across all 5 PDW channels (PRI, RF, PW, AOA, Amp).
"""

from __future__ import annotations
import argparse
import math
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.optim import AdamW

from foundation_models.common.dataset import (
    create_unified_multivariate_dataloader,
    MULTIVARIATE_CHANNELS,
    MULTIVARIATE_SCALES,
    MULTIVARIATE_WEIGHTS,
    MULTIVARIATE_TOLERANCES,
    MULTIVARIATE_UNITS,
)
from foundation_models.common.metrics import compute_forecast_metrics
from foundation_models.timesfm.adapter import TimesFMLoRAEngine
from foundation_models.timesfm.evaluate_multivariate import (
    evaluate_single_multivariate_dataset,
    export_multivariate_benchmark_results,
)

# Path resolution
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
DEFAULT_DATASETS_ROOT = PROJECT_ROOT / "datasets" / "single_radar"
DEFAULT_CHECKPOINTS_DIR = PROJECT_ROOT / "models" / "timesfm_lora" / "multivariate_fixed"
DEFAULT_RESULTS_ROOT = PROJECT_ROOT / "results" / "timesfm_3.0"


def validate_multivariate_epoch(
    lora_engine: TimesFMLoRAEngine,
    val_loader: Any,
    scales_tensor: torch.Tensor,
    weights_tensor: torch.Tensor,
    horizon: int = 32,
) -> Tuple[float, Dict[str, float]]:
    """Evaluates validation loss and per-channel MAEs on valid emitter pulses."""
    lora_engine.peft_model.eval()
    total_loss = 0.0
    channel_maes = {ch: [] for ch in MULTIVARIATE_CHANNELS}
    count = 0

    scales_view = scales_tensor.view(1, 5, 1).to(lora_engine.device)

    with torch.no_grad():
        for ctx_batch, tgt_batch, mask_batch in val_loader:
            tgt_norm = (tgt_batch.to(lora_engine.device) / scales_view)
            preds_norm = lora_engine.forward_train_multivariate(
                ctx_batch,
                horizon=horizon,
                scales=scales_tensor,
            )

            mask_dev = mask_batch.to(lora_engine.device)

            batch_loss = torch.tensor(0.0, device=lora_engine.device)
            for c_idx in range(5):
                pred_c = preds_norm[:, c_idx, :]
                tgt_c = tgt_norm[:, c_idx, :]
                if mask_dev.any():
                    l_c = F.smooth_l1_loss(pred_c[mask_dev], tgt_c[mask_dev], beta=0.01)
                else:
                    l_c = F.smooth_l1_loss(pred_c, tgt_c, beta=0.01)
                batch_loss = batch_loss + weights_tensor[c_idx] * l_c

            total_loss += float(batch_loss.item()) * len(tgt_batch)
            count += len(tgt_batch)

            preds_phys = (preds_norm * scales_view).detach().cpu().numpy()
            tgt_phys = tgt_batch.numpy()
            mask_np = mask_batch.numpy()

            for p_seq, g_seq, m_seq in zip(preds_phys, tgt_phys, mask_np):
                for c_idx, ch_name in enumerate(MULTIVARIATE_CHANNELS):
                    met = compute_forecast_metrics(
                        p_seq[c_idx],
                        g_seq[c_idx],
                        tolerance=MULTIVARIATE_TOLERANCES[c_idx],
                        mask=m_seq,
                        unit=MULTIVARIATE_UNITS[c_idx],
                    )
                    channel_maes[ch_name].append(met["mae"])

    avg_loss = total_loss / max(1, count)
    avg_channel_maes = {ch: float(np.mean(channel_maes[ch])) for ch in MULTIVARIATE_CHANNELS}
    return avg_loss, avg_channel_maes


def build_multivariate_comparison_report(
    zero_shot_csv: Path,
    lora_csv: Path,
    output_report: Path,
):
    """Side-by-side comparison of Zero-Shot vs LoRA for all 5 channels."""
    if not zero_shot_csv.exists() or not lora_csv.exists():
        print(f"[SKIP] Comparison report skipped: missing {zero_shot_csv} or {lora_csv}")
        return

    df_zs = pd.read_csv(zero_shot_csv)
    df_lora = pd.read_csv(lora_csv)

    merged = pd.merge(df_zs, df_lora, on=["radar_type", "error_level"], suffixes=("_zs", "_lora"))

    lines = [
        "# TimesFM 3.0 Joint 5-Channel Multivariate: Zero-Shot vs. LoRA Comparison\n",
        f"**Generated on**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        "| Radar Type | Error Level | PRI ZS (μs) | PRI LoRA (μs) | PRI Δ (%) | RF ZS (MHz) | RF LoRA (MHz) | PW LoRA (μs) | AOA LoRA (°) | Amp LoRA (dBm) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for _, row in merged.iterrows():
        pri_zs = row["mae_pri_zs"]
        pri_lora = row["mae_pri_lora"]
        rf_zs = row["mae_frequency_zs"]
        rf_lora = row["mae_frequency_lora"]
        pw_lora = row["mae_pw_lora"]
        aoa_lora = row["mae_aoa_lora"]
        amp_lora = row["mae_amplitude_lora"]

        pri_delta = ((pri_lora - pri_zs) / max(1e-5, pri_zs)) * 100.0
        pri_str = f"**{pri_lora:.2f}**" if pri_lora < pri_zs else f"{pri_lora:.2f}"
        rf_str = f"**{rf_lora:.2f}**" if rf_lora < rf_zs else f"{rf_lora:.2f}"

        lines.append(
            f"| `{row['radar_type']}` | `{row['error_level']}` | "
            f"{pri_zs:.2f} | {pri_str} | {pri_delta:+.1f}% | "
            f"{rf_zs:.2f} | {rf_str} | {pw_lora:.2f} | {aoa_lora:.2f} | {amp_lora:.2f} |"
        )

    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[SAVED] Multivariate Comparative Report: {output_report}")


def main():
    parser = argparse.ArgumentParser(description="PULSAR: TimesFM 3.0 Joint 5-Channel LoRA SFT Training")
    parser.add_argument("--profile-mode", choices=["fixed", "varying"], default="fixed")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs (default: 3)")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size (default: 64)")
    parser.add_argument("--lr", type=float, default=1e-4, help="Peak learning rate (default: 1e-4)")
    parser.add_argument("--lora-r", type=int, default=16, help="LoRA rank (default: 16)")
    parser.add_argument("--lora-alpha", type=int, default=32, help="LoRA alpha (default: 32)")
    parser.add_argument("--save-dir", type=Path, default=DEFAULT_CHECKPOINTS_DIR)
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)

    args = parser.parse_args()

    datasets_root = DEFAULT_DATASETS_ROOT / args.profile_mode

    print("=" * 80)
    print("PULSAR: TimesFM 3.0 Joint 5-Channel Multivariate SFT Training")
    print("=" * 80)
    print(f"Profile: {args.profile_mode} | Epochs: {args.epochs} | Batch Size: {args.batch_size} | LR: {args.lr}")
    print(f"Channels (5): {', '.join(MULTIVARIATE_CHANNELS)}")
    print(f"Tactical Weights: PRI: 35% | RF: 25% | PW: 15% | AOA: 15% | Amplitude: 10%")
    print(f"LoRA Target: Attention + MLP Projections (r={args.lora_r}, α={args.lora_alpha})")
    print("=" * 80 + "\n")

    # 1. Initialize LoRA Engine
    lora_engine = TimesFMLoRAEngine(
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
    )
    lora_engine.print_trainable_parameters()

    # 2. Build Unified 5-Channel DataLoaders
    print("\nLoading unified 5-channel training (14,000 seqs) and validation (2,000 seqs)...")
    train_loader = create_unified_multivariate_dataloader(
        datasets_root=datasets_root,
        profile_mode=args.profile_mode,
        split="train",
        context_len=args.context_len,
        horizon_len=args.horizon,
        batch_size=args.batch_size,
        shuffle=True,
    )
    val_loader = create_unified_multivariate_dataloader(
        datasets_root=datasets_root,
        profile_mode=args.profile_mode,
        split="val",
        context_len=args.context_len,
        horizon_len=args.horizon,
        batch_size=args.batch_size,
        shuffle=False,
    )
    print(f"Train Batches: {len(train_loader)} | Val Batches: {len(val_loader)}")

    scales_tensor = torch.tensor(MULTIVARIATE_SCALES, dtype=torch.float32)
    weights_tensor = torch.tensor(MULTIVARIATE_WEIGHTS, dtype=torch.float32, device=lora_engine.device)
    scales_view = scales_tensor.view(1, 5, 1).to(lora_engine.device)

    # 3. Optimizer & Scheduler
    optimizer = AdamW(
        [p for p in lora_engine.peft_model.parameters() if p.requires_grad],
        lr=args.lr,
        weight_decay=1e-2,
    )
    total_steps = len(train_loader) * args.epochs
    warmup_steps = int(0.1 * total_steps)

    def lr_lambda(step: int) -> float:
        if step < warmup_steps:
            return float(step) / float(max(1, warmup_steps))
        progress = float(step - warmup_steps) / float(max(1, total_steps - warmup_steps))
        return max(0.05, 0.5 * (1.0 + math.cos(math.pi * progress)))

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

    # 4. Training Loop
    best_val_loss = float("inf")
    checkpoint_best = PROJECT_ROOT / "models" / "timesfm_lora" / f"multivariate_{args.profile_mode}" / "best_model"
    checkpoint_best.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "-" * 80)
    print("Starting Joint 5-Channel SFT Training (FP32 Precision, Weighted Huber Loss)...")
    print("-" * 80)

    t_start = time.time()
    for epoch in range(1, args.epochs + 1):
        lora_engine.peft_model.train()
        train_loss = 0.0
        t_epoch = time.time()

        for step, (ctx_batch, tgt_batch, mask_batch) in enumerate(train_loader):
            optimizer.zero_grad()
            tgt_norm = (tgt_batch.to(lora_engine.device) / scales_view)

            preds_norm = lora_engine.forward_train_multivariate(
                ctx_batch,
                horizon=args.horizon,
                scales=scales_tensor,
            )

            mask_dev = mask_batch.to(lora_engine.device)

            batch_loss = torch.tensor(0.0, device=lora_engine.device)
            for c_idx in range(5):
                pred_c = preds_norm[:, c_idx, :]
                tgt_c = tgt_norm[:, c_idx, :]
                if mask_dev.any():
                    l_c = F.smooth_l1_loss(pred_c[mask_dev], tgt_c[mask_dev], beta=0.01)
                else:
                    l_c = F.smooth_l1_loss(pred_c, tgt_c, beta=0.01)
                batch_loss = batch_loss + weights_tensor[c_idx] * l_c

            batch_loss.backward()
            torch.nn.utils.clip_grad_norm_(lora_engine.peft_model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()

            train_loss += float(batch_loss.item()) * len(tgt_batch)

            if (step + 1) % 50 == 0 or (step + 1) == len(train_loader):
                cur_lr = scheduler.get_last_lr()[0]
                pri_mae = float(((preds_norm[:, 0, :] * 1000.0) - tgt_batch[:, 0, :].to(lora_engine.device)).abs().mean().item())
                rf_mae = float(((preds_norm[:, 1, :] * 10000.0) - tgt_batch[:, 1, :].to(lora_engine.device)).abs().mean().item())
                print(f"Epoch [{epoch}/{args.epochs}] Batch [{step+1:3d}/{len(train_loader)}] Loss: {batch_loss.item():.5f} | PRI MAE: {pri_mae:.1f} us | RF MAE: {rf_mae:.1f} MHz | LR: {cur_lr:.2e}")

        epoch_train_loss = train_loss / len(train_loader.dataset)
        val_loss, val_maes = validate_multivariate_epoch(
            lora_engine=lora_engine,
            val_loader=val_loader,
            scales_tensor=scales_tensor,
            weights_tensor=weights_tensor,
            horizon=args.horizon,
        )

        epoch_time = time.time() - t_epoch
        print(
            f"--> Epoch {epoch} Complete ({epoch_time:.1f}s) | "
            f"Train Loss: {epoch_train_loss:.5f} | "
            f"Val Loss: {val_loss:.5f} | "
            f"Val PRI MAE: {val_maes['PRI']:.2f} us | "
            f"Val RF MAE: {val_maes['Frequency']:.2f} MHz"
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            lora_engine.save_lora_checkpoint(checkpoint_best)
            print(f"    * New best validation loss! Saved checkpoint to {checkpoint_best}")

    t_train = time.time() - t_start
    print("\n" + "=" * 80)
    print(f"Joint Multivariate Training Complete in {t_train:.1f}s ({t_train/60:.1f} min)")
    print("=" * 80)

    # 5. Automated Post-Training Evaluation on 4,000 Test Sequences
    print("\nLoading Best Fine-Tuned Model for Full Test Split Evaluation...")
    tfm_eval = TimesFMLoRAEngine.load_for_inference(weights_dir=checkpoint_best)

    results_dir = DEFAULT_RESULTS_ROOT / "lora_sft" / f"multivariate_{args.profile_mode}"
    plots_dir = results_dir / "plots"

    radar_types = ["stable", "jitter", "stagger", "dwell_and_switch", "sliding"]
    error_levels = ["clean", "error_lv1", "error_lv2", "error_lv3"]

    test_results = []
    for rtype in radar_types:
        for elevel in error_levels:
            folder_name = f"1000x128_{elevel}"
            dataset_dir = datasets_root / rtype / folder_name
            dataset_display = f"{rtype}/{folder_name}"

            res = evaluate_single_multivariate_dataset(
                tfm=tfm_eval,
                dataset_dir=dataset_dir,
                dataset_display=dataset_display,
                radar_type=rtype,
                error_level=elevel,
                context_len=args.context_len,
                horizon_len=args.horizon,
                max_test_seqs=200,
                plots_dir=plots_dir,
            )
            if res:
                test_results.append(res)

    if test_results:
        export_multivariate_benchmark_results(
            test_results,
            results_dir,
            title=f"TimesFM 3.0 Joint 5-Channel LoRA SFT Benchmark [{args.profile_mode.capitalize()}]",
        )

        # 6. Generate Comparative Report
        zs_csv = DEFAULT_RESULTS_ROOT / "zero_shot" / f"multivariate_{args.profile_mode}" / "metrics.csv"
        lora_csv = results_dir / "metrics.csv"
        comp_md = DEFAULT_RESULTS_ROOT / f"comparison_zero_shot_vs_lora_multivariate_{args.profile_mode}.md"
        build_multivariate_comparison_report(zs_csv, lora_csv, comp_md)


if __name__ == "__main__":
    main()

