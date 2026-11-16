"""Reproducible forecast windows shared with the classical 1024-pulse sweep."""

from __future__ import annotations

import hashlib
import json
import zlib
from pathlib import Path
from typing import Any

import numpy as np


WINDOW_SEED = 20261116
WINDOW_MODES = ("first", "random", "tail")


def window_key(profile: str, radar_type: str, error_level: str, sequence_id: str, context_len: int) -> str:
    return f"{profile}/{radar_type}/{error_level}/{sequence_id}/{context_len}"


def draw_random_start(n_pulses: int, context_len: int, horizon_len: int, seed: int, key: str) -> int:
    """Match the classical sweep's seeded, inclusive uniform window draw."""
    max_start = n_pulses - context_len - horizon_len
    if max_start < 0:
        raise ValueError(f"{key}: {n_pulses} intervals cannot fit {context_len}+{horizon_len}")
    if max_start == 0:
        return 0
    rng = np.random.default_rng(zlib.crc32(f"{seed}|{key}".encode("utf-8")))
    return int(rng.integers(0, max_start + 1))


def file_sha256(path: Path) -> str:
    """Fingerprint the exact per-sequence CSV used by both forecasting pipelines."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_test_manifest(path: Path, dataset_size: str, context_len: int, horizon_len: int, seed: int) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    meta = manifest.get("meta", {})
    expected = {"split": "test", "dataset_size": dataset_size, "horizon_len": horizon_len,
                "seed": seed, "window_mode": "random"}
    for field, value in expected.items():
        if meta.get(field) != value:
            raise ValueError(f"{path}: manifest {field}={meta.get(field)!r}, expected {value!r}")
    if context_len not in meta.get("context_lens", []):
        raise ValueError(f"{path}: context length {context_len} is absent from manifest")
    if any(field not in manifest for field in ("windows", "sequence_lengths", "sequence_sha256")):
        raise ValueError(f"{path}: incomplete window manifest")
    return manifest


def select_start(
    n_pulses: int,
    context_len: int,
    horizon_len: int,
    mode: str,
    split: str,
    profile: str,
    radar_type: str,
    error_level: str,
    sequence_id: str,
    seed: int = WINDOW_SEED,
    manifest: dict[str, Any] | None = None,
) -> int:
    max_start = n_pulses - context_len - horizon_len
    if max_start < 0:
        raise ValueError(f"{sequence_id}: {n_pulses} intervals cannot fit {context_len}+{horizon_len}")
    if mode == "first":
        return 0
    if mode == "tail":
        return max_start
    if mode != "random":
        raise ValueError(f"Unknown window mode: {mode}")

    key = window_key(profile, radar_type, error_level, sequence_id, context_len)
    if split == "test":
        if manifest is None:
            raise ValueError("Random test windows require a test manifest from the evaluated dataset")
        sequence_key = key.rsplit("/", 1)[0]
        if int(manifest["sequence_lengths"].get(sequence_key, -1)) != n_pulses:
            raise ValueError(f"{sequence_id}: manifest sequence length differs from dataset")
        if key not in manifest["windows"]:
            raise KeyError(f"Missing test window: {key}")
        start = int(manifest["windows"][key])
    else:
        # Include the split so train and validation have independent draws.
        start = draw_random_start(n_pulses, context_len, horizon_len, seed, f"{split}/{key}")
    if not 0 <= start <= max_start:
        raise ValueError(f"{sequence_id}: start {start} is outside [0, {max_start}]")
    return start


def experiment_tag(dataset_size: str, mode: str, context_len: int, horizon_len: int, seed: int) -> str:
    return f"{dataset_size}_{mode}_L{context_len}_H{horizon_len}_w{seed}"
