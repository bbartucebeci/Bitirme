"""PULSAR: Compile Master Benchmark Summary across all 5 PDW parameters."""

from pathlib import Path
import pandas as pd
import numpy as np
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_ROOT = PROJECT_ROOT / "results" / "timesfm_3.0"

PARAMS = [
    {"slug": "pri", "name": "Pulse Repetition Interval (PRI)", "unit": "us", "tol": "±10 μs"},
    {"slug": "frequency", "name": "Carrier Frequency (RF)", "unit": "MHz", "tol": "±2 MHz"},
    {"slug": "pw", "name": "Pulse Width (PW)", "unit": "us", "tol": "±0.1 μs"},
    {"slug": "aoa", "name": "Angle of Arrival (AOA)", "unit": "deg", "tol": "±2°"},
    {"slug": "amplitude", "name": "Received Peak Power (Amplitude)", "unit": "dBm", "tol": "±2 dBm"},
]

def compile_summary():
    lines = [
        "# PULSAR: Comprehensive TimesFM 3.0 Benchmark Summary (Univariate Fixed Profile)",
        f"\n**Compiled on**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "\nThis report provides an end-to-end performance assessment of Google TimesFM 3.0 across all 5 Pulse Description Word (PDW) parameters.",
        "Crucially, **receiver noise pulses, false alarms, and missing gaps are filtered out**, evaluating model predictions strictly against ground-truth emitter pulses.\n",
        "---",
    ]

    for p in PARAMS:
        slug = p["slug"]
        name = p["name"]
        unit = p["unit"]
        tol = p["tol"]

        zs_csv = RESULTS_ROOT / "zero_shot" / "univariate_fixed" / slug / "metrics.csv"
        lora_csv = RESULTS_ROOT / "lora_sft" / "univariate_fixed" / slug / "metrics.csv"

        lines.append(f"\n## {name} (Gate Tolerance: {tol})\n")

        if not zs_csv.exists():
            lines.append(f"*Zero-Shot metrics not yet available for {name}.*\n")
            continue

        df_zs = pd.read_csv(zs_csv)
        mae_col_zs = f"mae_{unit}" if f"mae_{unit}" in df_zs.columns else [c for c in df_zs.columns if c.startswith("mae_")][0]

        if lora_csv.exists():
            df_lora = pd.read_csv(lora_csv)
            mae_col_lora = f"mae_{unit}" if f"mae_{unit}" in df_lora.columns else [c for c in df_lora.columns if c.startswith("mae_")][0]

            merged = pd.merge(df_zs, df_lora, on=["radar_type", "error_level"], suffixes=("_zs", "_lora"))

            lines.append(f"| Radar Type | Error Level | Zero-Shot MAE ({unit}) | LoRA SFT MAE ({unit}) | MAE Δ (%) | Zero-Shot Hit Rate | LoRA Hit Rate | Hit Rate Δ |")
            lines.append("|---|---|---:|---:|---:|---:|---:|---:|")

            for _, row in merged.iterrows():
                zs_mae = row[f"{mae_col_zs}_zs"]
                lora_mae = row[f"{mae_col_lora}_lora"]
                zs_hit = row["gate_hit_rate_pct_zs"]
                lora_hit = row["gate_hit_rate_pct_lora"]

                mae_delta = ((lora_mae - zs_mae) / max(1e-5, zs_mae)) * 100.0
                hit_delta = lora_hit - zs_hit

                mae_display = f"**{lora_mae:.2f}**" if lora_mae < zs_mae else f"{lora_mae:.2f}"
                hit_display = f"**{lora_hit:.1f}%**" if lora_hit > zs_hit else f"{lora_hit:.1f}%"

                lines.append(f"| `{row['radar_type']}` | `{row['error_level']}` | {zs_mae:.2f} | {mae_display} | {mae_delta:+.1f}% | {zs_hit:.1f}% | {hit_display} | {hit_delta:+.1f}% |")
        else:
            lines.append(f"| Radar Type | Error Level | Zero-Shot MAE ({unit}) | Zero-Shot RMSE ({unit}) | Tactical Hit Rate ({tol}) |")
            lines.append("|---|---|---:|---:|---:|")
            rmse_col = f"rmse_{unit}" if f"rmse_{unit}" in df_zs.columns else [c for c in df_zs.columns if c.startswith("rmse_")][0]
            for _, row in df_zs.iterrows():
                lines.append(f"| `{row['radar_type']}` | `{row['error_level']}` | {row[mae_col_zs]:.2f} | {row[rmse_col]:.2f} | {row['gate_hit_rate_pct']:.1f}% |")
            lines.append("\n*(LoRA SFT fine-tuning in progress or scheduled)*\n")

    summary_file = RESULTS_ROOT / "univariate_fixed_summary.md"
    summary_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[COMPILED] Master Summary saved to: {summary_file}")

if __name__ == "__main__":
    compile_summary()

