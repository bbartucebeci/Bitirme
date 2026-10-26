"""PULSAR: Centralized benchmark report compiler for Univariate and Multivariate regimes."""

from __future__ import annotations
import argparse
from pathlib import Path
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
RESULTS_ROOT = PROJECT_ROOT / "results" / "timesfm_3.0"

PARAMS = [
    {"slug": "pri", "name": "Pulse Repetition Interval (PRI)", "unit": "us", "tol": "±10 μs"},
    {"slug": "frequency", "name": "Carrier Frequency (RF)", "unit": "MHz", "tol": "±2 MHz"},
    {"slug": "pw", "name": "Pulse Width (PW)", "unit": "us", "tol": "±0.1 μs"},
    {"slug": "aoa", "name": "Angle of Arrival (AOA)", "unit": "deg", "tol": "±2°"},
    {"slug": "amplitude", "name": "Received Peak Power (Amplitude)", "unit": "dBm", "tol": "±2 dBm"},
]


def compile_univariate_summary(profile_mode: str = "fixed") -> Path:
    """Compiles unified 5-parameter report for univariate benchmarking."""
    lines = [
        f"# PULSAR: Comprehensive TimesFM 3.0 Benchmark Summary [Univariate {profile_mode.capitalize()} Profile]",
        f"\n**Compiled on**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"\nEvaluates off-the-shelf Zero-Shot vs. LoRA Fine-Tuned TimesFM 3.0 across all 5 PDW parameters on {profile_mode} profile datasets.",
        "Non-emitter pulses and false alarms are masked out; errors reflect true emitter pulse tracking accuracy.\n",
        "---",
    ]

    for p in PARAMS:
        slug = p["slug"]
        name = p["name"]
        unit = p["unit"]
        tol = p["tol"]

        zs_csv = RESULTS_ROOT / "zero_shot" / f"univariate_{profile_mode}" / slug / "metrics.csv"
        lora_csv = RESULTS_ROOT / "lora_sft" / f"univariate_{profile_mode}" / slug / "metrics.csv"

        lines.append(f"\n## {name} (Gate Tolerance: {tol})\n")

        if not zs_csv.exists():
            lines.append(f"*Zero-Shot metrics not yet available for {name} ({profile_mode}).*\n")
            continue

        df_zs = pd.read_csv(zs_csv)
        mae_col_zs = [c for c in df_zs.columns if c.lower().startswith("mae_")][0]
        hit_col_zs = [c for c in df_zs.columns if "hit_rate" in c.lower()][0]

        if lora_csv.exists():
            df_lora = pd.read_csv(lora_csv)
            mae_col_lora = [c for c in df_lora.columns if c.lower().startswith("mae_")][0]
            hit_col_lora = [c for c in df_lora.columns if "hit_rate" in c.lower()][0]

            merged = pd.merge(df_zs, df_lora, on=["radar_type", "error_level"], suffixes=("_zs", "_lora"))

            lines.append(f"| Radar Type | Error Level | Zero-Shot MAE ({unit}) | LoRA SFT MAE ({unit}) | MAE Δ (%) | Zero-Shot Hit Rate | LoRA Hit Rate | Hit Rate Δ |")
            lines.append("|---|---|---:|---:|---:|---:|---:|---:|")

            for _, row in merged.iterrows():
                zs_mae = row[f"{mae_col_zs}_zs"]
                lora_mae = row[f"{mae_col_lora}_lora"]
                zs_hit = row[f"{hit_col_zs}_zs"]
                lora_hit = row[f"{hit_col_lora}_lora"]

                mae_delta = ((lora_mae - zs_mae) / max(1e-5, zs_mae)) * 100.0
                hit_delta = lora_hit - zs_hit

                mae_display = f"**{lora_mae:.2f}**" if lora_mae < zs_mae else f"{lora_mae:.2f}"
                hit_display = f"**{lora_hit:.1f}%**" if lora_hit > zs_hit else f"{lora_hit:.1f}%"

                lines.append(f"| `{row['radar_type']}` | `{row['error_level']}` | {zs_mae:.2f} | {mae_display} | {mae_delta:+.1f}% | {zs_hit:.1f}% | {hit_display} | {hit_delta:+.1f}% |")
        else:
            lines.append(f"| Radar Type | Error Level | Zero-Shot MAE ({unit}) | Zero-Shot RMSE ({unit}) | Tactical Hit Rate ({tol}) |")
            lines.append("|---|---|---:|---:|---:|")
            rmse_col = [c for c in df_zs.columns if c.lower().startswith("rmse_")][0]
            for _, row in df_zs.iterrows():
                lines.append(f"| `{row['radar_type']}` | `{row['error_level']}` | {row[mae_col_zs]:.2f} | {row[rmse_col]:.2f} | {row[hit_col_zs]:.1f}% |")

    summary_file = RESULTS_ROOT / f"univariate_{profile_mode}_summary.md"
    summary_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[COMPILED] Univariate Summary saved to: {summary_file}")
    return summary_file


