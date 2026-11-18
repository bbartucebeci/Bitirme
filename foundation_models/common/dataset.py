"""Centralized PDW dataset loader and PyTorch dataset for PULSAR."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
import yaml
from dataset_generator.catalog import RADAR_TYPES, ERROR_LEVELS

from foundation_models.common.windowing import WINDOW_SEED, file_sha256, select_start
from dataset_generator.sequence_io import read_sequence_frame, is_boundary_dataset, boundary_start, reject_legacy_window_loader

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS_ROOT = PROJECT_ROOT / "datasets" / "single_radar"
CHANNELS = ("PRI", "Frequency", "PW", "AOA", "Amplitude")
TOLERANCES = {"PRI": 10.0, "Frequency": 2.0, "PW": 0.1, "AOA": 2.0, "Amplitude": 2.0}
UNITS = {"PRI": "us", "Frequency": "MHz", "PW": "us", "AOA": "deg", "Amplitude": "dBm"}


@dataclass(frozen=True)
class ForecastWindow:
    sequence_id: str
    context: np.ndarray  # channels x context length
    target: np.ndarray  # channels x horizon
    emitter_mask: np.ndarray  # horizon
    start: int = 0  # zero-based interval index after the anchor


@dataclass(frozen=True)
class LoadedSplit:
    windows: list[ForecastWindow]
    total_sequences: int
    skipped_short: int


def conditions(profile_mode: str, dataset_size: str = "1000x128", datasets_root: Path = DATASETS_ROOT) -> Iterator[tuple[str, str, Path]]:
    if profile_mode not in ("fixed", "varying"):
        raise ValueError(f"Unknown profile mode: {profile_mode}")
    for radar_type in RADAR_TYPES:
        for error_level in ERROR_LEVELS:
            yield radar_type, error_level, datasets_root / profile_mode / radar_type / f"{dataset_size}_{error_level}"


def _sequence_frames(split_dir: Path, limit: int | None) -> list[tuple[str, pd.DataFrame]]:
    files = sorted(split_dir.glob("seq_*.csv"))
    if files:
        selected = files[:limit] if limit is not None else files
        return [(file.stem, read_sequence_frame(file)) for file in selected]

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
    window_mode: str = "first",
    window_seed: int = WINDOW_SEED,
    window_manifest: dict[str, Any] | None = None,
) -> LoadedSplit:
    """Select one complete context-to-target window per independent sequence."""
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
    if is_boundary_dataset(metadata) or window_mode == "boundary":
        boundary_start(metadata, context_len, horizon_len, window_mode)
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
        if split == "test" and (window_mode == "random" or (window_mode == "boundary" and window_manifest is not None)):
            if window_manifest is None:
                raise ValueError("Random test windows require a test manifest")
            sequence_key = (f"{metadata['profile_mode']}/{metadata['radar_type']}/"
                            f"{metadata['error_level']}/{sequence_id}")
            expected_hash = window_manifest.get("sequence_sha256", {}).get(sequence_key)
            csv_file = split_dir / f"{sequence_id}.csv"
            if expected_hash is None or not csv_file.is_file() or file_sha256(csv_file) != expected_hash:
                raise ValueError(f"{sequence_id}: test CSV differs from the window manifest")
        missing = {"Radar_ID", "Measured_Delta_TOA", *CHANNELS} - set(frame.columns)
        if missing:
            raise ValueError(f"{sequence_id}: missing columns {sorted(missing)}")
        start = boundary_start(metadata, context_len, horizon_len, window_mode) if is_boundary_dataset(metadata) else select_start(
            len(frame), context_len, horizon_len, window_mode, split,
            str(metadata["profile_mode"]), str(metadata["radar_type"]),
            str(metadata["error_level"]), sequence_id, window_seed, window_manifest,
        )
        if window_mode=="boundary" and window_manifest is not None:
            from foundation_models.common.windowing import window_key
            key=window_key(metadata["profile_mode"],metadata["radar_type"],metadata["error_level"],sequence_id,context_len)
            meta=window_manifest.get("meta",{})
            if meta.get("window_mode")!="boundary" or meta.get("horizon_len")!=horizon_len or window_manifest["windows"].get(key)!=start:
                raise ValueError(f"{sequence_id}: manifest does not match the stored forecast boundary")
        frame = frame.iloc[start : start + context_len + horizon_len].reset_index(drop=True)
        mask = frame["Radar_ID"].eq("R_SINGLE").to_numpy(dtype=bool)
        names = CHANNELS if target_param == "multivariate" else (target_param,)
        context_columns = tuple("Measured_Delta_TOA" if name == "PRI" else name for name in names)
        context = frame.loc[: context_len - 1, list(context_columns)].to_numpy(dtype=np.float32).T.copy()
        target = frame.loc[context_len : context_len + horizon_len - 1, list(names)].to_numpy(dtype=np.float32).T.copy()
        if not np.isfinite(context).all():
            raise ValueError(f"{sequence_id}: non-finite context values")
        windows.append(ForecastWindow(sequence_id, context, target, mask[context_len:], start))
    return LoadedSplit(windows, len(frames), len(frames) - len(windows))


def training_series(windows: list[ForecastWindow]) -> list[np.ndarray]:
    """Give forecasting models exactly one context->target training slice per sequence.

    The first part contains observed values. The final part contains targets;
    non-emitter positions are NaN so models exclude them from loss.
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


