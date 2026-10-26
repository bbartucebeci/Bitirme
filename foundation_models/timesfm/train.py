"""Supervised Fine-Tuning (SFT) for TimesFM 3.0 via LoRA on PDW Datasets."""

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

from foundation_models.common.dataset import create_unified_pdw_dataloader, load_dataset_sequences
from foundation_models.common.metrics import compute_forecast_metrics
from foundation_models.common.plotting import save_forecast_plot
from foundation_models.timesfm.adapter import TimesFMLoRAEngine
from foundation_models.timesfm.evaluate import evaluate_single_dataset, export_benchmark_results

# Path resolution
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
DEFAULT_DATASETS_ROOT = PROJECT_ROOT / "datasets" / "single_radar"
DEFAULT_CHECKPOINTS_DIR = PROJECT_ROOT / "models" / "timesfm_lora"


def validate_epoch(
    lora_engine: TimesFMLoRAEngine,
    val_loader: Any,
    horizon: int = 32,
    beta: float = 5.0,
    tolerance: float = 10.0,
    scale: float = 1000.0,
) -> Tuple[float, float, float]:
    """Evaluates validation loss, MAE, and Tactical Hit Rate without gradient computation."""
    lora_engine.peft_model.eval()
    total_loss = 0.0
    mae_list, hit_rate_list = [], []
    count = 0
    device_type = "cuda" if "cuda" in str(lora_engine.device) else "cpu"

    with torch.no_grad():
        for ctx_batch, tgt_batch in val_loader:
            tgt_norm = (tgt_batch / scale).to(lora_engine.device)
            preds_norm = lora_engine.forward_train(ctx_batch, horizon=horizon, scale=scale)
            loss = F.smooth_l1_loss(preds_norm, tgt_norm, beta=beta / scale)

            total_loss += float(loss.item()) * len(tgt_batch)
            count += len(tgt_batch)

            preds_val = (preds_norm * scale).detach().cpu().numpy()
            tgt_val = tgt_batch.numpy()
            for p, g in zip(preds_val, tgt_val):
                m = compute_forecast_metrics(p, g, tolerance_us=tolerance)
                mae_list.append(m["mae_us"])
                hit_rate_list.append(m["hit_rate_pct"])

    avg_loss = total_loss / max(1, count)
    avg_mae = float(np.mean(mae_list)) if mae_list else 0.0
    avg_hit = float(np.mean(hit_rate_list)) if hit_rate_list else 0.0
    return avg_loss, avg_mae, avg_hit


def build_comparison_report(
    zero_shot_csv: Path,
    lora_csv: Path,
    output_report: Path,
):
    """Generates a side-by-side Markdown comparison of Zero-Shot vs LoRA."""
    if not zero_shot_csv.exists() or not lora_csv.exists():
        print(f"[SKIP] Comparison report skipped: missing {zero_shot_csv} or {lora_csv}")
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
        "# TimesFM 3.0: Zero-Shot vs. LoRA Fine-Tuned Benchmark Comparison\n",
        f"**Generated on**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        "| Radar Type | Error Level | Zero-Shot MAE (μs) | LoRA MAE (μs) | MAE Δ (%) | Zero-Shot Hit Rate | LoRA Hit Rate | Hit Rate Δ |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for _, row in merged.iterrows():
        zs_mae = row["mae_us_zero_shot"]
        lora_mae = row["mae_us_lora"]
        zs_hit = row["gate_hit_rate_pct_zero_shot"]
        lora_hit = row["gate_hit_rate_pct_lora"]

        # Improvement calculations
        mae_delta_pct = ((lora_mae - zs_mae) / max(1e-5, zs_mae)) * 100.0
        hit_delta_pct = lora_hit - zs_hit

        mae_str = f"**{lora_mae:.2f}**" if lora_mae < zs_mae else f"{lora_mae:.2f}"
        hit_str = f"**{lora_hit:.1f}%**" if lora_hit > zs_hit else f"{lora_hit:.1f}%"

        lines.append(
            f"| `{row['radar_type']}` | `{row['error_level']}` | "
            f"{zs_mae:.2f} | {mae_str} | {mae_delta_pct:+.1f}% | "
            f"{zs_hit:.1f}% | {hit_str} | {hit_delta_pct:+.1f}% |"
        )

    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[SAVED] Comparative Report: {output_report}")


