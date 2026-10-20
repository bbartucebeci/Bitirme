#!/usr/bin/env python3
"""Unified Dataset Generator CLI for Single-Radar and Interleaved Radar Benchmarks.

Generates reproducible train/val/test datasets with:
- 5 Radar types: stable, jitter, stagger, dwell_and_switch, sliding
- 2 Profile modes: fixed_profile, varying_profile
- 4 Error levels: clean, error_lv1, error_lv2, error_lv3
- Frequency modes: constant, hopping, agility
- Multi-radar interleaved benchmarks with pulse-on-pulse receiver collision filtering
- Standardized metadata.yaml, profiles.csv, combined sequences.csv, and per-sequence CSVs
- Fully configurable via external YAML configs in configs/ (error_levels, radar_profiles, clock_noise)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

# Path resolution
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
SIM_DIR = PROJECT_ROOT / "synthetic_data_generation"
CONFIGS_DIR = PROJECT_ROOT / "configs"

if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from radar_generator import (
    Environment,
    StableRadar,
    JitterRadar,
    StaggerRadar,
    DwellAndSwitchRadar,
    SlidingRadar,
)

RADAR_CLASSES = {
    "stable": StableRadar,
    "jitter": JitterRadar,
    "stagger": StaggerRadar,
    "dwell_and_switch": DwellAndSwitchRadar,
    "sliding": SlidingRadar,
}

OUTPUT_COLUMNS = [
    "Radar_ID", "TOA", "PRI", "Frequency", "PW", "Amplitude", "AOA",
    "Measured_Delta_TOA", "sequence_id", "pulse_index", "radar_type", "error_level"
]


# ---------------------------------------------------------------------------
# Configuration Loader
# ---------------------------------------------------------------------------

def load_all_configs(config_dir: Path) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Loads modular YAML configuration files from config_dir."""
    error_levels_path = config_dir / "error_levels.yaml"
    profiles_path = config_dir / "radar_profiles.yaml"
    clock_noise_path = config_dir / "clock_noise.yaml"

    # 1. Error levels
    if error_levels_path.exists():
        with open(error_levels_path, "r", encoding="utf-8") as f:
            raw_err = yaml.safe_load(f)
            error_levels = {
                k: {param: val for param, val in cfg.items() if param != "description"}
                for k, cfg in raw_err.items()
                if isinstance(cfg, dict)
            }
    else:
        raise FileNotFoundError(f"Missing error levels configuration at {error_levels_path}")

    # 2. Radar profiles
    if profiles_path.exists():
        with open(profiles_path, "r", encoding="utf-8") as f:
            radar_profiles = yaml.safe_load(f)
    else:
        raise FileNotFoundError(f"Missing radar profiles configuration at {profiles_path}")

    # 3. Clock noise
    if clock_noise_path.exists():
        with open(clock_noise_path, "r", encoding="utf-8") as f:
            clock_noise = yaml.safe_load(f)
    else:
        clock_noise = {}

    return error_levels, radar_profiles, clock_noise


# ---------------------------------------------------------------------------
# Receiver Overlap / Collision Helper
# ---------------------------------------------------------------------------

def fix_overlapping_toa(df: pd.DataFrame, sampling_resolution: float = 1.0) -> Tuple[pd.DataFrame, int]:
    """Resolves overlapping pulses arriving within receiver sampling resolution."""
    if df.empty or len(df) < 2:
        return df.copy(), 0

    out = df.sort_values("TOA").copy().reset_index(drop=True)
    total_overlaps = 0

    while True:
        toas = out["TOA"].to_numpy()
        gaps = np.diff(toas)
        flagged = np.where(gaps < sampling_resolution)[0]

        if len(flagged) == 0:
            break

        total_overlaps += len(flagged)
        idx = int(flagged[0])
        left_row = out.iloc[idx].copy()
        right_row = out.iloc[idx + 1].copy()

        # Dominant pulse by amplitude survives
        keep_row = left_row if left_row["Amplitude"] >= right_row["Amplitude"] else right_row

        out.iloc[idx] = keep_row
        out = out.drop(index=idx + 1).reset_index(drop=True)

    out = out.sort_values("TOA").reset_index(drop=True)
    return out, total_overlaps