def _boundary_training_sequences(dataset_dir, split, target_param, length, horizon, limit):
    """Adapt explicit boundary windows to the existing training Dataset contract."""
    metadata=yaml.safe_load((dataset_dir/"metadata.yaml").read_text(encoding="utf-8"))
    if not is_boundary_dataset(metadata):
        return None
    loaded=load_split(dataset_dir,split,target_param,length,horizon,limit,window_mode="boundary")
    result=[]
    for window in loaded.windows:
        series=np.concatenate((window.context,window.target),axis=1)
        if target_param!="multivariate":series=series[0]
        result.append((window.sequence_id,series,series.copy(),np.r_[np.ones(length,dtype=bool),window.emitter_mask]))
    return result


def clean_pri_context(context: np.ndarray, target_len: Optional[int] = None) -> np.ndarray:
    """Applies ESM front-end gating to raw Measured_Delta_TOA context (reconstructs splits & missing pulses).

    Args:
        context: 1D array of observed pulse intervals.
        target_len: Optional fixed length to pad or slice to.
    """
    x = np.asarray(context, dtype=np.float32).copy()
    if len(x) < 4:
        return x

    med = float(np.median(x))
    if med <= 0:
        return x

    reconstructed: List[float] = []
    i = 0
    n = len(x)
    while i < n:
        val = float(x[i])
        if val < 0.55 * med and (i + 1) < n:
            combined = val + float(x[i + 1])
            if abs(combined - med) < abs(float(x[i + 1]) - med) or combined < 1.45 * med:
                reconstructed.append(combined)
                i += 2
                continue
            else:
                i += 1
                continue
        reconstructed.append(val)
        i += 1

    if len(reconstructed) < 4:
        reconstructed = list(x)

    arr = np.asarray(reconstructed, dtype=np.float32)
    med = float(np.median(arr))

    expanded: List[float] = []
    for val in arr:
        ratio = float(val) / max(1e-5, med)
        if 1.65 <= ratio <= 2.45:
            expanded.extend([float(val) / 2.0, float(val) / 2.0])
        elif 2.45 < ratio <= 3.45:
            expanded.extend([float(val) / 3.0, float(val) / 3.0, float(val) / 3.0])
        elif 0.55 <= ratio < 1.65:
            expanded.append(float(val))
        else:
            expanded.append(med)

    res = np.asarray(expanded, dtype=np.float32)
    if target_len is not None:
        if len(res) < target_len:
            pad = np.full(target_len - len(res), med, dtype=np.float32)
            res = np.concatenate([pad, res])
        elif len(res) > target_len:
            res = res[-target_len:]
    return res


