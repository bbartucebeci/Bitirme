"""Zero-shot TiRex-2 evaluation on the single-radar PDW datasets."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from foundation_models.common.dataset import (
    CHANNELS,
    DATASETS_ROOT,
    ERROR_LEVELS,
    PROJECT_ROOT,
    RADAR_TYPES,
    UNITS,
    ForecastWindow,
    load_split,
)
from foundation_models.common.metrics import aggregate, score_single, score_window
from foundation_models.common.plotting import save_forecast_plot, save_multivariate_forecast_plot
from foundation_models.tirex2.adapter import MODEL_ID, load_pipeline, predict_median


RESULTS_ROOT = PROJECT_ROOT / "results" / "tirex2" / "zero_shot"


def audit_coverage(
    profile_mode: str,
    target_param: str,
    dataset_size: str,
    context_len: int,
    horizon_len: int,
    max_test_seqs: int | None,
    radar_type: str | None,
    error_level: str | None,
) -> pd.DataFrame:
    """Check selected test CSVs before downloading or loading TiRex-2."""
    rows = []
    for rtype in ((radar_type,) if radar_type else RADAR_TYPES):
        for level in ((error_level,) if error_level else ERROR_LEVELS):
            dataset_dir = DATASETS_ROOT / profile_mode / rtype / f"{dataset_size}_{level}"
            loaded = load_split(dataset_dir, "test", target_param, context_len, horizon_len, max_test_seqs)
            rows.append({
                "radar_type": rtype,
                "error_level": level,
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
    if target_param == "multivariate":
        save_multivariate_forecast_plot(
            plot_path=plot_path,
            title=f"TiRex-2 Joint 5-Channel Forecast | ({window.sequence_id})",
            context_5xN=window.context,
            ground_truth_5xN=window.target,
            predictions_5xN=prediction,
            tolerances=[TOLERANCES[ch] for ch in CHANNELS],
            param_names=list(CHANNELS),
            units=[UNITS[ch] for ch in CHANNELS],
        )
    else:
        tol = TOLERANCES.get(target_param, 10.0 if target_param == "PRI" else 1.0)
        unit = UNITS.get(target_param, "μs" if target_param == "PRI" else "units")
        save_forecast_plot(
            plot_path=plot_path,
            title=f"TiRex-2 {target_param} Forecast | ({window.sequence_id})",
            context=window.context[0],
            ground_truth=window.target[0],
            predictions=prediction[0],
            tolerance=tol,
            param_label=target_param,
            unit=unit,
        )


def evaluate_condition(
    model,
    dataset_dir: Path,
    target_param: str,
    context_len: int,
    horizon_len: int,
    batch_size: int,
    max_test_seqs: int | None,
    plot_path: Path | None,
) -> dict[str, float]:
    loaded = load_split(dataset_dir, "test", target_param, context_len, horizon_len, max_test_seqs)
    if not loaded.windows:
        raise ValueError(f"{dataset_dir}: no sequences have {context_len + horizon_len} usable pulses")

    scores = []
    for start in range(0, len(loaded.windows), batch_size):
        batch = loaded.windows[start : start + batch_size]
        predictions = predict_median(model, [window.context for window in batch], horizon_len, batch_size)
        for window, prediction in zip(batch, predictions, strict=True):
            score = (
                score_window(prediction, window.target, window.emitter_mask)
                if target_param == "multivariate"
                else score_single(prediction[0], window.target[0], window.emitter_mask, target_param)
            )
            if score is not None:
                scores.append(score)
        if start == 0 and plot_path is not None:
            _save_plot(plot_path, batch[0], predictions[0], target_param)

    return {
        "num_sequences": len(scores),
        "skipped_short": loaded.skipped_short,
        "skipped_no_emitter": len(loaded.windows) - len(scores),
        **aggregate(scores),
    }


def run_evaluation(
    model,
    profile_mode: str,
    target_param: str,
    dataset_size: str,
    context_len: int,
    horizon_len: int,
    batch_size: int,
    max_test_seqs: int | None,
    radar_type: str | None,
    error_level: str | None,
    plots: bool,
) -> pd.DataFrame:
    selected = [
        (rtype, level, DATASETS_ROOT / profile_mode / rtype / f"{dataset_size}_{level}")
        for rtype in ((radar_type,) if radar_type else RADAR_TYPES)
        for level in ((error_level,) if error_level else ERROR_LEVELS)
    ]
    missing = [str(path) for _, _, path in selected if not (path / "metadata.yaml").is_file()]
    if missing:
        raise FileNotFoundError("Missing benchmark datasets:\n" + "\n".join(missing))

    mode = (
        Path(f"multivariate_{profile_mode}")
        if target_param == "multivariate"
        else Path(f"univariate_{profile_mode}") / target_param.lower()
    )
    output_dir = RESULTS_ROOT / mode
    rows = []
    for rtype, level, dataset_dir in selected:
        plot_path = output_dir / "plots" / f"{rtype}_{level}.png" if plots else None
        metrics = evaluate_condition(
            model, dataset_dir, target_param, context_len, horizon_len,
            batch_size, max_test_seqs, plot_path,
        )
        row = {"radar_type": rtype, "error_level": level, **metrics}
        rows.append(row)
        label = (
            f"PRI MAE: {row['mae_pri']:.2f} us"
            if target_param == "multivariate"
            else f"MAE: {row['mae']:.2f} {UNITS[target_param]}"
        )
        print(f"[EVAL] {profile_mode}/{rtype}/{level}: {row['num_sequences']} sequences | {label}")

    results = pd.DataFrame(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_dir / "metrics.csv", index=False)
    lines = [
        f"# TiRex-2 {target_param} zero-shot benchmark ({profile_mode})",
        "",
        f"Dataset size: `{dataset_size}`. Context: {context_len}. Horizon: {horizon_len}.",
        "Scores are means of per-sequence emitter-only MAE, RMSE, and hit rate.",
        "The AOA circular metrics are additional; ordinary AOA metrics match the TimesFM definition.",
        "Sequences with no emitter pulses in the target window are excluded and counted.",
        "The point forecast is TiRex-2's 0.5 quantile (median).",
        "",
        results.to_markdown(index=False),
        "",
    ]
    (output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[SAVED] {output_dir / 'metrics.csv'}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-mode", choices=("fixed", "varying", "both"), default="fixed")
    parser.add_argument("--target-param", choices=(*CHANNELS, "multivariate", "all"), default="PRI")
    parser.add_argument("--dataset-size", default="1000x128")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--max-test-seqs", type=int)
    parser.add_argument("--radar-type", choices=RADAR_TYPES)
    parser.add_argument("--error-level", choices=ERROR_LEVELS)
    parser.add_argument("--model-id", default=MODEL_ID)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--coverage-only", action="store_true")
    args = parser.parse_args()
    if min(args.context_len, args.horizon, args.batch_size) <= 0:
        parser.error("Window lengths and batch size must be positive")
    if args.max_test_seqs is not None and args.max_test_seqs <= 0:
        parser.error("--max-test-seqs must be positive")

    profiles = ("fixed", "varying") if args.profile_mode == "both" else (args.profile_mode,)
    tasks = (*CHANNELS, "multivariate") if args.target_param == "all" else (args.target_param,)
    for profile in profiles:
        coverage = audit_coverage(
            profile, tasks[0], args.dataset_size, args.context_len, args.horizon,
            args.max_test_seqs, args.radar_type, args.error_level,
        )
        print(f"[COVERAGE] {profile}\n{coverage.to_string(index=False)}", flush=True)
        if args.coverage_only:
            continue
        if (coverage.eligible_windows == 0).any():
            parser.error(f"{profile} has a condition without a complete forecast window")

    if args.coverage_only:
        return

    model = load_pipeline(args.model_id, args.device)
    for profile in profiles:
        for task in tasks:
            run_evaluation(
                model, profile, task, args.dataset_size, args.context_len,
                args.horizon, args.batch_size, args.max_test_seqs,
                args.radar_type, args.error_level, not args.no_plots,
            )


if __name__ == "__main__":
    main()
