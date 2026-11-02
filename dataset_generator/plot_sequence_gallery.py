"""Plot 40 independent single-radar test sequences across the benchmark matrix.

Each of the five measured parameters gets one fixed-profile and one
varying-profile figure. The dataset CSVs are read without modification.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RADAR_TYPES = ("stable", "jitter", "stagger", "dwell_and_switch", "sliding")
ERROR_LEVELS = ("clean", "error_lv1", "error_lv2", "error_lv3")
PROFILES = ("fixed", "varying")
CHANNELS = (
    ("PRI", "Measured_Delta_TOA", "Interval (µs)"),
    ("Frequency", "Frequency", "Frequency (MHz)"),
    ("PW", "PW", "Pulse width (µs)"),
    ("Amplitude", "Amplitude", "Amplitude (dBm)"),
    ("AOA", "AOA", "AOA (degrees)"),
)
MIN_AXIS_SPAN = {"PRI": 10.0, "Frequency": 2.0, "PW": 0.05, "Amplitude": 1.0, "AOA": 2.0}


def load_sequence(path: Path, pulse_count: int) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path).sort_values("pulse_index").reset_index(drop=True)
    required = {"Radar_ID", "PRI", "Measured_Delta_TOA", "pulse_index", *(item[1] for item in CHANNELS)}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    # Match the forecasting loader's treatment of the 129-row captures.
    if len(frame) == 129 and float(frame.loc[0, "Measured_Delta_TOA"]) == 0.0:
        frame = frame.iloc[1:].reset_index(drop=True)
    if len(frame) < pulse_count:
        raise ValueError(f"{path}: only {len(frame)} observed pulses after anchor removal")
    return frame.iloc[:pulse_count].copy()


def plot_profile(
    profile: str,
    channel: str,
    value_column: str,
    unit_label: str,
    selected: dict[tuple[str, str, str], tuple[str, pd.DataFrame]],
    output_dir: Path,
    dpi: int,
) -> Path:
    fig, axes = plt.subplots(4, 5, figsize=(18, 11.2), sharex=True)
    for row, level in enumerate(ERROR_LEVELS):
        for col, radar in enumerate(RADAR_TYPES):
            axis = axes[row, col]
            sequence_id, frame = selected[(profile, radar, level)]
            x = np.arange(1, len(frame) + 1)
            genuine = frame["Radar_ID"].eq("R_SINGLE").to_numpy()
            values = frame[value_column].to_numpy(dtype=float)
            axis.plot(x, values, color="#1775a5", linewidth=1.15, marker=".", markersize=2.2)
            if channel == "PRI":
                source_pri = frame["PRI"].to_numpy(dtype=float)
                axis.plot(
                    x, np.where(genuine, source_pri, np.nan),
                    color="#e27929", linewidth=1.1, linestyle="--",
                )
            if (~genuine).any():
                axis.scatter(
                    x[~genuine], values[~genuine], color="#b51f37",
                    marker="x", s=18, linewidth=1.2, zorder=3,
                )
            lower = float(np.nanmin(values))
            upper = float(np.nanmax(values))
            if not np.isfinite((lower, upper)).all():
                raise ValueError(f"{profile}/{radar}/{level}/{channel}: non-finite plotted range")
            if upper - lower < MIN_AXIS_SPAN[channel]:
                center = (lower + upper) / 2
                half_span = MIN_AXIS_SPAN[channel] / 2
                axis.set_ylim(center - half_span, center + half_span)
            axis.ticklabel_format(axis="y", style="plain", useOffset=False)
            axis.yaxis.set_major_locator(MaxNLocator(nbins=4))
            axis.text(
                0.03, 0.95, sequence_id, transform=axis.transAxes,
                ha="left", va="top", fontsize=7,
                bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none", "pad": 1.5},
            )
            axis.grid(alpha=0.18)
            axis.tick_params(labelsize=7)
            if row == 0:
                axis.set_title(radar.replace("_", " "), fontsize=10)
            if col == 0:
                axis.set_ylabel(f"{level}\n{unit_label}", fontsize=8)
            if row == len(ERROR_LEVELS) - 1:
                axis.set_xlabel("Observed pulse position", fontsize=8)

    observed_label = "Observed ΔTOA" if channel == "PRI" else f"Recorded {channel}"
    handles = [Line2D([0], [0], color="#1775a5", linewidth=1.5, label=observed_label)]
    if channel == "PRI":
        handles.append(Line2D([0], [0], color="#e27929", linestyle="--", label="Source PRI (genuine pulses)"))
    handles.append(Line2D([0], [0], color="#b51f37", marker="x", linestyle="None", label="Non-emitter pulse"))
    fig.suptitle(f"{profile.title()} profile · {channel} · 20 distinct test sequences", fontsize=16, y=0.99)
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.965), ncol=len(handles), frameon=False)
    fig.text(0.5, 0.92, "Each panel has its own vertical scale; the initial timing anchor is excluded.",
             ha="center", fontsize=9)
    fig.subplots_adjust(left=0.075, right=0.99, top=0.865, bottom=0.07, hspace=0.35, wspace=0.31)
    output_path = output_dir / f"{profile}_{channel.lower()}.png"
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-size", default="1000x128")
    parser.add_argument("--first-test-id", type=int, default=800)
    parser.add_argument("--pulses", type=int, default=128)
    parser.add_argument("--dpi", type=int, default=160)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "results" / "dataset_gallery")
    args = parser.parse_args()
    if args.first_test_id < 0 or args.pulses <= 0 or args.dpi <= 0:
        parser.error("first test ID must be nonnegative; pulses and dpi must be positive")

    selected: dict[tuple[str, str, str], tuple[str, pd.DataFrame]] = {}
    manifest = []
    for profile in PROFILES:
        for level in ERROR_LEVELS:
            for radar in RADAR_TYPES:
                sequence_id = f"seq_{args.first_test_id + len(manifest):04d}"
                relative_path = (
                    Path("datasets") / "single_radar" / profile / radar
                    / f"{args.dataset_size}_{level}" / "test" / f"{sequence_id}.csv"
                )
                frame = load_sequence(PROJECT_ROOT / relative_path, args.pulses)
                selected[(profile, radar, level)] = (sequence_id, frame)
                manifest.append({
                    "profile": profile,
                    "radar_type": radar,
                    "error_level": level,
                    "sequence_id": sequence_id,
                    "source_csv": relative_path.as_posix(),
                    "plotted_pulses": len(frame),
                    "genuine_pulses": int(frame["Radar_ID"].eq("R_SINGLE").sum()),
                    "non_emitter_pulses": int(frame["Radar_ID"].ne("R_SINGLE").sum()),
                })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for profile in PROFILES:
        for channel, value_column, unit_label in CHANNELS:
            path = plot_profile(profile, channel, value_column, unit_label, selected, args.output_dir, args.dpi)
            print(f"[SAVED] {path}")
    manifest_path = args.output_dir / "selection.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[SAVED] {manifest_path} ({len(manifest)} distinct sequences)")


if __name__ == "__main__":
    main()