def load_sequence_arrays(
    csv_path: Path,
    target_param: str = "PRI",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reads a single PDW CSV file and extracts context, ground-truth, and emitter mask.

    Args:
        csv_path: Path to sequence CSV.
        target_param: One of 'PRI', 'Frequency', 'PW', 'AOA', 'Amplitude', or 'Measured_Delta_TOA'.

    Returns:
        Tuple of (context_vals, ground_truth_vals, emitter_mask):
        - context_vals: 1D float32 array (observed sequence)
        - ground_truth_vals: 1D float32 array (true emitter parameter sequence)
        - emitter_mask: 1D bool array (True where pulse belongs to true emitter, False for NOISE/ECHO)
    """
    df = read_sequence_frame(csv_path)

    # Drop arrival-time anchor at pulse 0 (Measured_Delta_TOA == 0.0)
    if len(df) > 1 and "Measured_Delta_TOA" in df.columns and float(df["Measured_Delta_TOA"].iloc[0]) == 0.0:
        df = df.iloc[1:].reset_index(drop=True)

    # 1. Emitter mask: True for true emitter pulses, False for NOISE or ECHO
    if "Radar_ID" in df.columns:
        radar_id_series = df["Radar_ID"].astype(str)
        emitter_mask = (radar_id_series == "R_SINGLE").to_numpy(dtype=bool)
    else:
        emitter_mask = np.ones(len(df), dtype=bool)

    # 2. Extract context and ground truth arrays
    param_upper = target_param.upper()
    if param_upper in ["PRI", "MEASURED_DELTA_TOA"]:
        # Context is observed pulse interval stream
        ctx_vals = df["Measured_Delta_TOA"].to_numpy(dtype=np.float32)
        # Ground truth is the true emitter source PRI
        if "PRI" in df.columns:
            tgt_vals = df["PRI"].to_numpy(dtype=np.float32)
        else:
            tgt_vals = ctx_vals.copy()
    elif target_param in df.columns:
        ctx_vals = df[target_param].to_numpy(dtype=np.float32)
        tgt_vals = ctx_vals.copy()
    else:
        raise ValueError(f"Target parameter '{target_param}' not found in {csv_path}. Columns: {df.columns.tolist()}")

    return ctx_vals, tgt_vals, emitter_mask


def load_dataset_sequences(
    dataset_dir: Path,
    split: str = "test",
    max_seqs: Optional[int] = None,
    target_param: str = "PRI",
) -> List[Tuple[str, np.ndarray, np.ndarray, np.ndarray]]:
    """Loads all sequences for a specific dataset, split, and target parameter.

    Returns:
        List of tuples: (sequence_id, context_vals, ground_truth_vals, emitter_mask)
    """
    reject_legacy_window_loader(dataset_dir)
    split_dir = dataset_dir / split
    if not split_dir.exists():
        raise FileNotFoundError(f"Split directory not found: {split_dir}")

    sequences = []

    # 1. Check individual sequence files
    seq_files = sorted(list(split_dir.glob("seq_*.csv")))
    if seq_files:
        if max_seqs is not None and max_seqs > 0:
            seq_files = seq_files[:max_seqs]
        for f in seq_files:
            ctx, tgt, mask = load_sequence_arrays(f, target_param=target_param)
            sequences.append((f.stem, ctx, tgt, mask))
        return sequences

    # 2. Fallback to combined sequences.csv
    comb_file = split_dir / "sequences.csv"
    if comb_file.exists():
        df_all = pd.read_csv(comb_file)
        unique_ids = df_all["sequence_id"].unique()
        if max_seqs is not None and max_seqs > 0:
            unique_ids = unique_ids[:max_seqs]
        for sid in unique_ids:
            df_seq = df_all[df_all["sequence_id"] == sid].sort_values("pulse_index")
            if len(df_seq) > 1 and "Measured_Delta_TOA" in df_seq.columns and float(df_seq["Measured_Delta_TOA"].iloc[0]) == 0.0:
                df_seq = df_seq.iloc[1:].reset_index(drop=True)

            if "Radar_ID" in df_seq.columns:
                mask = (df_seq["Radar_ID"] == "R_SINGLE").to_numpy(dtype=bool)
            else:
                mask = np.ones(len(df_seq), dtype=bool)

            param_upper = target_param.upper()
            if param_upper in ["PRI", "MEASURED_DELTA_TOA"]:
                ctx = df_seq["Measured_Delta_TOA"].to_numpy(dtype=np.float32)
                tgt = df_seq["PRI"].to_numpy(dtype=np.float32) if "PRI" in df_seq.columns else ctx.copy()
            else:
                ctx = df_seq[target_param].to_numpy(dtype=np.float32)
                tgt = ctx.copy()

            sequences.append((sid, ctx, tgt, mask))
        return sequences

    raise FileNotFoundError(f"No sequences found in {split_dir}")


class PDWSequenceDataset(Dataset):
    """PyTorch Dataset for sequence-to-sequence forecasting (Context -> Horizon)."""

    def __init__(
        self,
        sequences: List[Tuple[str, np.ndarray, np.ndarray, np.ndarray]],
        context_len: int = 96,
        horizon_len: int = 32,
    ):
        self.items = []
        self.context_len = context_len
        self.horizon_len = horizon_len

        required_len = context_len + horizon_len
        for seq_id, ctx, tgt, mask in sequences:
            if len(ctx) >= required_len:
                c = ctx[:context_len]
                t = tgt[context_len : context_len + horizon_len]
                m = mask[context_len : context_len + horizon_len]
                self.items.append((seq_id, c, t, m))

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        _, ctx, tgt, mask = self.items[idx]
        # Context shaped (1, context_len) for TimesFM input variate dimension
        ctx_tensor = torch.from_numpy(ctx.copy()).unsqueeze(0).float()
        tgt_tensor = torch.from_numpy(tgt.copy()).float()
        mask_tensor = torch.from_numpy(mask.copy()).bool()
        return ctx_tensor, tgt_tensor, mask_tensor


def create_unified_pdw_dataloader(
    datasets_root: Path,
    profile_mode: str = "fixed",
    split: str = "train",
    radar_types: Optional[List[str]] = None,
    error_levels: Optional[List[str]] = None,
    target_param: str = "PRI",
    context_len: int = 96,
    horizon_len: int = 32,
    batch_size: int = 64,
    shuffle: bool = True,
    max_seqs_per_dataset: Optional[int] = None,
    dataset_size: str = "1000x128",
) -> DataLoader:
    """Builds a unified DataLoader combining sequences across all radar types and error levels."""
    if radar_types is None:
        radar_types = list(RADAR_TYPES)
    if error_levels is None:
        error_levels = list(ERROR_LEVELS)

    all_sequences = []
    for rtype in radar_types:
        for elevel in error_levels:
            folder_name = f"{dataset_size}_{elevel}"
            dataset_dir = datasets_root / rtype / folder_name
            if dataset_dir.exists():
                seqs = _boundary_training_sequences(dataset_dir, split, target_param, context_len, horizon_len, max_seqs_per_dataset)
                if seqs is None:seqs = load_dataset_sequences(
                    dataset_dir,
                    split=split,
                    max_seqs=max_seqs_per_dataset,
                    target_param=target_param,
                )
                all_sequences.extend(seqs)
            else:
                raise FileNotFoundError(f"Missing selected dataset: {dataset_dir}")

    dataset = PDWSequenceDataset(all_sequences, context_len=context_len, horizon_len=horizon_len)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        drop_last=False,
    )


# ==============================================================================
# MULTIVARIATE (5-CHANNEL) DATASET INGESTION & PIPELINE
# ==============================================================================

MULTIVARIATE_CHANNELS = ["PRI", "Frequency", "PW", "AOA", "Amplitude"]
MULTIVARIATE_SCALES = np.array([1000.0, 10000.0, 1.0, 100.0, 50.0], dtype=np.float32)
MULTIVARIATE_WEIGHTS = np.array([0.35, 0.25, 0.15, 0.15, 0.10], dtype=np.float32)
MULTIVARIATE_TOLERANCES = [10.0, 2.0, 0.1, 2.0, 2.0]
MULTIVARIATE_UNITS = ["us", "MHz", "us", "deg", "dBm"]


def load_multivariate_sequence_arrays(
    csv_path: Path,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reads a PDW CSV file and extracts full 5-channel context and ground truth.

    Returns:
        Tuple of (ctx_channels, tgt_channels, emitter_mask):
        - ctx_channels: (5, sequence_len) float32 array
        - tgt_channels: (5, sequence_len) float32 array
        - emitter_mask: (sequence_len,) bool array
    """
    df = read_sequence_frame(csv_path)

    if len(df) > 1 and "Measured_Delta_TOA" in df.columns and float(df["Measured_Delta_TOA"].iloc[0]) == 0.0:
        df = df.iloc[1:].reset_index(drop=True)

    if "Radar_ID" in df.columns:
        emitter_mask = (df["Radar_ID"].astype(str) == "R_SINGLE").to_numpy(dtype=bool)
    else:
        emitter_mask = np.ones(len(df), dtype=bool)

    # 1. PRI (Observed Delta TOA vs Ground Truth PRI)
    ctx_pri = df["Measured_Delta_TOA"].to_numpy(dtype=np.float32)
    tgt_pri = df["PRI"].to_numpy(dtype=np.float32) if "PRI" in df.columns else ctx_pri.copy()

    # 2. Carrier Frequency
    rf_vals = df["Frequency"].to_numpy(dtype=np.float32)

    # 3. Pulse Width
    pw_vals = df["PW"].to_numpy(dtype=np.float32)

    # 4. Angle of Arrival
    aoa_vals = df["AOA"].to_numpy(dtype=np.float32)

    # 5. Amplitude
    amp_vals = df["Amplitude"].to_numpy(dtype=np.float32)

    ctx_channels = np.stack([ctx_pri, rf_vals, pw_vals, aoa_vals, amp_vals], axis=0)
    tgt_channels = np.stack([tgt_pri, rf_vals, pw_vals, aoa_vals, amp_vals], axis=0)

    return ctx_channels, tgt_channels, emitter_mask


def load_multivariate_dataset_sequences(
    dataset_dir: Path | str,
    split: str = "test",
    max_seqs: Optional[int] = None,
) -> List[Tuple[str, np.ndarray, np.ndarray, np.ndarray]]:
    """Loads all 5-channel sequences for a dataset directory and split.

    Returns:
        List of (sequence_id, ctx_channels (5, N), tgt_channels (5, N), mask (N,))
    """
    reject_legacy_window_loader(Path(dataset_dir))
    split_dir = Path(dataset_dir) / split
    if not split_dir.exists():
        raise FileNotFoundError(f"Split directory not found: {split_dir}")

    sequences = []
    seq_files = sorted(list(split_dir.glob("seq_*.csv")))
    if seq_files:
        if max_seqs is not None and max_seqs > 0:
            seq_files = seq_files[:max_seqs]
        for f in seq_files:
            ctx, tgt, mask = load_multivariate_sequence_arrays(f)
            sequences.append((f.stem, ctx, tgt, mask))
        return sequences

    # Fallback to sequences.csv
    comb_file = split_dir / "sequences.csv"
    if comb_file.exists():
        df_all = pd.read_csv(comb_file)
        unique_ids = df_all["sequence_id"].unique()
        if max_seqs is not None and max_seqs > 0:
            unique_ids = unique_ids[:max_seqs]
        for sid in unique_ids:
            df_seq = df_all[df_all["sequence_id"] == sid].sort_values("pulse_index")
            if len(df_seq) > 1 and "Measured_Delta_TOA" in df_seq.columns and float(df_seq["Measured_Delta_TOA"].iloc[0]) == 0.0:
                df_seq = df_seq.iloc[1:].reset_index(drop=True)

            mask = (df_seq["Radar_ID"] == "R_SINGLE").to_numpy(dtype=bool) if "Radar_ID" in df_seq.columns else np.ones(len(df_seq), dtype=bool)
            ctx_pri = df_seq["Measured_Delta_TOA"].to_numpy(dtype=np.float32)
            tgt_pri = df_seq["PRI"].to_numpy(dtype=np.float32) if "PRI" in df_seq.columns else ctx_pri.copy()
            rf_vals = df_seq["Frequency"].to_numpy(dtype=np.float32)
            pw_vals = df_seq["PW"].to_numpy(dtype=np.float32)
            aoa_vals = df_seq["AOA"].to_numpy(dtype=np.float32)
            amp_vals = df_seq["Amplitude"].to_numpy(dtype=np.float32)

            ctx = np.stack([ctx_pri, rf_vals, pw_vals, aoa_vals, amp_vals], axis=0)
            tgt = np.stack([tgt_pri, rf_vals, pw_vals, aoa_vals, amp_vals], axis=0)
            sequences.append((sid, ctx, tgt, mask))
        return sequences

    raise FileNotFoundError(f"No sequences found in {split_dir}")


class MultivariatePDWDataset(Dataset):
    """PyTorch Dataset for 5-channel Joint Multivariate Forecasting."""

    def __init__(
        self,
        sequences: List[Tuple[str, np.ndarray, np.ndarray, np.ndarray]],
        context_len: int = 96,
        horizon_len: int = 32,
    ):
        self.items = []
        self.context_len = context_len
        self.horizon_len = horizon_len

        required_len = context_len + horizon_len
        for seq_id, ctx, tgt, mask in sequences:
            if ctx.shape[1] >= required_len:
                c = ctx[:, :context_len]
                t = tgt[:, context_len : context_len + horizon_len]
                m = mask[context_len : context_len + horizon_len]
                self.items.append((seq_id, c, t, m))

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        _, ctx, tgt, mask = self.items[idx]
        ctx_tensor = torch.from_numpy(ctx.copy()).float()      # (5, context_len)
        tgt_tensor = torch.from_numpy(tgt.copy()).float()      # (5, horizon_len)
        mask_tensor = torch.from_numpy(mask.copy()).bool()     # (horizon_len,)
        return ctx_tensor, tgt_tensor, mask_tensor


def create_unified_multivariate_dataloader(
    datasets_root: Path,
    profile_mode: str = "fixed",
    split: str = "train",
    radar_types: Optional[List[str]] = None,
    error_levels: Optional[List[str]] = None,
    context_len: int = 96,
    horizon_len: int = 32,
    batch_size: int = 64,
    shuffle: bool = True,
    max_seqs_per_dataset: Optional[int] = None,
    dataset_size: str = "1000x128",
) -> DataLoader:
    """Builds a unified DataLoader combining 5-channel sequences across all datasets."""
    if radar_types is None:
        radar_types = list(RADAR_TYPES)
    if error_levels is None:
        error_levels = list(ERROR_LEVELS)

    all_sequences = []
    for rtype in radar_types:
        for elevel in error_levels:
            folder_name = f"{dataset_size}_{elevel}"
            dataset_dir = datasets_root / rtype / folder_name
            if dataset_dir.exists():
                seqs = _boundary_training_sequences(dataset_dir, split, "multivariate", context_len, horizon_len, max_seqs_per_dataset)
                if seqs is None:seqs = load_multivariate_dataset_sequences(
                    dataset_dir,
                    split=split,
                    max_seqs=max_seqs_per_dataset,
                )
                all_sequences.extend(seqs)
            else:
                raise FileNotFoundError(f"Missing selected dataset: {dataset_dir}")

    dataset = MultivariatePDWDataset(all_sequences, context_len=context_len, horizon_len=horizon_len)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        drop_last=False,
    )

