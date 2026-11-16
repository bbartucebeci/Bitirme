#!/usr/bin/env python3
"""Writes SHA256 hashes of every test-split file of the single-radar datasets of one size,
together with the git commit and the generation command, to datasets/MANIFEST_<pulses>.txt."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-size", default="1000x1024")
    parser.add_argument("--datasets-root", type=Path, default=PROJECT_ROOT / "datasets")
    parser.add_argument("--command", default="python dataset_generator/generate_datasets.py --radar-type all_single "
                                            "--profile-mode both --error-level all --pulses-per-sequence 1024")
    args = parser.parse_args()

    pulses = args.dataset_size.split("x")[1]
    out = args.datasets_root / f"MANIFEST_{pulses}.txt"
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "dataset_generator", "synthetic_data_generation", "configs"],
                           cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.strip()

    files = sorted((args.datasets_root / "single_radar").glob(f"*/*/{args.dataset_size}_*/test/*.csv"))
    lines = [
        f"# PULSAR single-radar datasets {args.dataset_size} - SHA256 of all test-split files",
        f"# git commit: {commit}" + (" (generator files had uncommitted changes)" if dirty else ""),
        f"# command: {args.command}",
        f"# files: {len(files)}",
        "",
    ]
    for f in files:
        lines.append(f"{sha256(f)}  {f.relative_to(args.datasets_root).as_posix()}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[SAVED] {out} ({len(files)} files)")


if __name__ == "__main__":
    main()