# ---------------------------------------------------------------------------
# Profile Sampling for Varying-Profile Mode
# ---------------------------------------------------------------------------

def sample_common_profile(
    rng: np.random.Generator,
    profile_id: str,
    sampling_cfg: Dict[str, Any],
    freq_mode_override: str = "as_configured",
) -> Dict[str, Any]:
    common_cfg = sampling_cfg["common"]
    freq_mean = float(rng.uniform(common_cfg["freq_mean_mhz"]["low"], common_cfg["freq_mean_mhz"]["high"]))

    mode = freq_mode_override if freq_mode_override != "as_configured" else common_cfg.get("freq_mode", "constant")

    hopping_cfg = common_cfg.get("freq_hopping", {})
    channel_count = hopping_cfg.get("channel_count", 4)
    step = hopping_cfg.get("step_mhz", 50.0)
    offsets = np.arange(channel_count) - (channel_count - 1) / 2.0
    freq_channels = [float(freq_mean + off * step) for off in offsets]

    return {
        "profile_id": profile_id,
        "mean_pri_us": float(rng.uniform(common_cfg["mean_pri_us"]["low"], common_cfg["mean_pri_us"]["high"])),
        "freq_mean_mhz": freq_mean,
        "freq_mode": mode,
        "freq_hopping_values": freq_channels if mode in ["hopping", "agility"] else [freq_mean],
        "pw_mean_us": float(rng.uniform(common_cfg["pw_mean_us"]["low"], common_cfg["pw_mean_us"]["high"])),
        "amp_mean_dbm": float(rng.uniform(common_cfg["amp_mean_dbm"]["low"], common_cfg["amp_mean_dbm"]["high"])),
        "aoa_mean_deg": float(rng.uniform(common_cfg["aoa_mean_deg"]["low"], common_cfg["aoa_mean_deg"]["high"])),
    }


def sample_radar_profile(
    radar_type: str,
    common: Dict[str, Any],
    rng: np.random.Generator,
    sampling_cfg: Dict[str, Any],
) -> Dict[str, Any]:
    mean_pri = common["mean_pri_us"]
    profile = dict(common)
    r_cfg = sampling_cfg["radar_specific"].get(radar_type, {})

    if radar_type == "stable":
        profile["pri_us"] = mean_pri
        profile["pri_args"] = {"pri": mean_pri}

    elif radar_type == "jitter":
        std_fraction = float(rng.uniform(r_cfg["std_fraction"]["low"], r_cfg["std_fraction"]["high"]))
        pri_jitter_std = std_fraction * mean_pri
        profile["std_fraction"] = std_fraction
        profile["pri_jitter_std_us"] = pri_jitter_std
        profile["pri_args"] = {"pri_mean": mean_pri, "pri_jitter_std": pri_jitter_std}

    elif radar_type == "stagger":
        outer_fraction = float(rng.uniform(r_cfg["outer_fraction"]["low"], r_cfg["outer_fraction"]["high"]))
        inner_fraction = float(rng.uniform(r_cfg["inner_fraction"]["low"], r_cfg["inner_fraction"]["high"]))
        pris = [
            float(mean_pri * (1.0 - outer_fraction)),
            float(mean_pri * (1.0 + inner_fraction)),
            float(mean_pri * (1.0 + outer_fraction)),
        ]
        profile["outer_fraction"] = outer_fraction
        profile["inner_fraction"] = inner_fraction
        profile["stagger_pris_us"] = pris
        profile["pri_args"] = {"stagger_pris": pris}

    elif radar_type == "dwell_and_switch":
        outer_fraction = float(rng.uniform(r_cfg["outer_fraction"]["low"], r_cfg["outer_fraction"]["high"]))
        pulses_per_dwell = int(rng.choice(r_cfg["pulses_per_dwell"]["values"]))
        pris = [
            float(mean_pri * (1.0 - outer_fraction)),
            float(mean_pri * (1.0 + outer_fraction)),
        ]
        profile["outer_fraction"] = outer_fraction
        profile["pulses_per_dwell"] = pulses_per_dwell
        profile["dwell_pris_us"] = pris
        profile["pri_args"] = {"dwell_pris": pris, "pulses_per_dwell": pulses_per_dwell}

    elif radar_type == "sliding":
        span_fraction = float(rng.uniform(r_cfg["span_fraction"]["low"], r_cfg["span_fraction"]["high"]))
        pulses_per_slide = int(rng.choice(r_cfg["pulses_per_slide"]["values"]))
        pri_start = float(mean_pri * (1.0 - span_fraction))
        pri_end = float(mean_pri * (1.0 + span_fraction))
        profile["span_fraction"] = span_fraction
        profile["pulses_per_slide"] = pulses_per_slide
        profile["pri_start_us"] = pri_start
        profile["pri_end_us"] = pri_end
        profile["pri_args"] = {
            "pri_start": pri_start,
            "pri_end": pri_end,
            "pulses_per_slide": pulses_per_slide,
        }
    else:
        raise ValueError(f"Unknown radar type: {radar_type}")

    return profile


