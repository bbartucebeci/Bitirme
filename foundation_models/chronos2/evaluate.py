"""Zero-shot and fine-tuned Chronos-2 evaluation on single-radar datasets."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from foundation_models.chronos2.adapter import MODEL_ID, load_pipeline, predict_median
from foundation_models.common.dataset import (
    CHANNELS,
    DATASETS_ROOT,
    ERROR_LEVELS,
    PROJECT_ROOT,
    RADAR_TYPES,
    TOLERANCES,
    UNITS,
    ForecastWindow,
    load_split,
)
from foundation_models.common.metrics import aggregate, score_single, score_window


RESULTS_ROOT = PROJECT_ROOT / "results" / "chronos2"


def audit_coverage(
    profile_mode: str,
    target_param: str,
    dataset_size: str,
    context_len: int,
    horizon_len: int,
    max_test_seqs: int | None = None,
    radar_type: str | None = None,
    error_level: str | None = None,
) -> pd.DataFrame:
    """Check every selected 96-to-32 test split before loading model weights."""
    rows = []
    for rtype in ((radar_type,) if radar_type else RADAR_TYPES):
        for level in ((error_level,) if error_level else ERROR_LEVELS):
            path = DATASETS_ROOT / profile_mode / rtype / f"{dataset_size}_{level}"
            loaded = load_split(path, "test", target_param, context_len, horizon_len, max_test_seqs)
            rows.append({
                "radar_type": rtype, "error_level": level,
                "sequence_files": loaded.total_sequences,
                "eligible_windows": len(loaded.windows),
                "skipped_short": loaded.skipped_short,
            })
    return pd.DataFrame(rows)


def _save_plot(
    plot_path: Path,
    window: ForecastWindow,
    prediction: np.ndarray,
    target_param: str,
) -> None:
    names = CHANNELS if target_param == "multivariate" else (target_param,)
    fig, axes = plt.subplots(len(names), 1, figsize=(11, 2.6 * len(names)), squeeze=False)
    for idx, name in enumerate(names):
        axis = axes[idx, 0]
        x_context = np.arange(window.context.shape[1])
        x_future = np.arange(window.context.shape[1], window.context.shape[1] + window.target.shape[1])
        axis.plot(x_context, window.context[idx], label="observed context")
        axis.plot(x_future, window.target[idx], label="target")
        axis.plot(x_future, prediction[idx], label="Chronos-2 median")
        axis.set_ylabel(f"{name} ({UNITS[name]})")
        axis.grid(alpha=0.25)
        axis.legend(loc="best")
    axes[-1, 0].set_xlabel("Pulse position within sequence")
    fig.suptitle(f"{target_param}: {window.sequence_id}")
    fig.tight_layout()
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(plot_path, dpi=140)
    plt.close(fig)


def evaluate_condition(
    pipeline,
    dataset_dir: Path,
    target_param: str,
    context_len: int,
    horizon_len: int,
    batch_size: int,
    max_test_seqs: int | None,
    plot_path: Path | None,
    clean_context: bool = False,
) -> dict[str, float]:
    loaded = load_split(
        dataset_dir,
        "test",
        target_param=target_param,
        context_len=context_len,
        horizon_len=horizon_len,
        limit=max_test_seqs,
    )
    windows = loaded.windows
    if not windows:
        raise ValueError(f"{dataset_dir}: no sequences have {context_len + horizon_len} usable pulses")
    scores = []
    for start in range(0, len(windows), batch_size):
        batch = windows[start : start + batch_size]
        batch_contexts = []
        for window in batch:
            ctx = window.context
            if clean_context and target_param in ("PRI", "multivariate"):
                from foundation_models.common.dataset import clean_pri_context
                cleaned_pri = clean_pri_context(ctx[0], target_len=context_len)
                ctx = ctx.copy()
                ctx[0] = cleaned_pri
            batch_contexts.append(ctx)
        predictions = predict_median(pipeline, batch_contexts, horizon_len, batch_size)
        for window, prediction in zip(batch, predictions, strict=True):
            if target_param == "multivariate":
                score = score_window(prediction, window.target, window.emitter_mask)
            else:
                score = score_single(prediction[0], window.target[0], window.emitter_mask, target_param)
            if score is not None:
                scores.append(score)
        if start == 0 and plot_path is not None:
            _save_plot(plot_path, batch[0], predictions[0], target_param)
    return {
        "num_sequences": len(scores),
        "skipped_short": loaded.skipped_short,
        "skipped_no_emitter": len(windows) - len(scores),
        **aggregate(scores),
    }


def run_evaluation(
    pipeline,
    profile_mode: str,
    target_param: str,
    dataset_size: str = "1000x128",
    context_len: int = 96,
    horizon_len: int = 32,
    batch_size: int = 64,
    max_test_seqs: int | None = None,
    output_dir: Path | None = None,
    radar_type: str | None = None,
    error_level: str | None = None,
    plots: bool = True,
    clean_context: bool = False,
) -> pd.DataFrame:
    if target_param not in (*CHANNELS, "multivariate"):
        raise ValueError(f"Unknown target parameter: {target_param}")
    if profile_mode not in ("fixed", "varying"):
        raise ValueError(f"Unknown profile mode: {profile_mode}")
    if radar_type is not None and radar_type not in RADAR_TYPES:
        raise ValueError(f"Unknown radar type: {radar_type}")
    if error_level is not None and error_level not in ERROR_LEVELS:
        raise ValueError(f"Unknown error level: {error_level}")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    radar_types = (radar_type,) if radar_type else RADAR_TYPES
    error_levels = (error_level,) if error_level else ERROR_LEVELS
    selected = [
        (rtype, level, DATASETS_ROOT / profile_mode / rtype / f"{dataset_size}_{level}")
        for rtype in radar_types
        for level in error_levels
    ]
    missing = [str(path) for _, _, path in selected if not (path / "metadata.yaml").is_file()]
    if missing:
        raise FileNotFoundError("Missing benchmark datasets:\n" + "\n".join(missing))

    rows = []
    for rtype, level, dataset_dir in selected:
        plot_path = output_dir / "plots" / f"{rtype}_{level}.png" if output_dir and plots else None
        metrics = evaluate_condition(
            pipeline, dataset_dir, target_param, context_len, horizon_len,
            batch_size, max_test_seqs, plot_path, clean_context=clean_context,
        )
        row = {"radar_type": rtype, "error_level": level, **metrics}
        rows.append(row)
        label = f"PRI MAE: {row['mae_pri']:.2f} us" if target_param == "multivariate" else f"MAE: {row['mae']:.2f} {UNITS[target_param]}"
        print(f"[EVAL] {profile_mode}/{rtype}/{level}: {row['num_sequences']} sequences | {label}")

    results = pd.DataFrame(rows)
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        results.to_csv(output_dir / "metrics.csv", index=False)
        lines = [
            f"# Chronos-2 {target_param} benchmark ({profile_mode})",
            "",
            f"Dataset size: `{dataset_size}`. Context: {context_len}. Horizon: {horizon_len}.",
            "Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.",
            "The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.",
            "Sequences with no emitter pulses in the target window are excluded and counted.",
            "",
            results.to_markdown(index=False),
            "",
        ]
        (output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"[SAVED] {output_dir / 'metrics.csv'}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Chronos-2 on single-radar PDW forecasts")
    parser.add_argument("--profile-mode", choices=("fixed", "varying"), default="fixed")
    parser.add_argument("--target-param", choices=(*CHANNELS, "multivariate", "all"), default="PRI")
    parser.add_argument("--dataset-size", default="1000x128")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--max-test-seqs", type=int)
    parser.add_argument("--radar-type", choices=RADAR_TYPES)
    parser.add_argument("--error-level", choices=ERROR_LEVELS)
    parser.add_argument("--model-id", default=MODEL_ID)
    parser.add_argument("--weights-dir", type=Path)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--clean-context", action="store_true", help="Apply classical clean_pri_context filter to input context before inference")
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--coverage-only", action="store_true", help="Inspect selected CSVs without loading Chronos-2")
    args = parser.parse_args()
    if args.target_param == "all" and args.weights_dir is not None:
        parser.error("--target-param all requires zero-shot mode; fine-tuned checkpoints are task-specific")

    tasks = (*CHANNELS, "multivariate") if args.target_param == "all" else (args.target_param,)
    coverage = audit_coverage(
        args.profile_mode, tasks[0], args.dataset_size, args.context_len,
        args.horizon, args.max_test_seqs, args.radar_type, args.error_level,
    )
    print(coverage.to_string(index=False))
    if args.coverage_only:
        return
    if (coverage.eligible_windows == 0).any():
        parser.error("At least one selected dataset has no complete forecast window; see coverage above")

    pipeline = load_pipeline(str(args.weights_dir) if args.weights_dir else args.model_id, args.device)
    regime = "lora_sft" if args.weights_dir else "zero_shot"
    for task in tasks:
        mode = f"multivariate_{args.profile_mode}" if task == "multivariate" else f"univariate_{args.profile_mode}/{task.lower()}"
        run_evaluation(
            pipeline, args.profile_mode, task, args.dataset_size,
            args.context_len, args.horizon, args.batch_size, args.max_test_seqs,
            RESULTS_ROOT / regime / mode, args.radar_type, args.error_level,
            not args.no_plots, clean_context=args.clean_context,
        )


if __name__ == "__main__":
    main()