def compile_univariate_vs_multivariate_summary(profile_mode: str = "fixed") -> Optional[Path]:
    """Compiles side-by-side comparison of Univariate vs. Multivariate modeling."""
    mv_zs_csv = RESULTS_ROOT / "zero_shot" / f"multivariate_{profile_mode}" / "metrics.csv"
    mv_lora_csv = RESULTS_ROOT / "lora_sft" / f"multivariate_{profile_mode}" / "metrics.csv"

    if not mv_zs_csv.exists() or not mv_lora_csv.exists():
        print(f"[SKIP] Multivariate files not found for profile {profile_mode}")
        return None

    df_mv_lora = pd.read_csv(mv_lora_csv)

    uv_pri_lora_csv = RESULTS_ROOT / "lora_sft" / f"univariate_{profile_mode}" / "pri" / "metrics.csv"
    uv_rf_lora_csv = RESULTS_ROOT / "lora_sft" / f"univariate_{profile_mode}" / "frequency" / "metrics.csv"

    if not uv_pri_lora_csv.exists() or not uv_rf_lora_csv.exists():
        print(f"[SKIP] Univariate files not found for profile {profile_mode}")
        return None

    df_uv_pri = pd.read_csv(uv_pri_lora_csv)
    df_uv_rf = pd.read_csv(uv_rf_lora_csv)

    uv_pri_mae_col = [c for c in df_uv_pri.columns if c.lower().startswith("mae_")][0]
    uv_pri_hit_col = [c for c in df_uv_pri.columns if "hit_rate" in c.lower()][0]
    uv_rf_mae_col = [c for c in df_uv_rf.columns if c.lower().startswith("mae_")][0]

    merged = pd.merge(
        df_uv_pri[["radar_type", "error_level", uv_pri_mae_col, uv_pri_hit_col]].rename(
            columns={uv_pri_mae_col: "uv_pri_mae", uv_pri_hit_col: "uv_pri_hit"}
        ),
        df_mv_lora[["radar_type", "error_level", "mae_pri", "hit_rate_pri", "mae_frequency", "hit_rate_frequency"]].rename(
            columns={"mae_pri": "mv_pri_mae", "hit_rate_pri": "mv_pri_hit", "mae_frequency": "mv_rf_mae", "hit_rate_frequency": "mv_rf_hit"}
        ),
        on=["radar_type", "error_level"],
    )

    merged = pd.merge(
        merged,
        df_uv_rf[["radar_type", "error_level", uv_rf_mae_col]].rename(columns={uv_rf_mae_col: "uv_rf_mae"}),
        on=["radar_type", "error_level"],
    )

    lines = [
        f"# PULSAR: Univariate vs. Joint 5-Channel Multivariate Comparison [{profile_mode.capitalize()} Profile]",
        f"\n**Compiled on**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "\nDirect side-by-side performance comparison between independent univariate LoRA adapters and unified 5-channel multivariate LoRA modeling.\n",
        "---",
        f"\n## LoRA Fine-Tuned: Univariate vs. Joint Multivariate Performance ({profile_mode.capitalize()})\n",
        "| Radar Type | Error Level | UV PRI MAE (μs) | MV PRI MAE (μs) | PRI Δ | UV PRI Hit | MV PRI Hit | UV RF MAE (MHz) | MV RF MAE (MHz) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for _, row in merged.iterrows():
        uv_p = row["uv_pri_mae"]
        mv_p = row["mv_pri_mae"]
        p_delta = ((mv_p - uv_p) / max(1e-5, uv_p)) * 100.0

        p_str = f"**{mv_p:.2f}**" if mv_p < uv_p else f"{mv_p:.2f}"
        uv_p_str = f"**{uv_p:.2f}**" if uv_p < mv_p else f"{uv_p:.2f}"

        lines.append(
            f"| `{row['radar_type']}` | `{row['error_level']}` | "
            f"{uv_p_str} | {p_str} | {p_delta:+.1f}% | "
            f"{row['uv_pri_hit']:.1f}% | {row['mv_pri_hit']:.1f}% | "
            f"{row['uv_rf_mae']:.2f} | {row['mv_rf_mae']:.2f} |"
        )

    summary_file = RESULTS_ROOT / f"univariate_vs_multivariate_{profile_mode}_summary.md"
    summary_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SAVED] Univariate vs Multivariate Summary saved to: {summary_file}")
    return summary_file


def main():
    parser = argparse.ArgumentParser(description="PULSAR: Compile Master Benchmark Summaries")
    parser.add_argument("--profile-mode", choices=["fixed", "varying", "both"], default="fixed")
    args = parser.parse_args()

    modes = ["fixed", "varying"] if args.profile_mode == "both" else [args.profile_mode]
    for mode in modes:
        compile_univariate_summary(mode)
        compile_univariate_vs_multivariate_summary(mode)


if __name__ == "__main__":
    main()