def get_fixed_profile(
    radar_type: str,
    fixed_cfg: Dict[str, Any],
    freq_mode_override: str = "as_configured",
) -> Dict[str, Any]:
    common = fixed_cfg["common"]
    mean_pri = float(common["mean_pri_us"])
    freq_mean = float(common["freq_mean_mhz"])
    mode = freq_mode_override if freq_mode_override != "as_configured" else common.get("freq_mode", "constant")
    hopping_vals = [float(f) for f in common.get("freq_hopping_values", [freq_mean])]

    profile = {
        "profile_id": "prof_fixed",
        "mean_pri_us": mean_pri,
        "freq_mean_mhz": freq_mean,
        "freq_mode": mode,
        "freq_hopping_values": hopping_vals if mode in ["hopping", "agility"] else [freq_mean],
        "pw_mean_us": float(common["pw_mean_us"]),
        "amp_mean_dbm": float(common["amp_mean_dbm"]),
        "aoa_mean_deg": float(common["aoa_mean_deg"]),
    }
    r_params = fixed_cfg.get(radar_type, {})
    if radar_type == "stable":
        profile["pri_args"] = {"pri": float(r_params["pri_us"])}
    elif radar_type == "jitter":
        profile["pri_args"] = {"pri_mean": float(r_params["pri_mean_us"]), "pri_jitter_std": float(r_params["pri_jitter_std_us"])}
    elif radar_type == "stagger":
        profile["pri_args"] = {"stagger_pris": [float(p) for p in r_params["stagger_pris_us"]]}
    elif radar_type == "dwell_and_switch":
        profile["pri_args"] = {"dwell_pris": [float(p) for p in r_params["dwell_pris_us"]], "pulses_per_dwell": int(r_params["pulses_per_dwell"])}
    elif radar_type == "sliding":
        profile["pri_args"] = {"pri_start": float(r_params["pri_start_us"]), "pri_end": float(r_params["pri_end_us"]), "pulses_per_slide": int(r_params["pulses_per_slide"])}
    return profile


# ---------------------------------------------------------------------------
# Single Radar Sequence Generator
# ---------------------------------------------------------------------------

def generate_single_radar_sequence(
    radar_type: str,
    profile: Dict[str, Any],
    error_config: Dict[str, Any],
    sequence_id: str,
    error_level: str,
    pulses_per_sequence: int = 128,
) -> pd.DataFrame:
    mean_pri = profile["mean_pri_us"]
    duration = pulses_per_sequence * mean_pri

    radar_cls = RADAR_CLASSES[radar_type]
    radar = radar_cls(
        radar_id="R_SINGLE",
        freq_mean=profile["freq_mean_mhz"],
        freq_mode=profile.get("freq_mode", "constant"),
        freq_hopping_values=profile.get("freq_hopping_values", None),
        pw_mean=profile["pw_mean_us"],
        amp_mean=profile["amp_mean_dbm"],
        aoa_mean=profile["aoa_mean_deg"],
        poi=error_config["poi"],
        multipath_prob=error_config["multipath_prob"],
        aoa_drift_rate=error_config["aoa_drift_rate"],
        **profile["pri_args"],
    )

    env = Environment()
    env.add_radar(radar)

    df = env.generate(
        duration=duration,
        start_time=0.0,
        toa_noise_std=error_config["toa_noise_std"],
        freq_noise_std=error_config["freq_noise_std"],
        pw_noise_std=error_config["pw_noise_std"],
        amp_noise_std=error_config["amp_noise_std"],
        aoa_noise_std=error_config["aoa_noise_std"],
        global_drop_rate=error_config["global_drop_rate"],
        noise_rate=error_config["noise_rate"],
        quantize=error_config["quantize"],
    )

    if df.empty:
        raise ValueError(f"Generated empty sequence for {sequence_id}")

    df = df.sort_values("TOA").reset_index(drop=True)
    df["sequence_id"] = sequence_id
    df["pulse_index"] = np.arange(len(df), dtype=int)
    df["radar_type"] = radar_type
    df["error_level"] = error_level

    cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    return df[cols]


