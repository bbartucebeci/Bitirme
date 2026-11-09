"""PULSAR: t0-gamma Joint 5-Channel Multivariate Supervised Fine-Tuning (LoRA SFT).

Trains a unified LoRA adapter targeting Attention projections using a
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
from foundation_models.t0_gamma.adapter import T0GammaLoRAEngine, T0GammaForecaster
from foundation_models.t0_gamma.evaluate_multivariate import (
    evaluate_single_multivariate_dataset,
    export_multivariate_benchmark_results,
)

# Path resolution
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
DEFAULT_DATASETS_ROOT = PROJECT_ROOT / "datasets" / "single_radar"
DEFAULT_CHECKPOINTS_DIR = PROJECT_ROOT / "models" / "t0_gamma_lora"
DEFAULT_RESULTS_ROOT = PROJECT_ROOT / "results" / "t0_gamma"


def validate_multivariate_epoch(
    lora_engine: T0GammaLoRAEngine,
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
            tgt_norm = tgt_batch.to(lora_engine.device) / scales_view
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
    profile_mode: str = "fixed",
):
    """Generates Markdown comparison of Zero-Shot vs LoRA across all 5 channels."""
    if not zero_shot_csv.exists() or not lora_csv.exists():
        print(f"[SKIP] Multivariate comparison skipped: missing {zero_shot_csv} or {lora_csv}")
        return

    df_zs = pd.read_csv(zero_shot_csv)
    df_lora = pd.read_csv(lora_csv)

    merged = pd.merge(
        df_zs,
        df_lora,
        on=["radar_type", "error_level"],
        suffixes=("_zero_shot", "_lora"),
    )

    lines = [
        f"# t0-gamma Joint 5-Channel Multivariate: Zero-Shot vs. LoRA SFT Comparison [{profile_mode.capitalize()}]\n",
        f"**Generated on**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        "| Radar Type | Error Level | PRI MAE (μs) ZS | PRI MAE LoRA | PRI Hit ZS | PRI Hit LoRA | RF MAE (MHz) ZS | RF MAE LoRA | PW MAE (μs) ZS | PW MAE LoRA |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for _, row in merged.iterrows():
        pri_zs = row["mae_pri_zero_shot"]
        pri_lo = row["mae_pri_lora"]
        hit_zs = row["hit_rate_pri_zero_shot"]
        hit_lo = row["hit_rate_pri_lora"]
        rf_zs = row["mae_frequency_zero_shot"]
        rf_lo = row["mae_frequency_lora"]
        pw_zs = row["mae_pw_zero_shot"]
        pw_lo = row["mae_pw_lora"]

        pri_str = f"**{pri_lo:.2f}**" if pri_lo < pri_zs else f"{pri_lo:.2f}"
        hit_str = f"**{hit_lo:.1f}%**" if hit_lo > hit_zs else f"{hit_lo:.1f}%"
        rf_str = f"**{rf_lo:.2f}**" if rf_lo < rf_zs else f"{rf_lo:.2f}"
        pw_str = f"**{pw_lo:.2f}**" if pw_lo < pw_zs else f"{pw_lo:.2f}"

        lines.append(
            f"| `{row['radar_type']}` | `{row['error_level']}` | "
            f"{pri_zs:.2f} | {pri_str} | {hit_zs:.1f}% | {hit_str} | "
            f"{rf_zs:.2f} | {rf_str} | {pw_zs:.2f} | {pw_str} |"
        )

    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[SAVED] Multivariate Comparison Report: {output_report}")


def main():
    parser = argparse.ArgumentParser(description="PULSAR: t0-gamma Joint 5-Channel Multivariate LoRA SFT")
    parser.add_argument("--profile-mode", choices=["fixed", "varying"], default="fixed")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs (default: 3)")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size (default: 32)")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate (default: 1e-4)")
    parser.add_argument("--lora-r", type=int, default=16, help="LoRA rank (default: 16)")
    parser.add_argument("--lora-alpha", type=int, default=32, help="LoRA alpha (default: 32)")
    parser.add_argument("--save-dir", type=Path, default=DEFAULT_CHECKPOINTS_DIR)
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--max-train-seqs", type=int, default=None)
    parser.add_argument("--max-val-seqs", type=int, default=None)

    args = parser.parse_args()

    datasets_root = DEFAULT_DATASETS_ROOT / args.profile_mode
    checkpoint_dir = args.save_dir / f"multivariate_{args.profile_mode}" / "best_model"

    print("=" * 80)
    print(f"PULSAR: t0-gamma Joint 5-Channel Multivariate LoRA SFT Training")
    print("=" * 80)
    print(f"Profile: {args.profile_mode} | Epochs: {args.epochs} | Batch Size: {args.batch_size} | LR: {args.lr}")
    print(f"Channels: {', '.join(MULTIVARIATE_CHANNELS)}")
    print(f"Weights: {MULTIVARIATE_WEIGHTS.tolist()} | Scales: {MULTIVARIATE_SCALES.tolist()}")
    print("=" * 80 + "\n")

    # 1. Initialize Engine
    lora_engine = T0GammaLoRAEngine(
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
    )
    lora_engine.print_trainable_parameters()

    # 2. Build Dataloaders
    print(f"\nBuilding Unified Multivariate DataLoaders for {args.profile_mode} profile...")
    train_loader = create_unified_multivariate_dataloader(
        datasets_root=datasets_root,
        profile_mode=args.profile_mode,
        split="train",
        context_len=args.context_len,
        horizon_len=args.horizon,
        batch_size=args.batch_size,
        shuffle=True,
        max_seqs_per_dataset=args.max_train_seqs,
    )
    val_loader = create_unified_multivariate_dataloader(
        datasets_root=datasets_root,
        profile_mode=args.profile_mode,
        split="val",
        context_len=args.context_len,
        horizon_len=args.horizon,
        batch_size=args.batch_size,
        shuffle=False,
        max_seqs_per_dataset=args.max_val_seqs,
    )
    print(f"Train Batches: {len(train_loader)} | Val Batches: {len(val_loader)}")

    # 3. Setup Optimizer and Scheduler
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
    scales_tensor = torch.from_numpy(MULTIVARIATE_SCALES).float().to(lora_engine.device)
    weights_tensor = torch.from_numpy(MULTIVARIATE_WEIGHTS).float().to(lora_engine.device)
    scales_view = scales_tensor.view(1, 5, 1)

    best_val_loss = float("inf")
    checkpoint_dir.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "-" * 80)
    print("Starting Multivariate LoRA Training...")
    print("-" * 80)

    t_start = time.time()
    global_step = 0

    for epoch in range(1, args.epochs + 1):
        lora_engine.peft_model.train()
        train_loss = 0.0
        t_epoch = time.time()

        for step, (ctx_batch, tgt_batch, mask_batch) in enumerate(train_loader):
            optimizer.zero_grad()
            tgt_norm = tgt_batch.to(lora_engine.device) / scales_view

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
            global_step += 1

            if (step + 1) % 25 == 0 or (step + 1) == len(train_loader):
                cur_lr = scheduler.get_last_lr()[0]
                print(
                    f"Epoch [{epoch}/{args.epochs}] Batch [{step+1:3d}/{len(train_loader)}] "
                    f"Weighted Huber Loss: {batch_loss.item():.5f} | LR: {cur_lr:.2e}"
                )

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
            f"Train Loss: {epoch_train_loss:.5f} | Val Loss: {val_loss:.5f} | "
            f"PRI MAE: {val_maes['PRI']:.2f} us | RF MAE: {val_maes['Frequency']:.2f} MHz"
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            lora_engine.save_lora_checkpoint(checkpoint_dir)
            print(f"    * Best checkpoint saved to {checkpoint_dir}")

    total_time = time.time() - t_start
    print("\n" + "=" * 80)
    print(f"Multivariate Training Complete in {total_time:.1f}s ({total_time/60:.1f} min)")
    print("=" * 80)

    # 5. Full Test Evaluation
    print("\nEvaluating Best Model on Full Test Set across 20 Benchmark Datasets...")
    best_model = T0GammaForecaster.load_for_inference(weights_dir=checkpoint_dir)

    target_dir = DEFAULT_RESULTS_ROOT / "lora_sft" / f"multivariate_{args.profile_mode}"
    plots_dir = target_dir / "plots"

    radar_types = ["stable", "jitter", "stagger", "dwell_and_switch", "sliding"]
    error_levels = ["clean", "error_lv1", "error_lv2", "error_lv3"]

    results = []
    for rtype in radar_types:
        for elevel in error_levels:
            dataset_dir = None
            for pattern in [f"1000x128_{elevel}", f"10x128_{elevel}"]:
                candidate = datasets_root / rtype / pattern
                if candidate.exists():
                    dataset_dir = candidate
                    break
            if dataset_dir is None:
                continue

            dataset_display = f"{rtype}/{dataset_dir.name}"
            res = evaluate_single_multivariate_dataset(
                model=best_model,
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
                results.append(res)

    if results:
        title = f"t0-gamma LoRA SFT Joint 5-Channel Benchmark [{args.profile_mode.capitalize()}]"
        export_multivariate_benchmark_results(results, target_dir, title=title)

        zs_csv = DEFAULT_RESULTS_ROOT / "zero_shot" / f"multivariate_{args.profile_mode}" / "metrics.csv"
        lora_csv = target_dir / "metrics.csv"
        comp_report = DEFAULT_RESULTS_ROOT / "comparisons" / f"comparison_zero_shot_vs_lora_multivariate_{args.profile_mode}.md"
        build_multivariate_comparison_report(zs_csv, lora_csv, comp_report, profile_mode=args.profile_mode)


if __name__ == "__main__":
    main()
