#!/usr/bin/env python3
"""Unified Dataset Generator CLI for Single-Radar and Interleaved Radar Benchmarks.

Generates reproducible train/val/test datasets with:
- 8 PRI types, including sinusoidal, triangular sliding and Markov agile
- 2 Profile modes: fixed_profile, varying_profile
- 8 Error levels: clean and error_lv1 through error_lv7, without false pulses/echoes
- Frequency modes: constant, hopping, agility
- Multi-radar interleaved benchmarks with pulse-on-pulse receiver collision filtering
- metadata.yaml, varying profiles.csv, per-sequence generation.csv, and PDW CSVs
- Fully configurable via external YAML configs in configs/ (error_levels, radar_profiles, clock_noise)
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import zlib
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
    SinusoidalRadar,
    TriangularSlidingRadar,
    MarkovAgileRadar,
)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from dataset_generator.catalog import COMPLEX_DATASETS_ROOT, RADAR_TYPES, ERROR_LEVELS, sinusoidal_repeat_period

RADAR_CLASSES = {
    "stable": StableRadar,
    "jitter": JitterRadar,
    "stagger": StaggerRadar,
    "dwell_and_switch": DwellAndSwitchRadar,
    "sliding": SlidingRadar,
    "sinusoidal": SinusoidalRadar,
    "triangular_sliding": TriangularSlidingRadar,
    "markov_agile": MarkovAgileRadar,
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

    if tuple(error_levels) != ERROR_LEVELS:
        raise ValueError(f"Expected error levels in order {ERROR_LEVELS}")
    for name, cfg in error_levels.items():
        if not 0 <= cfg["poi"] <= 1 or not 0 <= cfg["global_drop_rate"] <= 1:
            raise ValueError(f"{name}: invalid loss probability")
        if cfg["noise_rate"] != 0 or cfg["multipath_prob"] != 0:
            raise ValueError(f"{name}: complex PRI datasets require no false pulses or multipath")
        for key in ("toa_noise_std", "freq_noise_std", "pw_noise_std", "amp_noise_std", "aoa_noise_std"):
            if not np.isfinite(cfg[key]) or cfg[key] < 0:
                raise ValueError(f"{name}: invalid {key}")
    # Validate both fixed definitions and the shape of sampled profiles before writing.
    for kind in RADAR_TYPES:
        validate_profile(kind, get_fixed_profile(kind, radar_profiles["fixed_profiles"]))
        rng = np.random.default_rng(0)
        sampling = radar_profiles["varying_profile_sampling"]
        common = sample_common_profile(rng, "validation", sampling)
        validate_profile(kind, sample_radar_profile(kind, common, rng, sampling))
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
        count = int(rng.integers(r_cfg["level_count"]["low"], r_cfg["level_count"]["high"] + 1))
        span = float(rng.uniform(r_cfg["span_fraction"]["low"], r_cfg["span_fraction"]["high"]))
        order = rng.permutation(count).tolist()
        levels = np.linspace(mean_pri * (1 - span), mean_pri * (1 + span), count)
        pris = levels[order].tolist()
        profile.update(level_count=count, span_fraction=span, level_order=order)
        profile["stagger_pris_us"] = pris
        profile["pri_args"] = {"stagger_pris": pris}

    elif radar_type == "dwell_and_switch":
        outer_fraction = float(rng.uniform(r_cfg["outer_fraction"]["low"], r_cfg["outer_fraction"]["high"]))
        pulses_per_dwell = int(rng.choice(r_cfg["pulses_per_dwell"]["values"]))
        pris = (mean_pri * np.array([1 - outer_fraction, 1 + outer_fraction / 2,
                                   1 - outer_fraction / 2, 1 + outer_fraction, 1])).tolist()
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
    elif radar_type in ("sinusoidal", "triangular_sliding", "markov_agile"):
        span = float(rng.uniform(r_cfg["span_fraction"]["low"], r_cfg["span_fraction"]["high"]))
        profile["span_fraction"] = span
        if radar_type == "sinusoidal":
            period_cfg = r_cfg["period_pulses"]
            for _ in range(10000):
                period = float(rng.uniform(period_cfg["low"], period_cfg["high"]))
                if sinusoidal_repeat_period(period) >= r_cfg["minimum_repeat_period"]:
                    break
            else:
                raise ValueError("Cannot sample a sinusoidal period without a short exact repeat")
            profile["pri_args"] = {"pri_mean": mean_pri, "amplitude": mean_pri * span, "period": period}
        elif radar_type == "triangular_sliding":
            profile["pri_args"] = {"pri_min": mean_pri * (1 - span), "pri_max": mean_pri * (1 + span),
                                   "steps_per_leg": int(r_cfg["steps_per_leg"])}
        else:
            profile["pri_args"] = {"pri_levels": (mean_pri * np.array([1-span, 1-span/3, 1+span/3, 1+span])).tolist(),
                                   "transition_matrix": [[float(x) for x in row] for row in r_cfg["transition_matrix"]]}
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
        count, order = int(r_params["level_count"]), r_params["level_order"]
        if sorted(order) != list(range(count)):
            raise ValueError("Fixed stagger order must contain each level index exactly once")
        levels = np.linspace(r_params["pri_min_us"], r_params["pri_max_us"], count)
        profile.update(level_count=count, level_order=order)
        profile["pri_args"] = {"stagger_pris": levels[order].tolist()}
    elif radar_type == "dwell_and_switch":
        profile["pri_args"] = {"dwell_pris": [float(p) for p in r_params["dwell_pris_us"]], "pulses_per_dwell": int(r_params["pulses_per_dwell"])}
    elif radar_type == "sliding":
        profile["pri_args"] = {"pri_start": float(r_params["pri_start_us"]), "pri_end": float(r_params["pri_end_us"]), "pulses_per_slide": int(r_params["pulses_per_slide"])}
    elif radar_type == "sinusoidal":
        profile["pri_args"] = {"pri_mean": float(r_params["pri_mean_us"]), "amplitude": float(r_params["amplitude_us"]),
                               "period": float(r_params["period_pulses"])}
    elif radar_type == "triangular_sliding":
        profile["pri_args"] = {"pri_min": float(r_params["pri_min_us"]), "pri_max": float(r_params["pri_max_us"]),
                               "steps_per_leg": int(r_params["steps_per_leg"])}
    elif radar_type == "markov_agile":
        profile["pri_args"] = {"pri_levels": [float(x) for x in r_params["pri_levels_us"]],
                               "transition_matrix": [[float(x) for x in row] for row in r_params["transition_matrix"]]}
    else:
        raise ValueError(f"Unknown radar type: {radar_type}")
    return profile


def validate_profile(radar_type: str, profile: Dict[str, Any]) -> None:
    """Check the agreed source-law invariants before simulation or file writes."""
    args = profile["pri_args"]
    if not np.isfinite(profile["mean_pri_us"]) or profile["mean_pri_us"] <= 0:
        raise ValueError("PRI center must be positive and finite")
    if radar_type == "stagger":
        values = args["stagger_pris"]
        if not 16 <= len(values) <= 32 or len(set(values)) != len(values):
            raise ValueError("Stagger requires 16–32 distinct levels")
        # Check source-level separation before clock and measurement effects.
        if np.min(np.diff(np.sort(values))) <= 10.0:
            raise ValueError("Stagger source levels must be separated by more than 10 us")
    elif radar_type == "dwell_and_switch":
        values = args["dwell_pris"]
        if len(values) != 5 or len(set(values)) != 5 or args["pulses_per_dwell"] < 32:
            raise ValueError("D&S requires five distinct levels and dwell >=32")
    elif radar_type == "sinusoidal":
        values = [args["pri_mean"] - args["amplitude"]]
        if args["amplitude"] <= 0 or sinusoidal_repeat_period(args["period"]) <= 1024:
            raise ValueError("Invalid sinusoidal amplitude or short repeat period")
    elif radar_type == "triangular_sliding":
        values = [args["pri_min"], args["pri_max"]]
        if args["steps_per_leg"] != 10 or values[0] >= values[1]:
            raise ValueError("Triangle requires ordered bounds and 10 steps per leg")
    elif radar_type == "markov_agile":
        values = args["pri_levels"]
        probabilities = np.asarray(args["transition_matrix"], dtype=float)
        if (len(values) != 4 or len(set(values)) != 4 or probabilities.shape != (4, 4) or
                not np.isfinite(probabilities).all() or (probabilities < 0).any() or
                not np.allclose(probabilities.sum(axis=1), 1, rtol=0, atol=1e-12) or
                not np.allclose(probabilities.sum(axis=0), 1, rtol=0, atol=1e-12)):
            raise ValueError("Invalid Markov levels or probabilities")
    elif radar_type == "sliding":
        values = [args["pri_start"], args["pri_end"]]
        if args["pulses_per_slide"] < 2:
            raise ValueError("Sliding requires at least two values")
    else:
        values = [args.get("pri", args.get("pri_mean"))]
        if radar_type == "jitter" and (not np.isfinite(args["pri_jitter_std"]) or args["pri_jitter_std"] < 0):
            raise ValueError("Jitter standard deviation must be finite and nonnegative")
    if not np.isfinite(values).all() or np.min(values) <= 0:
        raise ValueError(f"{radar_type}: source PRI must be positive and finite")
    source_center = args["pri_mean"] if radar_type == "sinusoidal" else float(np.mean(values))
    if not np.isclose(source_center, profile["mean_pri_us"], rtol=1e-12, atol=1e-9):
        raise ValueError(f"{radar_type}: source law center differs from profile PRI center")


def sample_initialization(radar_type: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    args = profile["pri_args"]
    if radar_type == "stagger":
        return {"pattern_phase": int(np.random.randint(len(args["stagger_pris"])))}
    if radar_type == "dwell_and_switch":
        return {"pattern_phase": int(np.random.randint(len(args["dwell_pris"]) * args["pulses_per_dwell"]))}
    if radar_type == "sliding":
        return {"pattern_phase": int(np.random.randint(args["pulses_per_slide"]))}
    if radar_type == "triangular_sliding":
        return {"pattern_phase": int(np.random.randint(2 * args["steps_per_leg"]))}
    if radar_type == "sinusoidal":
        return {"phase_rad": float(np.random.uniform(0, 2 * np.pi))}
    if radar_type == "markov_agile":
        return {"initial_state": int(np.random.randint(len(args["pri_levels"]))),
                "source_seed": int(np.random.randint(0, 2**32, dtype=np.uint32))}
    return {}


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
    # Save one anchor plus exactly N observed intervals, even when pulses are lost.
    target_rows = pulses_per_sequence + 1
    mean_pri = profile["mean_pri_us"]

    validate_profile(radar_type, profile)
    initialization = sample_initialization(radar_type, profile)

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
        **initialization,
    )

    env = Environment()
    env.add_radar(radar)

    # The TimesFM benchmark first simulates with a margin, then extends the
    # capture if necessary. A final check prevents saving a short sequence.
    sim_pulses = int(np.ceil(target_rows * 1.5)) + 10
    for _ in range(4):
        df = env.generate(
            duration=sim_pulses * mean_pri,
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
        if len(df) >= target_rows:
            break
        sim_pulses = max(sim_pulses * 2, target_rows * 3)
    else:
        raise ValueError(f"Generated only {len(df)} of {target_rows} observed pulses for {sequence_id}")

    df = df.sort_values("TOA").iloc[:target_rows].copy().reset_index(drop=True)
    df["sequence_id"] = sequence_id
    df["pulse_index"] = np.arange(len(df), dtype=int)
    df["radar_type"] = radar_type
    df["error_level"] = error_level
    df["Measured_Delta_TOA"] = df["TOA"].diff().fillna(0.0)

    cols = [c for c in OUTPUT_COLUMNS if c in df.columns]
    result = df[cols]
    result.attrs["initialization"] = initialization
    return result


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
    if dest_dir.exists() and any(dest_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite an existing dataset: {dest_dir}")
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

    generation_rows = []
    def gen_wrapper(sid: str):
        # Seed the global RNG per sequence: all pulse-level randomness in radar_generator
        # (jitter, start offset, missed/false pulses, multipath, TOA noise) uses np.random.
        key = f"{seed}|{radar_type}|{profile_mode}|{error_level}|{pulses_per_sequence}|{sid}"
        sequence_seed = zlib.crc32(key.encode("utf-8"))
        np.random.seed(sequence_seed)
        result = generate_single_radar_sequence(
            radar_type=radar_type,
            profile=profiles_dict[sid],
            error_config=error_config,
            sequence_id=sid,
            error_level=error_level,
            pulses_per_sequence=pulses_per_sequence,
        )
        generation_rows.append({"sequence_id": sid, "sequence_seed": sequence_seed,
                                "initialization_json": json.dumps(result.attrs["initialization"], sort_keys=True)})
        return result

    train_rows = write_split(dest_dir / "train", train_ids, gen_wrapper)
    val_rows = write_split(dest_dir / "val", val_ids, gen_wrapper)
    test_rows = write_split(dest_dir / "test", test_ids, gen_wrapper)
    pd.DataFrame(generation_rows).to_csv(dest_dir / "generation.csv", index=False)

    metadata = {
        "name": dataset_name,
        "radar_type": radar_type,
        "profile_mode": profile_mode,
        "freq_mode": freq_mode,
        "effective_freq_mode": next(iter(profiles_dict.values()))["freq_mode"],
        "seed": seed,
        "schema_version": "complex_pri_v1",
        "profile_definition": profiles_cfg["fixed_profiles"] if profile_mode == "fixed" else profiles_cfg["varying_profile_sampling"],
        "profile_config_sha256": hashlib.sha256(json.dumps(profiles_cfg, sort_keys=True).encode()).hexdigest(),
        "fixed_profile": fixed_prof if profile_mode == "fixed" else None,
        "sequence_count": sequence_count,
        "expected_pulses_per_sequence": pulses_per_sequence,
        "observed_rows_per_sequence": pulses_per_sequence + 1,
        "first_row_is_anchor": True,
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
        choices=[*RADAR_TYPES, "interleaved", "all_single", "all"],
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
        choices=[*ERROR_LEVELS, "all"],
        default="clean",
        help="Error level to simulate (default: clean)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=COMPLEX_DATASETS_ROOT,
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
    parser.add_argument(
    "--pulses-per-sequence",
    type=int,
    choices=[128, 256, 512, 1024],
    default=128,
    )
    args = parser.parse_args()

    # Load modular configs
    error_levels_cfg, profiles_cfg, clock_noise_cfg = load_all_configs(args.config_dir)

    sequence_count = 10 if args.smoke_test else 1000
    pulses_per_sequence = args.pulses_per_sequence

    error_levels = list(error_levels_cfg.keys()) if args.error_level == "all" else [args.error_level]
    profile_modes = ["fixed", "varying"] if args.profile_mode == "both" else [args.profile_mode]

    if args.radar_type in ["all", "all_single"]:
        radar_types = list(RADAR_CLASSES.keys())
    elif args.radar_type == "interleaved":
        radar_types = []
    else:
        radar_types = [args.radar_type]

    # Preflight all destinations before writing any combination.
    for rtype in radar_types:
        for pmode in profile_modes:
            for elvl in error_levels:
                destination = args.output_dir / "single_radar" / pmode / rtype / f"{sequence_count}x{pulses_per_sequence}_{elvl}"
                if destination.exists() and any(destination.iterdir()):
                    parser.error(f"Output already contains data: {destination}")

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
