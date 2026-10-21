"""Centralized PDW dataset loader and PyTorch dataset for PULSAR."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader


def load_sequence_pri(csv_path: Path) -> np.ndarray:
    """Reads a single PDW CSV file and returns the clean PRI interval array."""
    df = pd.read_csv(csv_path)
    if "Measured_Delta_TOA" in df.columns:
        pri = df["Measured_Delta_TOA"].to_numpy(dtype=np.float32)
        # Drop anchor index 0 if it is 0.0
        if len(pri) > 1 and pri[0] == 0.0:
            pri = pri[1:]
        return pri
    raise ValueError(f"No Measured_Delta_TOA column found in {csv_path}")


def load_dataset_sequences(
    dataset_dir: Path,
    split: str = "test",
    max_seqs: Optional[int] = None,
) -> List[Tuple[str, np.ndarray]]:
    """Loads all sequences for a specific dataset and split."""
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
            pri = load_sequence_pri(f)
            sequences.append((f.stem, pri))
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
            pri = df_seq["Measured_Delta_TOA"].to_numpy(dtype=np.float32)
            if len(pri) > 1 and pri[0] == 0.0:
                pri = pri[1:]
            sequences.append((sid, pri))
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
                seqs = load_dataset_sequences(dataset_dir, split=split, max_seqs=max_seqs_per_dataset)
                all_sequences.extend(seqs)

    dataset = PDWSequenceDataset(all_sequences, context_len=context_len, horizon_len=horizon_len)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        drop_last=False,
    )