def main():
    parser = argparse.ArgumentParser(description="PULSAR: TimesFM 3.0 Supervised Fine-Tuning (LoRA SFT)")
    parser.add_argument("--profile-mode", choices=["fixed", "varying"], default="fixed")
    parser.add_argument("--target-col", choices=["Measured_Delta_TOA", "Frequency", "PW"], default="Measured_Delta_TOA", help="Target parameter column")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs (default: 3)")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size (default: 64)")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate (default: 1e-4)")
    parser.add_argument("--huber-beta", type=float, default=None, help="Huber loss transition threshold (default: auto)")
    parser.add_argument("--scale", type=float, default=None, help="Normalization scale factor (default: auto)")
    parser.add_argument("--lora-r", type=int, default=16, help="LoRA rank (default: 16)")
    parser.add_argument("--lora-alpha", type=int, default=32, help="LoRA alpha (default: 32)")
    parser.add_argument("--save-dir", type=Path, default=DEFAULT_CHECKPOINTS_DIR)
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--tolerance", type=float, default=None, help="Tactical tolerance corridor (default: auto)")
    parser.add_argument("--tolerance-us", type=float, default=None, help="Deprecated alias for --tolerance")

    args = parser.parse_args()

    # Parameter metadata
    if args.target_col == "Measured_Delta_TOA":
        param_name = "PRI"
        param_unit = "us"
        default_tol = 10.0
        default_scale = 1000.0
        default_huber = 5.0
        param_slug = ""
    elif args.target_col == "Frequency":
        param_name = "Carrier Frequency"
        param_unit = "MHz"
        default_tol = 2.0
        default_scale = 1000.0
        default_huber = 5.0
        param_slug = "frequency"
    elif args.target_col == "PW":
        param_name = "Pulse Width"
        param_unit = "us"
        default_tol = 0.1
        default_scale = 1.0
        default_huber = 0.05
        param_slug = "pw"
    else:
        param_name = args.target_col
        param_unit = "units"
        default_tol = 1.0
        default_scale = 1.0
        default_huber = 1.0
        param_slug = args.target_col.lower()

    tolerance = args.tolerance or args.tolerance_us or default_tol
    scale = args.scale or default_scale
    huber_beta = args.huber_beta or default_huber

    datasets_root = DEFAULT_DATASETS_ROOT / args.profile_mode

    print("=" * 75)
    print(f"PULSAR: TimesFM 3.0 LoRA SFT Training [{param_name} - {args.target_col}]")
    print("=" * 75)
    print(f"Profile: {args.profile_mode} | Epochs: {args.epochs} | Batch Size: {args.batch_size} | Scale: {scale}")
    print(f"LR: {args.lr} | Huber Beta: {huber_beta} {param_unit} | LoRA r={args.lora_r}, α={args.lora_alpha} (Attn+MLP)")
    print("=" * 75 + "\n")

    # 1. Initialize LoRA Engine (Targets: seq_attn.query_proj, seq_attn.value_proj, ff0, ff1)
    lora_engine = TimesFMLoRAEngine(
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
    )
    lora_engine.print_trainable_parameters()

    # 2. Build Unified DataLoaders
    print(f"\nLoading unified training (14,000 seqs) and validation (2,000 seqs) for {args.target_col}...")
    train_loader = create_unified_pdw_dataloader(
        datasets_root=datasets_root,
        profile_mode=args.profile_mode,
        split="train",
        col_name=args.target_col,
        context_len=args.context_len,
        horizon_len=args.horizon,
        batch_size=args.batch_size,
        shuffle=True,
    )
    val_loader = create_unified_pdw_dataloader(
        datasets_root=datasets_root,
        profile_mode=args.profile_mode,
        split="val",
        col_name=args.target_col,
        context_len=args.context_len,
        horizon_len=args.horizon,
        batch_size=args.batch_size,
        shuffle=False,
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

    # 4. Training Loop with BF16 Mixed Precision
    best_val_loss = float("inf")
    checkpoint_subdir = args.save_dir / (param_slug if param_slug else "pri") / "best_model"
    checkpoint_subdir.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "-" * 75)
    print(f"Starting SFT Training (FP32 Precision)...")
    print("-" * 75)

    global_step = 0
    t_start = time.time()

    for epoch in range(1, args.epochs + 1):
        lora_engine.peft_model.train()
        train_loss = 0.0
        t_epoch = time.time()

        for step, (ctx_batch, tgt_batch) in enumerate(train_loader):
            optimizer.zero_grad()
            tgt_norm = (tgt_batch / scale).to(lora_engine.device)

            preds_norm = lora_engine.forward_train(ctx_batch, horizon=args.horizon, scale=scale)
            loss = F.smooth_l1_loss(preds_norm, tgt_norm, beta=huber_beta / scale)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(lora_engine.peft_model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()

            train_loss += float(loss.item()) * len(tgt_batch)
            global_step += 1

            if (step + 1) % 50 == 0 or (step + 1) == len(train_loader):
                cur_lr = scheduler.get_last_lr()[0]
                batch_mae = float(((preds_norm * scale) - tgt_batch.to(lora_engine.device)).abs().mean().item())
                print(f"Epoch [{epoch}/{args.epochs}] Batch [{step+1:3d}/{len(train_loader)}] Loss: {loss.item():.5f} | Batch MAE: {batch_mae:.2f} {param_unit} | LR: {cur_lr:.2e}")

        epoch_train_loss = train_loss / len(train_loader.dataset)
        val_loss, val_mae, val_hit = validate_epoch(
            lora_engine=lora_engine,
            val_loader=val_loader,
            horizon=args.horizon,
            beta=huber_beta,
            tolerance=tolerance,
            scale=scale,
        )

        epoch_time = time.time() - t_epoch
        print(
            f"--> Epoch {epoch} Complete ({epoch_time:.1f}s) | "
            f"Train Huber: {epoch_train_loss:.5f} | "
            f"Val Huber: {val_loss:.5f} | "
            f"Val MAE: {val_mae:.2f} {param_unit} | "
            f"Val Hit Rate (±{tolerance:g}{param_unit}): {val_hit:.1f}%"
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            lora_engine.save_lora_checkpoint(checkpoint_subdir)
            print(f"    * New best validation loss! Saved checkpoint to {checkpoint_subdir}")

    total_train_time = time.time() - t_start
    print("\n" + "=" * 75)
    print(f"Training Complete in {total_train_time:.1f}s ({total_train_time/60:.1f} min)")
    print("=" * 75)

    # 5. Automated Post-Training Evaluation on 4,000 Test Sequences
    print("\nLoading Best Fine-Tuned Model for Full Test Split Evaluation...")
    tfm_eval = TimesFMLoRAEngine.load_for_inference(weights_dir=checkpoint_subdir)

    base_results_dir = PROJECT_ROOT / "results" / "timesfm_3.0" / "lora_sft" / f"univariate_{args.profile_mode}"
    target_results_dir = base_results_dir / param_slug if param_slug else base_results_dir
    plots_dir = target_results_dir / "plots"

    radar_types = ["stable", "jitter", "stagger", "dwell_and_switch", "sliding"]
    error_levels = ["clean", "error_lv1", "error_lv2", "error_lv3"]

    test_results = []
    for rtype in radar_types:
        for elevel in error_levels:
            folder_name = f"1000x128_{elevel}"
            dataset_dir = datasets_root / rtype / folder_name
            dataset_display = f"{rtype}/{folder_name}"

            res = evaluate_single_dataset(
                tfm=tfm_eval,
                dataset_dir=dataset_dir,
                dataset_display=dataset_display,
                radar_type=rtype,
                error_level=elevel,
                context_len=args.context_len,
                horizon_len=args.horizon,
                max_test_seqs=200,
                tolerance=tolerance,
                target_col=args.target_col,
                unit=param_unit,
                param_display_name=param_name,
                plots_dir=plots_dir,
            )
            if res:
                test_results.append(res)

    if test_results:
        export_benchmark_results(
            test_results,
            target_results_dir,
            title=f"TimesFM 3.0 LoRA Fine-Tuned (SFT) Benchmark Report [{param_name} {args.profile_mode.capitalize()}]",
            unit=param_unit,
        )

        # 6. Generate Side-by-Side Comparison if Zero-Shot exists
        zero_shot_base = PROJECT_ROOT / "results" / "timesfm_3.0" / "zero_shot" / f"univariate_{args.profile_mode}"
        zero_shot_csv = (zero_shot_base / param_slug if param_slug else zero_shot_base) / "metrics.csv"
        lora_csv = target_results_dir / "metrics.csv"
        cmp_filename = f"comparison_zero_shot_vs_lora_{args.profile_mode}_{param_slug}.md" if param_slug else f"comparison_zero_shot_vs_lora_{args.profile_mode}.md"
        comparison_md = PROJECT_ROOT / "results" / "timesfm_3.0" / cmp_filename

        build_comparison_report(zero_shot_csv, lora_csv, comparison_md)

        build_comparison_report(zero_shot_csv, lora_csv, comparison_md)


if __name__ == "__main__":
    main()
