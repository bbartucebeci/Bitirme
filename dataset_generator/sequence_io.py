"""Single-copy sequence storage and explicit forecast-boundary contracts; no torch."""
from pathlib import Path

import numpy as np
import pandas as pd

from dataset_generator.catalog import SCHEMA_V2
SOURCE_COLUMNS = ["source_pulse_id", "poi_keep", "global_keep", "observed_keep", "sequence_index", "segment"]


def read_sequence_frame(path: Path) -> pd.DataFrame:
    """Project the stored source stream into anchor + observed context + full future.

    Ordinary v1 sequence CSVs pass through. Audit-only rows/masks never become
    forecast features. All channels are selected using one shared row index.
    """
    frame = pd.read_csv(path)
    if "sequence_index" not in frame:
        return frame
    if set(SOURCE_COLUMNS) - set(frame):
        raise ValueError(f"{path}: incomplete source-stream schema")
    if not np.array_equal(frame.source_pulse_id.to_numpy(), np.arange(len(frame))):
        raise ValueError(f"{path}: stored source IDs are not consecutive")
    if any(frame[field].dtype!=bool for field in ("poi_keep","global_keep","observed_keep")):
        raise ValueError(f"{path}: loss masks must be boolean")
    if not np.array_equal(frame.observed_keep,frame.poi_keep & frame.global_keep):
        raise ValueError(f"{path}: inconsistent loss masks")
    frame = frame.loc[frame.sequence_index >= 0].sort_values("sequence_index").reset_index(drop=True)
    if not np.array_equal(frame.sequence_index.to_numpy(), np.arange(len(frame))):
        raise ValueError(f"{path}: selected sequence indices are not contiguous")
    if not np.array_equal(frame.pulse_index.to_numpy(), frame.sequence_index.to_numpy()):
        raise ValueError(f"{path}: pulse_index differs from sequence_index")
    contexts=frame.loc[frame.segment.eq("context")]
    future=frame.loc[frame.segment.eq("horizon")]
    if len(contexts)==0 or len(future)==0 or frame.segment.iloc[0]!="anchor":
        raise ValueError(f"{path}: incomplete context/horizon segments")
    expected_segments=["anchor"]+["context"]*len(contexts)+["horizon"]*len(future)
    if frame.segment.tolist()!=expected_segments or not contexts.observed_keep.all():
        raise ValueError(f"{path}: invalid observed context segments")
    ids=contexts.source_pulse_id.iloc[-1]+np.arange(1,len(future)+1)
    if not np.array_equal(future.source_pulse_id,ids):
        raise ValueError(f"{path}: future does not continue the source stream")
    return frame


def is_boundary_dataset(metadata: dict) -> bool:
    return metadata.get("schema_version") == SCHEMA_V2


def boundary_start(metadata: dict, length: int, horizon: int, mode: str) -> int:
    if not is_boundary_dataset(metadata):
        raise ValueError("Explicit boundary mode requires a consecutive_future_v2 dataset")
    if mode != "boundary":
        raise ValueError("consecutive_future_v2 requires --window-mode boundary; first/random/tail can move the target")
    context = int(metadata["context_intervals"])
    if not 0 < length <= context or not 0 < horizon <= int(metadata["max_horizon"]):
        raise ValueError(f"Requested L={length}, H={horizon} exceeds stored context/horizon budgets")
    return context - length


def reject_legacy_window_loader(dataset_dir: Path) -> None:
    """Do not let old first-window evaluators silently score the context as future."""
    import yaml
    metadata_path = Path(dataset_dir)/"metadata.yaml"
    if metadata_path.is_file() and is_boundary_dataset(yaml.safe_load(metadata_path.read_text(encoding="utf-8"))):
        raise ValueError("This legacy first-window loader does not support consecutive_future_v2; use load_split(window_mode='boundary')")