# ---------------------------------------------------------------------------
# Interleaved Radar Sequence Generator
# ---------------------------------------------------------------------------

def generate_interleaved_sequence(
    sequence_id: str,
    error_config: Dict[str, Any],
    error_level: str,
    interleaved_cfg: Dict[str, Any],
    pulses_per_sequence: int = 128,
) -> pd.DataFrame:
    env_cfg = interleaved_cfg["environment"]
    sampling_resolution = env_cfg.get("sampling_resolution", 1.0)
    mean_pri = 1000.0
    duration = pulses_per_sequence * mean_pri

    env = Environment(
        N=env_cfg.get("N", 150.0),
        rain=env_cfg.get("rain", 0.0),
        fog=env_cfg.get("fog", 0.0),
    )

    for r_entry in interleaved_cfg["radars"]:
        rtype = r_entry["type"]
        r_cls = RADAR_CLASSES[rtype]
        r_args = {k: v for k, v in r_entry.items() if k not in ["type", "radar_id"]}
        radar_obj = r_cls(
            radar_id=r_entry["radar_id"],
            poi=error_config["poi"],
            multipath_prob=error_config["multipath_prob"],
            **r_args,
        )
        env.add_radar(radar_obj)

    df = env.generate(
        duration=duration,
        start_time=0.0,
        toa_noise_std=error_config["toa_noise_std"],
        freq_noise_std=error_config["freq_noise_std"],
        pw_noise_std=error_config["pw_noise_std"],
        amp_noise_std=error_config["amp_noise_std"],
        aoa_noise_std=error_config["aoa_noise_std"],
        global_drop_rate=error_config["global_drop_rate"],
        noise_rate=error_config["noise_rate"],
        quantize=error_config["quantize"],
    )

    # Receiver pulse overlap cleanup
    df, _ = fix_overlapping_toa(df, sampling_resolution=sampling_resolution)

    df = df.sort_values("TOA").reset_index(drop=True)
    df["sequence_id"] = sequence_id
    df["pulse_index"] = np.arange(len(df), dtype=int)
    df["radar_type"] = "interleaved"
    df["error_level"] = error_level

    cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    return df[cols]


# ---------------------------------------------------------------------------
# Dataset Writer & Orchestrator
# ---------------------------------------------------------------------------

def write_split(
    split_dir: Path,
    seq_ids: List[str],
    generate_fn,
) -> int:
    split_dir.mkdir(parents=True, exist_ok=True)
    dfs = []
    for seq_id in seq_ids:
        df_seq = generate_fn(seq_id)
        df_seq.to_csv(split_dir / f"{seq_id}.csv", index=False)
        dfs.append(df_seq)

    combined = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    if not combined.empty:
        combined.to_csv(split_dir / "sequences.csv", index=False)
    return len(combined)


