"""Single-radar observed history with a consecutive transmitted-pulse future."""
from __future__ import annotations

import numpy as np
import pandas as pd

from dataset_generator.sequence_io import SOURCE_COLUMNS


def assemble_source_stream(source: pd.DataFrame, poi_keep, global_keep,
                           context_intervals: int, max_horizon: int) -> pd.DataFrame:
    """Keep each PDW once. sequence_index projects the model-facing sequence."""
    if min(context_intervals, max_horizon) <= 0:
        raise ValueError("Context and horizon must be positive")
    source = source.reset_index(drop=True)
    if not np.array_equal(source.source_pulse_id, np.arange(len(source))):
        raise ValueError("Complete source IDs must be consecutive before assembly")
    poi_keep, global_keep = np.asarray(poi_keep, dtype=bool), np.asarray(global_keep, dtype=bool)
    if poi_keep.shape != (len(source),) or global_keep.shape != (len(source),):
        raise ValueError("Loss masks must select whole source rows")
    observed = poi_keep & global_keep
    retained = np.flatnonzero(observed)[:context_intervals+1]
    if len(retained) != context_intervals+1:
        raise ValueError("Insufficient observed context pulses")
    boundary = int(retained[-1])
    if boundary+max_horizon >= len(source):
        raise ValueError("Insufficient consecutive source future")
    end = boundary+max_horizon+1
    output = source.iloc[:end].copy()
    selected = np.r_[retained, np.arange(boundary+1, end)]
    output["poi_keep"] = poi_keep[:end]
    output["global_keep"] = global_keep[:end]
    output["observed_keep"] = observed[:end]
    output["sequence_index"] = -1
    output["segment"] = "missed_context"
    output.loc[selected, "sequence_index"] = np.arange(len(selected))
    output.loc[retained, "segment"] = "context"
    output.loc[retained[0], "segment"] = "anchor"
    output.loc[boundary+1:, "segment"] = "horizon"
    output["pulse_index"] = output.sequence_index
    # Only selected rows are observed intervals. Audit rows retain source deltas.
    output["Measured_Delta_TOA"] = output.TOA.diff().fillna(0.)
    output.loc[selected, "Measured_Delta_TOA"] = np.r_[0., np.diff(output.loc[selected, "TOA"])]
    return output


def generate_consecutive_sequence(radar_type, profile, error_config, sequence_id,
                                  error_level, context_intervals, max_horizon, loss_seed):
    # Import lazily: the existing CLI imports this optional protocol.
    from dataset_generator.generate_datasets import (
        RADAR_CLASSES, Environment, OUTPUT_COLUMNS, validate_profile, sample_initialization,
    )
    if error_config["noise_rate"] != 0 or error_config["multipath_prob"] != 0:
        raise ValueError("Consecutive-source protocol requires no false pulses or echoes")
    if not 0 < error_config["poi"] <= 1 or not 0 <= error_config["global_drop_rate"] < 1:
        raise ValueError("Context retention probability must be positive")
    validate_profile(radar_type, profile)
    initialization = sample_initialization(radar_type, profile)
    radar = RADAR_CLASSES[radar_type](
        radar_id="R_SINGLE", freq_mean=profile["freq_mean_mhz"], freq_mode=profile["freq_mode"],
        freq_hopping_values=profile.get("freq_hopping_values"), pw_mean=profile["pw_mean_us"],
        amp_mean=profile["amp_mean_dbm"], aoa_mean=profile["aoa_mean_deg"],
        poi=1., multipath_prob=0., aoa_drift_rate=error_config["aoa_drift_rate"],
        track_source_ids=True, **profile["pri_args"], **initialization,
    )
    environment = Environment(); environment.add_radar(radar)
    retention = error_config["poi"]*(1-error_config["global_drop_rate"])
    budget = int(np.ceil(1.5*(context_intervals+1)/retention))+max_horizon+10
    capture_state = np.random.get_state()
    for attempt in range(4):
        np.random.set_state(capture_state)
        source = environment.generate(
            duration=budget*profile["mean_pri_us"], start_time=0.,
            **{name:error_config[name] for name in ("toa_noise_std","freq_noise_std","pw_noise_std","amp_noise_std","aoa_noise_std","quantize")},
            global_drop_rate=0., noise_rate=0.,
        )
        if not np.array_equal(source.source_pulse_id.to_numpy(), np.arange(len(source))):
            raise ValueError("Receiver removed/reordered a source pulse in the complete capture")
        # A dedicated stream prevents measurement draws from consuming loss draws.
        draws = np.random.default_rng(loss_seed).random((len(source), 2))
        poi_keep = draws[:,0] < error_config["poi"]
        global_keep = draws[:,1] >= error_config["global_drop_rate"]
        observed = np.flatnonzero(poi_keep & global_keep)
        if len(observed) >= context_intervals+1 and observed[context_intervals]+max_horizon < len(source):
            result = assemble_source_stream(source, poi_keep, global_keep, context_intervals, max_horizon)
            break
        budget *= 2
    else:
        raise ValueError(f"Insufficient source buffer for {sequence_id}")
    result["sequence_id"] = sequence_id
    result["radar_type"] = radar_type
    result["error_level"] = error_level
    result = result[OUTPUT_COLUMNS+SOURCE_COLUMNS]
    result.attrs.update(initialization=initialization, loss_seed=int(loss_seed),
                        capture_budget=budget, capture_attempts=attempt+1,
                        model_row_count=context_intervals+max_horizon+1)
    return result
