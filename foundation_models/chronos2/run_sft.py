"""LoRA SFT matrix for new_complex_pri; one adapter per profile/task/context."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gc
import hashlib
import importlib.metadata
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from dataset_generator.catalog import NEW_COMPLEX_PRI, NEW_COMPLEX_DATASETS_ROOT, PROJECT_ROOT, RADAR_TYPES, ERROR_LEVELS
from dataset_generator.sequence_io import SCHEMA_V2, boundary_start
from foundation_models.chronos2.adapter import MODEL_ID, load_pipeline
from foundation_models.chronos2.run_zero_shot import (
    CONTEXT_LENS, TASKS, code_fingerprint, evaluate_one, export_reports, prepare_inputs, write_json,
)
from foundation_models.common.dataset import load_split, training_series
from foundation_models.common.windowing import file_sha256, WINDOW_SEED


def sft_fingerprint() -> str:
    digest = hashlib.sha256(code_fingerprint().encode())
    digest.update(Path(__file__).read_bytes())
    return digest.hexdigest()


def step_budget(count: int, task: str, batch_size: int, epochs: int, steps: int | None) -> tuple[int, int]:
    """Chronos fills a batch in whole tasks until its variate budget is reached.

    Sampling is with replacement: epochs here describe expected exposure, not
    guaranteed exhaustive passes. Every multivariate task has five targets.
    """
    channels = 5 if task == "multivariate" else 1
    if min(count, batch_size, epochs) <= 0 or (steps is not None and steps <= 0):
        raise ValueError("Training budgets must be positive")
    sequences_per_batch = math.ceil(batch_size / channels)
    return (steps or epochs * math.ceil(count / sequences_per_batch)), sequences_per_batch


def audit_inputs(root: Path, size: str, profile: str, radars, levels, limits: dict) -> dict:
    """Fingerprint selected train/val CSVs; check split membership without test reads."""
    audit = {"sequence_sha256": {}, "metadata_sha256": {}, "counts": {"train": 0, "val": 0}}
    for radar, level in itertools.product(radars, levels):
        condition = f"{profile}/{radar}/{level}"
        folder = root / profile / radar / f"{size}_{level}"
        metadata = yaml.safe_load((folder / "metadata.yaml").read_text(encoding="utf-8"))
        boundary_start(metadata, 1, 1, "boundary")
        if (metadata["profile_mode"], metadata["radar_type"], metadata["error_level"]) != (profile, radar, level):
            raise ValueError(f"Condition metadata mismatch: {folder}")
        if metadata["expected_pulses_per_sequence"] != int(size.split("x")[1]):
            raise ValueError(f"Dataset size mismatch: {folder}")
        audit["metadata_sha256"][condition] = file_sha256(folder / "metadata.yaml")
        memberships = {}
        for split in ("train", "val", "test"):
            files = sorted((folder / split).glob("seq_*.csv"))
            if len(files) != metadata["split"][split]["sequence_count"]:
                raise ValueError(f"Incomplete {split} split: {folder}")
            memberships[split] = {p.stem for p in files}
            if split != "test":
                selected = files[:limits[split]] if limits[split] is not None else files
                if not selected:
                    raise ValueError(f"Empty {split}: {folder}")
                audit["counts"][split] += len(selected)
                for path in selected:
                    audit["sequence_sha256"][f"{condition}/{split}/{path.stem}"] = file_sha256(path)
        if any(memberships[a] & memberships[b] for a, b in itertools.combinations(memberships, 2)):
            raise ValueError(f"Train/val/test sequence IDs overlap: {folder}")
        if sum(map(len, memberships.values())) != metadata["sequence_count"]:
            raise ValueError(f"Split totals differ from sequence count: {folder}")
    return audit


def load_pool(root: Path, size: str, profile: str, task: str, length: int, horizon: int,
              radars, levels, split: str, limit: int | None) -> list[np.ndarray]:
    if split not in ("train", "val"):
        raise ValueError("SFT fitting may only read train or val")
    pool = []
    for radar, level in itertools.product(radars, levels):
        loaded = load_split(root/profile/radar/f"{size}_{level}", split, task, length, horizon,
                            limit, window_mode="boundary")
        if loaded.skipped_short or not loaded.windows:
            raise ValueError(f"Incomplete {split} windows: {profile}/{radar}/{level}")
        arrays = training_series(loaded.windows)
        channels = 5 if task == "multivariate" else 1
        if len(arrays) != len(loaded.windows) or any(a.shape != (channels, length+horizon) or
                                                   not np.isfinite(a).all() for a in arrays):
            raise ValueError("SFT requires complete finite L+H boundary windows")
        pool.extend(arrays)
        print(f"[DATA] {split}/{profile}/{radar}/{level}: {len(arrays)}", flush=True)
    return pool


def verify_reference(manifest: dict, reference: Path, model_id: str) -> dict:
    """Compare every selected input/window with the completed zero-shot baseline."""
    config = json.loads((reference/"run_config.json").read_text(encoding="utf-8"))
    other = json.loads((reference/"test_windows.json").read_text(encoding="utf-8"))
    if (config["regime"] != "zero_shot" or config["window_mode"] != "boundary"
            or config["model_id"] != model_id):
        raise ValueError("Reference must be boundary zero-shot with the same base model")
    for field in ("schema_version", "dataset_size", "horizon_len", "window_mode"):
        if manifest["meta"][field] != other["meta"][field]:
            raise ValueError(f"Reference protocol mismatch: {field}")
    for group in ("windows", "sequence_sha256", "metadata_sha256", "sequence_lengths", "plot_sequences"):
        if any(other[group].get(k) != v for k, v in manifest[group].items()):
            raise ValueError(f"Reference differs in {group}")
    if not (reference/"metrics.csv").is_file():
        raise ValueError("Reference metrics missing")
    rows = pd.read_csv(reference/"metrics.csv")
    expected = set(itertools.product(manifest["meta"]["context_lens"], manifest["plot_sequences"]))
    for length, condition in expected:
        profile, radar, level = condition.split("/")
        for task in ("PRI", "Frequency", "multivariate"):
            match = rows[(rows.task == task) & (rows.context_len == length) & (rows.profile == profile)
                         & (rows.radar_type == radar) & (rows.error_level == level)]
            selected_count = sum(k.startswith(condition+"/") for k in manifest["sequence_sha256"])
            if len(match) != 1 or int(match.iloc[0].num_sequences) < selected_count:
                raise ValueError(f"Reference condition incomplete: {task}/{length}/{condition}")
    return {name: file_sha256(reference/name) for name in ("run_config.json", "test_windows.json", "metrics.csv")}


def checkpoint_hashes(path: Path) -> dict:
    files = [p for p in path.rglob("*") if p.is_file()]
    if not (path/"adapter_config.json").is_file() or not (path/"adapter_model.safetensors").is_file():
        raise ValueError(f"LoRA checkpoint incomplete: {path}")
    return {p.relative_to(path).as_posix(): file_sha256(p) for p in files}


def release_gpu():
    import torch
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def fit_adapter(args, task, length, profile, job: Path, inputs: dict) -> Path:
    import torch
    import peft  # Fail explicitly; Chronos otherwise may fall back to full fine-tuning.
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
        torch.cuda.reset_peak_memory_stats()
    root = args.datasets_root.resolve()
    train = load_pool(root, args.dataset_size, profile, task, length, args.horizon,
                      args.radar_types, args.error_levels, "train", args.max_train_seqs_per_dataset)
    val = load_pool(root, args.dataset_size, profile, task, length, args.horizon,
                    args.radar_types, args.error_levels, "val", args.max_val_seqs_per_dataset)
    actual = audit_inputs(root, args.dataset_size, profile, args.radar_types, args.error_levels,
                          {"train": args.max_train_seqs_per_dataset, "val": args.max_val_seqs_per_dataset})
    if actual != inputs:
        raise ValueError("Training CSVs changed while loading")
    steps, batch_sequences = step_budget(len(train), task, args.train_batch_size, args.epochs, args.steps)
    attempt = args.model_output_dir/task/f"L{length}"/profile/datetime.now(timezone.utc).strftime("attempt_%Y%m%d_%H%M%S_%f_UTC")
    attempt.mkdir(parents=True, exist_ok=False)
    pipeline = load_pipeline(args.model_id, args.device)
    runtime = {"torch": torch.__version__, "chronos_forecasting": importlib.metadata.version("chronos-forecasting"),
               "peft": peft.__version__, "device": str(pipeline.model.device),
               "gpu_name": torch.cuda.get_device_name() if pipeline.model.device.type == "cuda" else None,
               "base_model_commit": getattr(pipeline.model.config, "_commit_hash", None),
               "train_windows": len(train), "val_windows": len(val), "steps": steps,
               "sequences_per_batch": batch_sequences, "train_batch_variates": args.train_batch_size,
               "expected_exposures_per_sequence": steps*batch_sequences/len(train),
               "checkpoint_selection": "minimum validation eval_loss (Chronos quantile loss)"}
    write_json(job/"training_runtime.json", runtime)
    print(f"[TRAIN] {profile}/{task}/L{length}: {steps} steps, {len(train)} train, {len(val)} val", flush=True)
    fitted = pipeline.fit(
        inputs=train, validation_inputs=val, prediction_length=args.horizon,
        context_length=length, min_past=length, finetune_mode="lora",
        lora_config={"r": args.lora_r, "lora_alpha": args.lora_alpha,
                     "target_modules": ["self_attention.q", "self_attention.v", "self_attention.k",
                                        "self_attention.o", "output_patch_embedding.output_layer"]},
        learning_rate=args.lr, num_steps=steps, batch_size=args.train_batch_size,
        output_dir=attempt, finetuned_ckpt_name="best_model", seed=args.seed, data_seed=args.seed,
        eval_steps=min(args.eval_steps, steps), save_steps=min(args.eval_steps, steps),
        logging_steps=min(10, steps), report_to="none",
    )
    checkpoint = attempt/"best_model"
    hashes = checkpoint_hashes(checkpoint)
    states = [json.loads(path.read_text()) for path in attempt.glob("checkpoint-*/trainer_state.json")]
    if not states:
        raise ValueError("Training produced no validation/checkpoint selection record")
    state = max(states, key=lambda value: value["global_step"])
    if state.get("best_metric") is None or not math.isfinite(float(state["best_metric"])):
        raise ValueError("Training produced no finite best validation loss")
    runtime.update(best_validation_loss=state["best_metric"],
                   selected_checkpoint=state.get("best_model_checkpoint"),
                   optimization_steps=state["global_step"])
    if not hasattr(fitted.model, "get_nb_trainable_parameters"):
        raise ValueError("Expected a LoRA model, refusing to accept a full fine-tune")
    trainable, total = fitted.model.get_nb_trainable_parameters()
    runtime.update(trainable_parameters=trainable, total_parameters=total)
    if audit_inputs(root, args.dataset_size, profile, args.radar_types, args.error_levels,
                    {"train": args.max_train_seqs_per_dataset, "val": args.max_val_seqs_per_dataset}) != inputs:
        raise ValueError("Training inputs changed during fit; checkpoint cannot be marked complete")
    if torch.cuda.is_available():
        runtime["peak_cuda_allocated_bytes"] = torch.cuda.max_memory_allocated()
    write_json(job/"training_runtime.json", runtime)
    # Fit copies the base model. Free both before loading the saved adapter.
    del fitted, pipeline, train, val
    release_gpu()
    write_json(job/"training_complete.json", {"checkpoint": str(checkpoint), "sha256": hashes})
    return checkpoint


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--datasets-root", type=Path, default=NEW_COMPLEX_DATASETS_ROOT/"production/C1024_H32/single_radar")
    p.add_argument("--dataset-size", default="1000x1056")
    p.add_argument("--profiles", nargs="+", choices=("fixed", "varying"), default=("fixed", "varying"))
    p.add_argument("--tasks", nargs="+", choices=TASKS, default=TASKS)
    p.add_argument("--context-lens", nargs="+", type=int, default=CONTEXT_LENS)
    p.add_argument("--radar-types", nargs="+", choices=RADAR_TYPES, default=RADAR_TYPES)
    p.add_argument("--error-levels", nargs="+", choices=ERROR_LEVELS, default=ERROR_LEVELS)
    p.add_argument("--horizon", type=int, default=32)
    p.add_argument("--epochs", type=int, default=3, help="Expected exposure budget; Chronos samples with replacement")
    p.add_argument("--steps", type=int, help="Explicit optimization steps per adapter")
    p.add_argument("--train-batch-size", type=int, default=20, help="Chronos variate budget: 20 univariate or 4 five-channel sequences")
    p.add_argument("--batch-size", type=int, default=16, help="Evaluation variate budget")
    p.add_argument("--eval-steps", type=int, default=500)
    p.add_argument("--lr", type=float, default=1e-5)
    p.add_argument("--lora-r", type=int, default=16)
    p.add_argument("--lora-alpha", type=int, default=32)
    p.add_argument("--seed", type=int, default=20261020)
    p.add_argument("--window-seed", type=int, default=WINDOW_SEED)
    p.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    p.add_argument("--model-id", default=MODEL_ID)
    p.add_argument("--zero-shot-run", type=Path, required=True, help="Completed reference run; exact test inputs/windows must match")
    p.add_argument("--output-dir", type=Path)
    p.add_argument("--model-output-dir", type=Path)
    p.add_argument("--plot-sequence-id", default="seq_0800")
    p.add_argument("--max-train-seqs-per-dataset", type=int)
    p.add_argument("--max-val-seqs-per-dataset", type=int)
    p.add_argument("--max-test-seqs", type=int)
    p.add_argument("--smoke-test", action="store_true", help="Cap each condition to 2/1/2 train/val/test sequences and each adapter to 2 steps")
    p.add_argument("--dry-run", action="store_true", help="Print jobs without reading data, loading weights, or creating outputs")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--no-plots", action="store_true")
    return p


def main():
    p = parser()
    args = p.parse_args()
    if min(args.horizon, args.epochs, args.train_batch_size, args.batch_size, args.eval_steps,
           args.lora_r, args.lora_alpha, *args.context_lens) <= 0 or args.lr <= 0:
        p.error("Lengths, budgets and learning rate must be positive")
    for name in ("steps", "max_train_seqs_per_dataset", "max_val_seqs_per_dataset", "max_test_seqs"):
        if getattr(args, name) is not None and getattr(args, name) <= 0:
            p.error(f"{name} must be positive")
    for name in ("profiles", "tasks", "context_lens", "radar_types", "error_levels"):
        if len(set(getattr(args, name))) != len(getattr(args, name)):
            p.error(f"Duplicate {name}")
    if args.smoke_test:
        for name, cap in (("steps", 2), ("max_train_seqs_per_dataset", 2),
                          ("max_val_seqs_per_dataset", 1), ("max_test_seqs", 2)):
            setattr(args, name, min(getattr(args, name) or cap, cap))
    jobs = list(itertools.product(args.tasks, args.context_lens, args.profiles))
    if args.dry_run:
        for task, length, profile in jobs:
            print(f"[PLAN] {profile}/{task}/L{length}, H={args.horizon}; pool {len(args.radar_types)} radars x {len(args.error_levels)} error levels")
        print(f"[PLAN] {len(jobs)} adapters; {len(jobs)*len(args.radar_types)*len(args.error_levels)} evaluation conditions; no training started")
        return
    stamp = datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S_UTC")
    output = (args.output_dir or PROJECT_ROOT/"results/chronos2/lora_sft"/NEW_COMPLEX_PRI/stamp).resolve()
    if args.smoke_test and args.output_dir is None:
        output = PROJECT_ROOT/"outputs"/"chronos2_sft_smoke"/stamp
    args.model_output_dir = (args.model_output_dir or PROJECT_ROOT/"models/lora_sft/chronos2"/NEW_COMPLEX_PRI/output.name).resolve()
    root = args.datasets_root.resolve()
    # Outputs must never be inside input data or reference results, or overwrite ancestors.
    protected = (root, args.zero_shot_run.resolve())
    for destination in (output, args.model_output_dir):
        if any(destination == source or source in destination.parents or destination in source.parents for source in protected):
            p.error("Output/checkpoint directories must be separate from datasets and zero-shot reference")
    if output == args.model_output_dir or output in args.model_output_dir.parents or args.model_output_dir in output.parents:
        p.error("Result and checkpoint directories must be separate")
    if output.exists() and any(output.iterdir()) and not args.resume:
        p.error(f"Output already contains files: {output}; use a fresh run or --resume")
    if args.model_output_dir.exists() and any(args.model_output_dir.iterdir()) and not args.resume:
        p.error("Checkpoint root is not empty; use a fresh run or --resume")
    config = {name: getattr(args, name) for name in (
        "dataset_size", "profiles", "tasks", "context_lens", "radar_types", "error_levels", "horizon",
        "epochs", "steps", "train_batch_size", "eval_steps", "lr", "lora_r", "lora_alpha", "seed",
        "window_seed", "model_id", "plot_sequence_id", "max_train_seqs_per_dataset",
        "max_val_seqs_per_dataset", "max_test_seqs", "smoke_test")}
    config.update(regime="lora_sft", dataset_family=NEW_COMPLEX_PRI, window_mode="boundary",
                  datasets_root=str(root), checkpoint_root=str(args.model_output_dir),
                  zero_shot_run=str(args.zero_shot_run.resolve()), code_sha256=sft_fingerprint(), plots=not args.no_plots)
    config = json.loads(json.dumps(config))
    if args.resume and output.exists() and (output/"run_config.json").is_file():
        if json.loads((output/"run_config.json").read_text()) != config:
            p.error("SFT configuration/code changed; resume rejected")
    elif args.resume and output.exists() and any(output.iterdir()):
        p.error("Cannot resume without run_config.json")
    coverage, manifest = prepare_inputs(root, args.dataset_size, args.profiles, args.radar_types,
                                       args.error_levels, args.context_lens, args.horizon, "boundary",
                                       args.window_seed, args.max_test_seqs, args.plot_sequence_id)
    if manifest["meta"]["schema_version"] != SCHEMA_V2:
        p.error("SFT matrix requires new_complex_pri boundary data")
    reference = verify_reference(manifest, args.zero_shot_run, args.model_id)
    for name, value in (("test_windows.json", manifest), ("zero_shot_reference.json", reference)):
        path = output/name
        if args.resume and path.is_file() and json.loads(path.read_text()) != value:
            p.error(f"Inputs/reference changed; resume rejected: {name}")
    output.mkdir(parents=True, exist_ok=True)
    write_json(output/"run_config.json", config)
    write_json(output/"test_windows.json", manifest)
    write_json(output/"zero_shot_reference.json", reference)
    coverage.to_csv(output/"coverage.csv", index=False)
    rows = []
    for index, (task, length, profile) in enumerate(jobs, 1):
        job = output/"training"/task/f"L{length}"/profile
        limits = {"train": args.max_train_seqs_per_dataset, "val": args.max_val_seqs_per_dataset}
        inputs = audit_inputs(root, args.dataset_size, profile, args.radar_types, args.error_levels, limits)
        audit = job/"inputs.json"
        if args.resume and audit.is_file() and json.loads(audit.read_text()) != inputs:
            raise ValueError(f"Training inputs changed; resume rejected: {job}")
        write_json(audit, inputs)
        complete = job/"training_complete.json"
        reused_adapter = args.resume and complete.is_file()
        if reused_adapter:
            saved = json.loads(complete.read_text())
            checkpoint = Path(saved["checkpoint"])
            if checkpoint_hashes(checkpoint) != saved["sha256"]:
                raise ValueError(f"Saved adapter changed: {checkpoint}")
            print(f"[RESUME] adapter {profile}/{task}/L{length}", flush=True)
        else:
            checkpoint = fit_adapter(args, task, length, profile, job, inputs)
        # Always reload the saved adapter, including on its first evaluation.
        pipeline = load_pipeline(str(checkpoint), args.device)
        scope = output/task/f"L{length}"/profile
        for radar, level in itertools.product(args.radar_types, args.error_levels):
            marker = scope/"completed"/f"{radar}_{level}.json"
            if reused_adapter and marker.is_file():
                row = json.loads(marker.read_text())
                required = [scope/"per_sequence"/f"{radar}_{level}.csv", scope/"examples"/f"{radar}_{level}.json"]
                if not args.no_plots:
                    required.append(scope/"plots"/f"{NEW_COMPLEX_PRI}_{radar}_{level}.png")
                if not all(path.is_file() for path in required):
                    raise ValueError(f"Incomplete saved evaluation: {marker}")
            else:
                row = evaluate_one(pipeline, root/profile/radar/f"{args.dataset_size}_{level}",
                                   profile, radar, level, task, length, args.horizon, args.batch_size,
                                   args.max_test_seqs, "boundary", args.window_seed, manifest, scope,
                                   not args.no_plots, regime="lora_sft")
            rows.append(row)
            pd.DataFrame(rows).to_csv(output/"metrics.csv", index=False)
        export_reports(rows, output, config)
        del pipeline
        release_gpu()
        print(f"[PROGRESS] {index}/{len(jobs)} adapters evaluated; {len(rows)} conditions", flush=True)
    write_json(output/"completed.json", {"adapters": len(jobs), "conditions": len(rows), "regime": "lora_sft"})
    print(f"[DONE] {output/'report.md'}", flush=True)


if __name__ == "__main__":
    main()
