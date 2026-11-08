"""Chronos-2 LoRA fine-tuning with the same PDW forecast windows as evaluation."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np

from foundation_models.chronos2.adapter import MODEL_ID, load_pipeline
from foundation_models.common.dataset import (
    CHANNELS,
    DATASETS_ROOT,
    ERROR_LEVELS,
    PROJECT_ROOT,
    RADAR_TYPES,
    load_split,
    training_series,
)
from foundation_models.chronos2.evaluate import RESULTS_ROOT, run_evaluation


def _load_training_split(
    profile_mode: str,
    dataset_size: str,
    split: str,
    target_param: str,
    context_len: int,
    horizon_len: int,
    limit: int | None,
    radar_types: tuple[str, ...],
    error_levels: tuple[str, ...],
) -> list[np.ndarray]:
    all_series = []
    for radar_type in radar_types:
        for error_level in error_levels:
            dataset_dir = DATASETS_ROOT / profile_mode / radar_type / f"{dataset_size}_{error_level}"
            loaded = load_split(dataset_dir, split, target_param, context_len, horizon_len, limit)
            print(f"[DATA] {split} {profile_mode}/{radar_type}/{error_level}: "
                  f"{len(loaded.windows)} usable, {loaded.skipped_short} short")
            if not loaded.windows:
                raise ValueError(f"{dataset_dir}: no {split} sequences meet the {context_len}+{horizon_len} window")
            all_series.extend(training_series(loaded.windows))
    if not all_series:
        raise ValueError(f"No usable {split} sequences")
    return all_series


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Chronos-2 on the single-radar benchmark")
    parser.add_argument("--profile-mode", choices=("fixed", "varying"), default="fixed")
    parser.add_argument("--target-param", choices=(*CHANNELS, "multivariate"), default="PRI")
    parser.add_argument("--dataset-size", default="1000x128")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=3, help="Sets the default step budget")
    parser.add_argument("--steps", type=int, help="Override the default 3-epoch-equivalent step budget")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--seed", type=int, default=20261020)
    parser.add_argument("--max-train-seqs-per-dataset", type=int)
    parser.add_argument("--max-val-seqs-per-dataset", type=int)
    parser.add_argument("--max-test-seqs", type=int)
    parser.add_argument("--radar-type", choices=RADAR_TYPES)
    parser.add_argument("--error-level", choices=ERROR_LEVELS)
    parser.add_argument("--model-id", default=MODEL_ID)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--skip-eval", action="store_true")
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    if min(args.epochs, args.batch_size, args.context_len, args.horizon, args.lora_r, args.lora_alpha) <= 0:
        parser.error("Epochs, batch size, window lengths, and LoRA settings must be positive")
    if args.steps is not None and args.steps <= 0:
        parser.error("--steps must be positive")
    if args.lr <= 0:
        parser.error("--lr must be positive")

    import torch

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    radar_types = (args.radar_type,) if args.radar_type else RADAR_TYPES
    error_levels = (args.error_level,) if args.error_level else ERROR_LEVELS
    train_series = _load_training_split(
        args.profile_mode, args.dataset_size, "train", args.target_param,
        args.context_len, args.horizon, args.max_train_seqs_per_dataset,
        radar_types, error_levels,
    )
    val_series = _load_training_split(
        args.profile_mode, args.dataset_size, "val", args.target_param,
        args.context_len, args.horizon, args.max_val_seqs_per_dataset,
        radar_types, error_levels,
    )
    steps = args.steps or args.epochs * math.ceil(len(train_series) / args.batch_size)
    print(f"[DATA] {len(train_series)} train, {len(val_series)} validation sequences; {steps} steps")

    output_dir = PROJECT_ROOT / "models" / "lora_sft" / "chronos2" / args.profile_mode / args.target_param.lower()
    pipeline = load_pipeline(args.model_id, args.device)
    finetuned = pipeline.fit(
        inputs=train_series,
        validation_inputs=val_series,
        prediction_length=args.horizon,
        context_length=args.context_len,
        min_past=args.context_len,
        finetune_mode="lora",
        lora_config={
            "r": args.lora_r,
            "lora_alpha": args.lora_alpha,
            "target_modules": [
                "self_attention.q", "self_attention.v", "self_attention.k",
                "self_attention.o", "output_patch_embedding.output_layer",
            ],
        },
        learning_rate=args.lr,
        num_steps=steps,
        batch_size=args.batch_size,
        output_dir=output_dir,
        finetuned_ckpt_name="best_model",
    )
    print(f"[CHECKPOINT] {output_dir / 'best_model'}")

    if not args.skip_eval:
        mode = f"multivariate_{args.profile_mode}" if args.target_param == "multivariate" else f"univariate_{args.profile_mode}/{args.target_param.lower()}"
        run_evaluation(
            finetuned, args.profile_mode, args.target_param, args.dataset_size,
            args.context_len, args.horizon, args.batch_size, args.max_test_seqs,
            RESULTS_ROOT / "lora_sft" / mode, args.radar_type, args.error_level,
            not args.no_plots,
        )


if __name__ == "__main__":
    main()
