"""Centralized PDW dataset loader and PyTorch dataset for PULSAR."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader


def load_sequence_column(csv_path: Path, col_name: str = "Measured_Delta_TOA") -> np.ndarray:
    """Reads a single PDW CSV file and returns the specified parameter array."""
    df = pd.read_csv(csv_path)
    if col_name not in df.columns:
        raise ValueError(f"No '{col_name}' column found in {csv_path}. Available: {df.columns.tolist()}")
    vals = df[col_name].to_numpy(dtype=np.float32)
    # If Measured_Delta_TOA, drop anchor index 0 (value 0.0) so length matches 128 intervals
    if col_name == "Measured_Delta_TOA" and len(vals) > 1 and vals[0] == 0.0:
        vals = vals[1:]
    elif len(vals) == 129:
        # Align with the 128 pulse interval length of the sequence
        vals = vals[1:]
    return vals


def load_sequence_pri(csv_path: Path) -> np.ndarray:
    """Backwards-compatible helper for loading PRI."""
    return load_sequence_column(csv_path, col_name="Measured_Delta_TOA")


def load_dataset_sequences(
    dataset_dir: Path,
    split: str = "test",
    max_seqs: Optional[int] = None,
    col_name: str = "Measured_Delta_TOA",
) -> List[Tuple[str, np.ndarray]]:
    """Loads all sequences for a specific dataset, split, and target column."""
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
            vals = load_sequence_column(f, col_name=col_name)
            sequences.append((f.stem, vals))
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
            vals = df_seq[col_name].to_numpy(dtype=np.float32)
            if col_name == "Measured_Delta_TOA" and len(vals) > 1 and vals[0] == 0.0:
                vals = vals[1:]
            elif len(vals) == 129:
                vals = vals[1:]
            sequences.append((sid, vals))
        return sequences

    raise FileNotFoundError(f"No sequences found in {split_dir}")


class PDWSequenceDataset(Dataset):
    """PyTorch Dataset for sequence-to-sequence forecasting (Context -> Horizon)."""

    def __init__(
        self,
        sequences: List[Tuple[str, np.ndarray]],
        context_len: int = 96,
        horizon_len: int = 32,
    ):
        self.items = []
        self.context_len = context_len
        self.horizon_len = horizon_len

        required_len = context_len + horizon_len
        for seq_id, pri in sequences:
            if len(pri) >= required_len:
                ctx = pri[:context_len]
                tgt = pri[context_len : context_len + horizon_len]
                self.items.append((seq_id, ctx, tgt))

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        _, ctx, tgt = self.items[idx]
        # Context shaped (1, context_len) for TimesFM input variate dimension
        ctx_tensor = torch.from_numpy(ctx).unsqueeze(0).float()
        tgt_tensor = torch.from_numpy(tgt).float()
        return ctx_tensor, tgt_tensor


def create_unified_pdw_dataloader(
    datasets_root: Path,
    profile_mode: str = "fixed",
    split: str = "train",
    radar_types: Optional[List[str]] = None,
    error_levels: Optional[List[str]] = None,
    col_name: str = "Measured_Delta_TOA",
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
                    col_name=col_name,
                )
                all_sequences.extend(seqs)

    dataset = PDWSequenceDataset(all_sequences, context_len=context_len, horizon_len=horizon_len)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        drop_last=False,
    )