def build_single_dataset(
    output_root: Path,
    radar_type: str,
    profile_mode: str,
    error_level: str,
    sequence_count: int,
    pulses_per_sequence: int,
    seed: int,
    error_config: Dict[str, Any],
    profiles_cfg: Dict[str, Any],
    freq_mode: str = "as_configured",
):
    dataset_folder = f"{sequence_count}x{pulses_per_sequence}_{error_level}"
    dataset_name = f"single_{radar_type}_{dataset_folder}"

    dest_dir = output_root / "single_radar" / profile_mode / radar_type / dataset_folder
    dest_dir.mkdir(parents=True, exist_ok=True)

    train_count = int(0.7 * sequence_count)
    val_count = int(0.1 * sequence_count)
    test_count = sequence_count - train_count - val_count

    seq_ids = [f"seq_{i:04d}" for i in range(sequence_count)]
    train_ids = seq_ids[:train_count]
    val_ids = seq_ids[train_count:train_count + val_count]
    test_ids = seq_ids[train_count + val_count:]

    rng_profiles = np.random.default_rng(seed)
    profiles_dict = {}

    if profile_mode == "fixed":
        fixed_prof = get_fixed_profile(radar_type, profiles_cfg["fixed_profiles"], freq_mode_override=freq_mode)
        for sid in seq_ids:
            profiles_dict[sid] = fixed_prof
    else:
        # Sample unique profile per sequence
        sampling_cfg = profiles_cfg["varying_profile_sampling"]
        profiles_rows = []
        for sid in seq_ids:
            common = sample_common_profile(rng_profiles, profile_id=f"prof_{sid}", sampling_cfg=sampling_cfg, freq_mode_override=freq_mode)
            prof = sample_radar_profile(radar_type, common, rng_profiles, sampling_cfg=sampling_cfg)
            profiles_dict[sid] = prof
            prof_row = {k: v for k, v in prof.items() if k != "pri_args"}
            prof_row["pri_arguments_json"] = json.dumps(prof["pri_args"])
            prof_row["sequence_id"] = sid
            profiles_rows.append(prof_row)

        pd.DataFrame(profiles_rows).to_csv(dest_dir / "profiles.csv", index=False)

    def gen_wrapper(sid: str):
        return generate_single_radar_sequence(
            radar_type=radar_type,
            profile=profiles_dict[sid],
            error_config=error_config,
            sequence_id=sid,
            error_level=error_level,
            pulses_per_sequence=pulses_per_sequence,
        )

    train_rows = write_split(dest_dir / "train", train_ids, gen_wrapper)
    val_rows = write_split(dest_dir / "val", val_ids, gen_wrapper)
    test_rows = write_split(dest_dir / "test", test_ids, gen_wrapper)

    metadata = {
        "name": dataset_name,
        "radar_type": radar_type,
        "profile_mode": profile_mode,
        "freq_mode": freq_mode,
        "sequence_count": sequence_count,
        "expected_pulses_per_sequence": pulses_per_sequence,
        "error_level": error_level,
        "error_parameters": error_config,
        "split": {
            "train": {"sequence_count": train_count, "row_count": train_rows},
            "val": {"sequence_count": val_count, "row_count": val_rows},
            "test": {"sequence_count": test_count, "row_count": test_rows},
        },
        "units": {
            "TOA": "microseconds",
            "PRI": "microseconds",
            "Frequency": "MHz",
            "PW": "microseconds",
            "Amplitude": "dBm",
            "AOA": "degrees",
        },
    }

    with (dest_dir / "metadata.yaml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(metadata, f, sort_keys=False)

    print(f"[SUCCESS] Generated: {radar_type}/{dataset_folder} ({train_rows + val_rows + test_rows} total rows)")


def build_interleaved_dataset(
    output_root: Path,
    error_level: str,
    sequence_count: int,
    pulses_per_sequence: int,
    error_config: Dict[str, Any],
    interleaved_cfg: Dict[str, Any],
):
    dataset_name = f"5radars_{sequence_count}x{pulses_per_sequence}_{error_level}"

    dest_dir = output_root / "interleaved" / dataset_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    train_count = int(0.7 * sequence_count)
    val_count = int(0.1 * sequence_count)
    test_count = sequence_count - train_count - val_count

    seq_ids = [f"seq_{i:04d}" for i in range(sequence_count)]
    train_ids = seq_ids[:train_count]
    val_ids = seq_ids[train_count:train_count + val_count]
    test_ids = seq_ids[train_count + val_count:]

    def gen_wrapper(sid: str):
        return generate_interleaved_sequence(
            sequence_id=sid,
            error_config=error_config,
            error_level=error_level,
            interleaved_cfg=interleaved_cfg,
            pulses_per_sequence=pulses_per_sequence,
        )

    train_rows = write_split(dest_dir / "train", train_ids, gen_wrapper)
    val_rows = write_split(dest_dir / "val", val_ids, gen_wrapper)
    test_rows = write_split(dest_dir / "test", test_ids, gen_wrapper)

    metadata = {
        "name": dataset_name,
        "radar_type": "interleaved",
        "radars": [r["radar_id"] for r in interleaved_cfg["radars"]],
        "sequence_count": sequence_count,
        "expected_pulses_per_sequence": pulses_per_sequence,
        "error_level": error_level,
        "error_parameters": error_config,
        "split": {
            "train": {"sequence_count": train_count, "row_count": train_rows},
            "val": {"sequence_count": val_count, "row_count": val_rows},
            "test": {"sequence_count": test_count, "row_count": test_rows},
        },
        "units": {
            "TOA": "microseconds",
            "PRI": "microseconds",
            "Frequency": "MHz",
            "PW": "microseconds",
            "Amplitude": "dBm",
            "AOA": "degrees",
        },
    }

    with (dest_dir / "metadata.yaml").open("w", encoding="utf-8") as f:
        yaml.safe_dump(metadata, f, sort_keys=False)

    print(f"[SUCCESS] Generated: interleaved/{dataset_name} ({train_rows + val_rows + test_rows} total rows)")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="PULSAR Benchmark Dataset Generator")
    parser.add_argument(
        "--radar-type",
        choices=["stable", "jitter", "stagger", "dwell_and_switch", "sliding", "interleaved", "all_single", "all"],
        default="stable",
        help="Type of radar to generate (default: stable)",
    )
    parser.add_argument(
        "--profile-mode",
        choices=["fixed", "varying", "both"],
        default="fixed",
        help="Fixed or varying profile (default: fixed)",
    )
    parser.add_argument(
        "--freq-mode",
        choices=["as_configured", "constant", "hopping", "agility"],
        default="as_configured",
        help="Carrier frequency mode override (default: as_configured)",
    )
    parser.add_argument(
        "--error-level",
        choices=["clean", "error_lv1", "error_lv2", "error_lv3", "all"],
        default="clean",
        help="Error level to simulate (default: clean)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "datasets",
        help="Root directory to output datasets into",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=CONFIGS_DIR,
        help="Directory containing YAML configuration files (default: configs/)",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run a quick smoke test generating 10 sequences instead of 1000",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20261020,
        help="Random seed for reproducibility",
    )

    args = parser.parse_args()

    # Load modular configs
    error_levels_cfg, profiles_cfg, clock_noise_cfg = load_all_configs(args.config_dir)

    sequence_count = 10 if args.smoke_test else 1000
    pulses_per_sequence = 128

    error_levels = list(error_levels_cfg.keys()) if args.error_level == "all" else [args.error_level]
    profile_modes = ["fixed", "varying"] if args.profile_mode == "both" else [args.profile_mode]

    if args.radar_type in ["all", "all_single"]:
        radar_types = list(RADAR_CLASSES.keys())
    elif args.radar_type == "interleaved":
        radar_types = []
    else:
        radar_types = [args.radar_type]

    # Generate single radar benchmarks
    for rtype in radar_types:
        for pmode in profile_modes:
            for elvl in error_levels:
                build_single_dataset(
                    output_root=args.output_dir,
                    radar_type=rtype,
                    profile_mode=pmode,
                    error_level=elvl,
                    sequence_count=sequence_count,
                    pulses_per_sequence=pulses_per_sequence,
                    seed=args.seed,
                    error_config=error_levels_cfg[elvl],
                    profiles_cfg=profiles_cfg,
                    freq_mode=args.freq_mode,
                )

    # Generate interleaved benchmarks
    if args.radar_type in ["interleaved", "all"]:
        for elvl in error_levels:
            build_interleaved_dataset(
                output_root=args.output_dir,
                error_level=elvl,
                sequence_count=sequence_count,
                pulses_per_sequence=pulses_per_sequence,
                error_config=error_levels_cfg[elvl],
                interleaved_cfg=profiles_cfg["interleaved_scenario"],
            )


if __name__ == "__main__":
    main()
