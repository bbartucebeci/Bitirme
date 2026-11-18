#!/usr/bin/env python3
"""Export Kalman new_complex_pri results to one CSV comparable with Chronos-2 zero-shot metrics.csv.

One row per config x profile x radar_type x error_level x context_len, aggregated the same way
as foundation_models/chronos2/run_zero_shot.py: per-sequence MAE / RMSE / hit rate (|err| <= 10 us
on emitter pulses), then the mean over test sequences. Column names and the profile / radar_type /
error_level spellings match the Chronos-2 metrics.csv.

config values:
  default_max_period_24  the default Kalman bank (level, trend, periodic P = 2..24), all radar types
  max_period_32          stagger only, periodic P = 2..32 (the new stagger has 32 levels)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS = PROJECT_ROOT / "results" / "classic_methods" / "new_complex_pri"
SOURCES = {
    "default_max_period_24": RESULTS / "kalman_filter" / "raw",
    "max_period_32": RESULTS / "kalman_filter_stagger_max_period_32" / "raw",
}
COLUMNS = ["profile", "radar_type", "error_level", "context_len", "num_sequences",
           "mae", "rmse", "hit_rate_pct", "config"]


def build() -> pd.DataFrame:
    frames = []
    for config, raw_dir in SOURCES.items():
        files = sorted(raw_dir.glob("*.csv"))
        if not files:
            raise FileNotFoundError(f"No raw results in {raw_dir}")
        raw = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
        agg = (raw.groupby(["profile", "radar_type", "error_level", "context_len"], as_index=False)
                  .agg(num_sequences=("sequence_id", "size"), mae=("mae_us", "mean"),
                       rmse=("rmse_us", "mean"), hit_rate_pct=("hit_rate_pct", "mean")))
        agg["config"] = config
        frames.append(agg)
    out = pd.concat(frames, ignore_index=True)[COLUMNS]
    if out.duplicated(["config", "profile", "radar_type", "error_level", "context_len"]).any():
        raise ValueError("duplicate condition rows")
    return out.sort_values(["config", "profile", "radar_type", "error_level", "context_len"]).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--output", type=Path, default=RESULTS / "kalman_filter" / "metrics_all.csv")
    args = ap.parse_args()
    out = build()
    out.to_csv(args.output, index=False)
    print(f"{len(out)} rows -> {args.output}")
    print(out.groupby("config").size().to_string())


if __name__ == "__main__":
    main()
