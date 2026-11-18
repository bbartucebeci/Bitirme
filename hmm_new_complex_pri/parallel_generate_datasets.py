#!/usr/bin/env python3
"""16-core parallel generator for the full new_complex_pri (1000x1056) dataset.

Generates all 128 conditions (2 profiles x 8 radar types x 8 error levels) with
700 train / 100 val / 200 test sequences per condition (128,000 CSV files) under
datasets/new_complex_pri/production/C1024_H32, using one worker process per core
without modifying any existing repository files.
"""

from __future__ import annotations

import os

# Keep BLAS/OpenMP single-threaded inside each worker so ProcessPoolExecutor scales across all cores.
for _env_var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_env_var, "1")

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dataset_generator.catalog import (
    ERROR_LEVELS,
    NEW_COMPLEX_DATASETS_ROOT,
    NEW_COMPLEX_PRI,
    RADAR_TYPES,
    SCHEMA_V2,
)
from dataset_generator.generate_datasets import (
    CONFIGS_DIR,
    RADAR_CLASSES,
    build_single_dataset,
    load_all_configs,
)


def _is_condition_complete(
    dest_dir: Path,
    profile_mode: str,
    train_count: int = 700,
    val_count: int = 100,
    test_count: int = 200,
) -> bool:
    """Returns True only if all expected files and split CSV counts exist for one condition."""
    if not (dest_dir / "metadata.yaml").is_file():
        return False
    if not (dest_dir / "generation.csv").is_file():
        return False
    if profile_mode == "varying" and not (dest_dir / "profiles.csv").is_file():
        return False
    for split_name, expected_n in (("train", train_count), ("val", val_count), ("test", test_count)):
        split_dir = dest_dir / split_name
        if not split_dir.is_dir():
            return False
        if len(list(split_dir.glob("seq_*.csv"))) != expected_n:
            return False
    return True


def _generate_one_condition(task: Tuple[Any, ...]) -> Tuple[str, str, str, str, float]:
    """Worker entrypoint generating a single (profile_mode, radar_type, error_level) condition."""
    (
        output_root_str,
        rtype,
        pmode,
        elvl,
        sequence_count,
        pulses_per_sequence,
        seed,
        error_config,
        profiles_cfg,
        freq_mode,
        context_intervals,
        max_horizon,
    ) = task

    output_root = Path(output_root_str)
    dataset_folder = f"{sequence_count}x{pulses_per_sequence}_{elvl}"
    dest_dir = output_root / "single_radar" / pmode / rtype / dataset_folder

    train_count = int(0.7 * sequence_count)
    val_count = int(0.1 * sequence_count)
    test_count = sequence_count - train_count - val_count

    if _is_condition_complete(dest_dir, pmode, train_count, val_count, test_count):
        return pmode, rtype, elvl, "skipped", 0.0

    # Clean up partial interrupted condition directory before calling build_single_dataset.
    if dest_dir.exists():
        shutil.rmtree(dest_dir)

    t0 = time.perf_counter()
    build_single_dataset(
        output_root=output_root,
        radar_type=rtype,
        profile_mode=pmode,
        error_level=elvl,
        sequence_count=sequence_count,
        pulses_per_sequence=pulses_per_sequence,
        seed=seed,
        error_config=error_config,
        profiles_cfg=profiles_cfg,
        freq_mode=freq_mode,
        protocol=SCHEMA_V2,
        context_intervals=context_intervals,
        max_horizon=max_horizon,
    )
    return pmode, rtype, elvl, "generated", time.perf_counter() - t0


