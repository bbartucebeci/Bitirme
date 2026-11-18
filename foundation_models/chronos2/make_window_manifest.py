"""Create a test-window manifest usable by Chronos-2 and the unchanged classical sweep."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml
from dataset_generator.catalog import RADAR_TYPES, ERROR_LEVELS

from foundation_models.common.windowing import (
    WINDOW_SEED,
    draw_random_start,
    file_sha256,
    window_key,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS_ROOT = PROJECT_ROOT / "datasets" / "single_radar"
CONTEXT_LENS = (96, 256, 512, 992)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a verified Chronos/classical test-window manifest")
    parser.add_argument("--dataset-size", default="1000x1024")
    parser.add_argument("--datasets-root", type=Path, default=DATASETS_ROOT, help="Root containing fixed/ and varying/")
    parser.add_argument("--context-lens", type=int, nargs="+", default=CONTEXT_LENS)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--seed", type=int, default=WINDOW_SEED)
    parser.add_argument("--window-mode", choices=("random", "tail"), default="random")
    parser.add_argument("--profiles", nargs="+", choices=("fixed", "varying"), default=("fixed", "varying"))
    parser.add_argument("--radar-types", nargs="+", choices=RADAR_TYPES, default=RADAR_TYPES)
    parser.add_argument("--error-levels", nargs="+", choices=ERROR_LEVELS, default=ERROR_LEVELS)
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "datasets" / "windows_1024_lab.json")
    args = parser.parse_args()
    if args.max_test_seqs <= 0 or args.horizon <= 0 or any(length <= 0 for length in args.context_lens):
        parser.error("Window sizes and --max-test-seqs must be positive")

    expected_pulses = int(args.dataset_size.split("x")[1])
    windows: dict[str, int] = {}
    lengths: dict[str, int] = {}
    hashes: dict[str, str] = {}
    all_noise = {str(length): 0 for length in args.context_lens}
    for profile in args.profiles:
        for radar_type in args.radar_types:
            for level in args.error_levels:
                dataset_dir = args.datasets_root / profile / radar_type / f"{args.dataset_size}_{level}"
                with (dataset_dir / "metadata.yaml").open(encoding="utf-8") as handle:
                    metadata = yaml.safe_load(handle)
                if int(metadata["expected_pulses_per_sequence"]) != expected_pulses:
                    raise ValueError(f"{dataset_dir}: metadata pulse count differs from {args.dataset_size}")
                test_dir = dataset_dir / "test"
                files = sorted(test_dir.glob("seq_*.csv"))[: args.max_test_seqs]
                expected_files = min(args.max_test_seqs, int(metadata["split"]["test"]["sequence_count"]))
                if len(files) != expected_files:
                    raise ValueError(f"{test_dir}: expected {expected_files} sequence CSVs, found {len(files)}")
                for csv_file in files:
                    frame = pd.read_csv(csv_file, usecols=["Radar_ID", "Measured_Delta_TOA"])
                    if len(frame) > 1 and float(frame["Measured_Delta_TOA"].iloc[0]) == 0.0:
                        frame = frame.iloc[1:]
                    n = len(frame)
                    if n != expected_pulses:
                        raise ValueError(f"{csv_file}: expected {expected_pulses} intervals after anchor, found {n}")
                    sequence_key = f"{profile}/{radar_type}/{level}/{csv_file.stem}"
                    lengths[sequence_key] = n
                    hashes[sequence_key] = file_sha256(csv_file)
                    emitter = frame["Radar_ID"].eq("R_SINGLE").to_numpy(dtype=bool)
                    for length in args.context_lens:
                        key = window_key(profile, radar_type, level, csv_file.stem, length)
                        if length + args.horizon > n:
                            raise ValueError(f"{csv_file}: {length}+{args.horizon} exceeds {n}")
                        start = (draw_random_start(n, length, args.horizon, args.seed, key)
                                 if args.window_mode == "random" else n - length - args.horizon)
                        windows[key] = start
                        if not emitter[start + length : start + length + args.horizon].any():
                            all_noise[str(length)] += 1
                print(f"[WINDOWS] {profile}/{radar_type}/{level}: {len(files)} test sequences")

    manifest = {
        "meta": {
            "seed": args.seed,
            "window_mode": args.window_mode,
            "dataset_size": args.dataset_size,
            "context_lens": args.context_lens,
            "horizon_len": args.horizon,
            "split": "test",
            "key_format": "profile/law/level/sequence_id/L",
            "rule": "seeded uniform start in [0, n-L-H]" if args.window_mode == "random" else "s = n-L-H",
            "all_noise_windows_by_L": all_noise,
            "n_min": min(lengths.values()),
            "n_max": max(lengths.values()),
        },
        "sequence_lengths": lengths,
        "sequence_sha256": hashes,
        "windows": windows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=0, sort_keys=True), encoding="utf-8")
    print(f"[SAVED] {args.output}: {len(windows)} windows; all-noise targets: {all_noise}")


if __name__ == "__main__":
    main()
