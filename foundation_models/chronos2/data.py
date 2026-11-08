"""Load the branch's single-radar CSVs as independent forecast windows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS_ROOT = PROJECT_ROOT / "datasets" / "single_radar"
RADAR_TYPES = ("stable", "jitter", "stagger", "dwell_and_switch", "sliding")
ERROR_LEVELS = ("clean", "error_lv1", "error_lv2", "error_lv3")
CHANNELS = ("PRI", "Frequency", "PW", "AOA", "Amplitude")
TOLERANCES = {"PRI": 10.0, "Frequency": 2.0, "PW": 0.1, "AOA": 2.0, "Amplitude": 2.0}
UNITS = {"PRI": "us", "Frequency": "MHz", "PW": "us", "AOA": "deg", "Amplitude": "dBm"}


@dataclass(frozen=True)
class ForecastWindow:
    sequence_id: str
    context: np.ndarray  # channels x context length
    target: np.ndarray  # channels x horizon
    emitter_mask: np.ndarray  # horizon


@dataclass(frozen=True)
class LoadedSplit:
    windows: list[ForecastWindow]
    total_sequences: int
    skipped_short: int


def conditions(profile_mode: str, dataset_size: str = "1000x128") -> Iterator[tuple[str, str, Path]]:
    if profile_mode not in ("fixed", "varying"):
        raise ValueError(f"Unknown profile mode: {profile_mode}")
    for radar_type in RADAR_TYPES:
        for error_level in ERROR_LEVELS:
            yield radar_type, error_level, DATASETS_ROOT / profile_mode / radar_type / f"{dataset_size}_{error_level}"


def _sequence_frames(split_dir: Path, limit: int | None) -> list[tuple[str, pd.DataFrame]]:
    files = sorted(split_dir.glob("seq_*.csv"))
    if files:
        selected = files[:limit] if limit is not None else files
        return [(file.stem, pd.read_csv(file)) for file in selected]

    combined = split_dir / "sequences.csv"
    if not combined.is_file():
        raise FileNotFoundError(f"No sequence CSVs in {split_dir}")
    grouped = pd.read_csv(combined).groupby("sequence_id", sort=True)
    frames = []
    for sequence_id, frame in grouped:
        frames.append((str(sequence_id), frame))
        if limit is not None and len(frames) >= limit:
            break
    return frames


def load_split(
    dataset_dir: Path,
    split: str,
    target_param: str = "PRI",
    context_len: int = 96,
    horizon_len: int = 32,
    limit: int | None = None,
) -> LoadedSplit:
    """Use the first context+horizon pulses; never join distinct sequences."""
    if target_param not in (*CHANNELS, "multivariate"):
        raise ValueError(f"Unknown target parameter: {target_param}")
    if split not in ("train", "val", "test"):
        raise ValueError(f"Unknown split: {split}")
    if context_len <= 0 or horizon_len <= 0 or (limit is not None and limit <= 0):
        raise ValueError("Window lengths and limit must be positive")

    metadata_path = dataset_dir / "metadata.yaml"
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Missing dataset metadata: {metadata_path}")
    with metadata_path.open(encoding="utf-8") as handle:
        metadata = yaml.safe_load(handle)
    expected_count = int(metadata["split"][split]["sequence_count"])
    expected_pulses = int(metadata["expected_pulses_per_sequence"])
    if context_len + horizon_len > expected_pulses:
        raise ValueError(f"{dataset_dir}: window exceeds {expected_pulses} generated intervals")

    split_dir = dataset_dir / split
    if not split_dir.is_dir():
        raise FileNotFoundError(f"Missing split: {split_dir}")
    frames = _sequence_frames(split_dir, limit)
    required = expected_count if limit is None else min(limit, expected_count)
    if len(frames) != required:
        raise ValueError(f"{split_dir}: expected {required} sequences, found {len(frames)}")

    windows = []
    for sequence_id, frame in frames:
        frame = frame.sort_values("pulse_index").reset_index(drop=True)
        if "sequence_id" in frame and frame["sequence_id"].nunique() != 1:
            raise ValueError(f"{sequence_id}: contains multiple sequence IDs")
        # Drop arrival-time anchor at pulse 0 (Measured_Delta_TOA == 0.0)
        if len(frame) > 1 and "Measured_Delta_TOA" in frame and float(frame.loc[0, "Measured_Delta_TOA"]) == 0.0:
            frame = frame.iloc[1:].reset_index(drop=True)
        if len(frame) < context_len + horizon_len:
            continue
        frame = frame.iloc[: context_len + horizon_len]

        missing = {"Radar_ID", "Measured_Delta_TOA", *CHANNELS} - set(frame.columns)
        if missing:
            raise ValueError(f"{sequence_id}: missing columns {sorted(missing)}")
        mask = frame["Radar_ID"].eq("R_SINGLE").to_numpy(dtype=bool)
        names = CHANNELS if target_param == "multivariate" else (target_param,)
        context_columns = tuple("Measured_Delta_TOA" if name == "PRI" else name for name in names)
        context = frame.loc[: context_len - 1, list(context_columns)].to_numpy(dtype=np.float32).T
        target = frame.loc[context_len : context_len + horizon_len - 1, list(names)].to_numpy(dtype=np.float32).T
        if not np.isfinite(context).all():
            raise ValueError(f"{sequence_id}: non-finite context values")
        windows.append(ForecastWindow(sequence_id, context, target, mask[context_len:]))
    return LoadedSplit(windows, len(frames), len(frames) - len(windows))


def training_series(windows: list[ForecastWindow]) -> list[np.ndarray]:
    """Give Chronos exactly one context->target training slice per sequence.

    The first part contains observed values. The final part contains targets;
    non-emitter positions are NaN so Chronos excludes them from its loss.
    """
    series = []
    for window in windows:
        if not window.emitter_mask.any():
            continue
        future = window.target.copy()
        future[:, ~window.emitter_mask] = np.nan
        if not np.isfinite(future[:, window.emitter_mask]).all():
            raise ValueError(f"{window.sequence_id}: non-finite emitter targets")
        series.append(np.concatenate((window.context, future), axis=1))
    if not series:
        raise ValueError("No trainable sequences with emitter targets")
    return series