def _write_collection_atomic(output_dir: Path, collection: Dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "collection.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(collection, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_against_reference_manifest(output_dir: Path, manifest_path: Path) -> None:
    """Verifies generated test CSV SHA256 hashes and v2 metadata schema against Chronos test_windows.json."""
    if not manifest_path.is_file():
        print(f"[INFO] Reference manifest not found at {manifest_path}; skipping hash check.")
        return

    import yaml

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    single_root = output_dir / "single_radar"

    expected_seq_hashes: Dict[str, str] = manifest.get("sequence_sha256", {})
    expected_meta_hashes: Dict[str, str] = manifest.get("metadata_sha256", {})

    print(
        f"[VERIFY] Checking {len(expected_meta_hashes)} metadata files (schema_version={SCHEMA_V2}) "
        f"and {len(expected_seq_hashes)} test CSV SHA256 hashes against {manifest_path.name}..."
    )
    for condition in expected_meta_hashes:
        pmode, rtype, elvl = condition.split("/")
        meta_path = single_root / pmode / rtype / f"1000x1056_{elvl}" / "metadata.yaml"
        if not meta_path.is_file():
            raise RuntimeError(f"Missing metadata.yaml for {condition}: {meta_path}")
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        if meta.get("schema_version") != SCHEMA_V2:
            raise RuntimeError(f"{meta_path}: unexpected schema_version={meta.get('schema_version')!r}")

    seq_mismatches = 0
    for seq_key, expected_hash in expected_seq_hashes.items():
        pmode, rtype, elvl, sid = seq_key.split("/")
        csv_path = single_root / pmode / rtype / f"1000x1056_{elvl}" / "test" / f"{sid}.csv"
        actual_hash = _file_sha256(csv_path)
        if actual_hash != expected_hash:
            seq_mismatches += 1
            if seq_mismatches <= 5:
                print(f"  [CSV MISMATCH] {seq_key}: actual={actual_hash} != expected={expected_hash}")

    if seq_mismatches:
        raise RuntimeError(f"Hash verification failed: {seq_mismatches} test CSV SHA256 mismatches")
    print(
        f"[VERIFY] Verified all {len(expected_meta_hashes)} metadata.yaml ({SCHEMA_V2}) files and "
        f"100% byte-identical match across all {len(expected_seq_hashes)} test CSV SHA256 hashes!"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=NEW_COMPLEX_DATASETS_ROOT / "production" / "C1024_H32",
        help="Target production collection root",
    )
    parser.add_argument("--config-dir", type=Path, default=CONFIGS_DIR)
    parser.add_argument("--context-intervals", type=int, default=1024)
    parser.add_argument("--max-horizon", type=int, default=32)
    parser.add_argument("--sequence-count", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20261020)
    parser.add_argument("--freq-mode", choices=["as_configured", "constant", "hopping", "agility"], default="constant")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 16)
    parser.add_argument("--skip-hash-verify", action="store_true")
    args = parser.parse_args()

    error_levels_cfg, profiles_cfg, _ = load_all_configs(args.config_dir)
    pulses_per_sequence = args.context_intervals + args.max_horizon
    radar_types = list(RADAR_TYPES)
    profile_modes = ["fixed", "varying"]
    error_levels = list(ERROR_LEVELS)

    collection: Dict[str, Any] = {
        "schema_version": SCHEMA_V2,
        "dataset_family": NEW_COMPLEX_PRI,
        "status": "building",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "production",
        "dataset_size": f"{args.sequence_count}x{pulses_per_sequence}",
        "context_intervals": args.context_intervals,
        "max_horizon": args.max_horizon,
        "seed": args.seed,
        "profiles": profile_modes,
        "radar_types": radar_types,
        "error_levels": error_levels,
        "expected_conditions": len(profile_modes) * len(radar_types) * len(error_levels),
        "completed_conditions": [],
        "code_sha256": {},
    }
    for relative in (
        "dataset_generator/generate_datasets.py",
        "dataset_generator/consecutive_future.py",
        "dataset_generator/sequence_io.py",
        "synthetic_data_generation/radar_generator.py",
    ):
        collection["code_sha256"][relative] = hashlib.sha256((PROJECT_ROOT / relative).read_bytes()).hexdigest()

    _write_collection_atomic(args.output_dir, collection)

    # Order jobs so heavier varying / high-drop conditions start early (better load balancing).
    error_priority = list(reversed(error_levels))
    profile_priority = ["varying", "fixed"]
    tasks: List[Tuple[Any, ...]] = []
    for elvl in error_priority:
        for pmode in profile_priority:
            for rtype in radar_types:
                tasks.append(
                    (
                        str(args.output_dir),
                        rtype,
                        pmode,
                        elvl,
                        args.sequence_count,
                        pulses_per_sequence,
                        args.seed,
                        error_levels_cfg[elvl],
                        profiles_cfg,
                        args.freq_mode,
                        args.context_intervals,
                        args.max_horizon,
                    )
                )

    print(
        f"[START] Parallel dataset generation: {len(tasks)} conditions "
        f"({args.sequence_count}x{pulses_per_sequence}), workers={args.workers}, root={args.output_dir}",
        flush=True,
    )
    t_start = time.perf_counter()
    completed = 0
    generated_count = 0
    skipped_count = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(_generate_one_condition, t): t for t in tasks}
        for future in as_completed(futures):
            pmode, rtype, elvl, status, elapsed = future.result()
            completed += 1
            if status == "generated":
                generated_count += 1
            else:
                skipped_count += 1
            collection["completed_conditions"].append(f"{pmode}/{rtype}/{elvl}")
            _write_collection_atomic(args.output_dir, collection)
            print(
                f"[{completed:3d}/{len(tasks)}] {status:9s} {pmode}/{rtype}/{elvl} "
                f"({elapsed:.1f}s) | wall={time.perf_counter() - t_start:.1f}s",
                flush=True,
            )

    collection["status"] = "complete"
    collection["completed_utc"] = datetime.now(timezone.utc).isoformat()
    _write_collection_atomic(args.output_dir, collection)

    print(
        f"[COMPLETE] All {completed} conditions ready ({generated_count} generated, {skipped_count} skipped) "
        f"in {time.perf_counter() - t_start:.1f}s.",
        flush=True,
    )

    if not args.skip_hash_verify:
        ref_manifest = (
            PROJECT_ROOT
            / "results"
            / "chronos2"
            / "zero_shot"
            / "new_complex_pri"
            / "run_20261118_151924"
            / "test_windows.json"
        )
        verify_against_reference_manifest(args.output_dir, ref_manifest)


if __name__ == "__main__":
    main()
