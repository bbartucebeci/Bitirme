#!/usr/bin/env python3
"""Draws the random context start of every test sequence once and saves it to a JSON manifest.

For each (profile, law, level, test sequence, L) the start s is drawn uniformly from
[0, n - L - H], where n is the number of pulses after the anchor row, so that
context = pulses s .. s+L-1 and horizon = s+L .. s+L+H-1 fit in the sequence. Each draw
is seeded with crc32(f"{seed}|{key}"), so it is reproducible and independent of order.
Sequences shorter than L + H (missed pulses) get s = 0 and use the legacy fallback in
common.extract_window (context shortened to n - H); they are counted in meta.

Every evaluation script reads this manifest (--window-manifest) instead of re-drawing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.common import (
    DEFAULT_DATASET_SIZE,
    DEFAULT_DATASETS_ROOT,
    DEFAULT_WINDOW_SEED,
    ERROR_LEVELS,
    RADAR_TYPES,
    draw_window_start,
    load_dataset_sequences,
    window_key,
)


def main():
    parser = argparse.ArgumentParser(description="Build the random-context-start window manifest")
    parser.add_argument("--dataset-size", default=DEFAULT_DATASET_SIZE)
    parser.add_argument("--datasets-root", type=Path, default=DEFAULT_DATASETS_ROOT)
    parser.add_argument("--context-lens", type=int, nargs="+", default=[96, 256, 512, 992])
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--seed", type=int, default=DEFAULT_WINDOW_SEED)
    parser.add_argument("--profiles", nargs="+", default=["fixed", "varying"])
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "results" / "windows_1024.json")
    args = parser.parse_args()

    windows = {}
    lengths = {}
    short = {str(L): 0 for L in args.context_lens}
    for prof in args.profiles:
        for rtype in RADAR_TYPES:
            for level in ERROR_LEVELS:
                ddir = args.datasets_root / prof / rtype / f"{args.dataset_size}_{level}"
                seqs = load_dataset_sequences(ddir, split="test", max_seqs=args.max_test_seqs)
                for sid, ctx_vals, _, _ in seqs:
                    n = len(ctx_vals)
                    lengths[f"{prof}/{rtype}/{level}/{sid}"] = n
                    for L in args.context_lens:
                        key = window_key(prof, rtype, level, sid, L)
                        windows[key] = draw_window_start(n, L, args.horizon, args.seed, key)
                        if n < L + args.horizon:
                            short[str(L)] += 1
                print(f"  {prof}/{rtype}/{level}: {len(seqs)} sequences")

    manifest = {
        "meta": {
            "seed": args.seed,
            "dataset_size": args.dataset_size,
            "context_lens": args.context_lens,
            "horizon_len": args.horizon,
            "split": "test",
            "rule": "s ~ U{0, n-L-H}, rng = default_rng(crc32(f'{seed}|{key}')); "
                    "n = pulses after anchor row; n < L+H -> s = 0 with context n-H (fallback)",
            "key_format": "profile/law/level/sequence_id/L",
            "fallback_counts_by_L": short,
            "n_min": min(lengths.values()),
            "n_max": max(lengths.values()),
        },
        "sequence_lengths": lengths,
        "windows": windows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=0, sort_keys=True)
    print(f"[SAVED] {args.output}: {len(windows)} windows | fallbacks by L: {short} | "
          f"n in [{manifest['meta']['n_min']}, {manifest['meta']['n_max']}]")


if __name__ == "__main__":
    main()
