"""Centralized PDW dataset loader and PyTorch dataset for PULSAR."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader


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
    df = pd.read_csv(csv_path)

    # If 129 pulses with anchor at pulse 0 (Measured_Delta_TOA == 0.0), drop anchor
    if len(df) == 129 and "Measured_Delta_TOA" in df.columns and df["Measured_Delta_TOA"].iloc[0] == 0.0:
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
            if len(df_seq) == 129 and df_seq["Measured_Delta_TOA"].iloc[0] == 0.0:
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
) -> DataLoader:
    """Builds a unified DataLoader combining sequences across all radar types and error levels."""
    if radar_types is None:
        radar_types = ["stable", "jitter", "stagger", "dwell_and_switch", "sliding"]
    if error_levels is None:
        error_levels = ["clean", "error_lv1", "error_lv2", "error_lv3"]

    all_sequences = []
    for rtype in radar_types:
        for elevel in error_levels:
            folder_name = f"1000x128_{elevel}"
            dataset_dir = datasets_root / rtype / folder_name
            if dataset_dir.exists():
                seqs = load_dataset_sequences(
                    dataset_dir,
                    split=split,
                    max_seqs=max_seqs_per_dataset,
                    target_param=target_param,
                )
                all_sequences.extend(seqs)

    dataset = PDWSequenceDataset(all_sequences, context_len=context_len, horizon_len=horizon_len)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        drop_last=False,
    )
