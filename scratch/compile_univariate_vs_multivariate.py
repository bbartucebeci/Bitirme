"""PULSAR: Compile Master Univariate vs. Multivariate Comparison Summary."""

from pathlib import Path
import pandas as pd
import numpy as np
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_ROOT = PROJECT_ROOT / "results" / "timesfm_3.0"

def compile_comparison():
    lines = [
        "# PULSAR: Univariate vs. Joint 5-Channel Multivariate Benchmark Summary",
        f"\n**Compiled on**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "\nThis report directly compares the predictive fidelity of **Independent Univariate Adapters** against **Joint 5-Channel Multivariate Modeling** across all 20 single-radar fixed datasets.",
        "Both regimes evaluate with **ground-truth emitter pulse masking** (filtering out receiver false alarms and dropped pulse doublings).\n",
        "---",
    ]

    # Load Multivariate Results
    mv_zs_csv = RESULTS_ROOT / "zero_shot" / "multivariate_fixed" / "metrics.csv"
    mv_lora_csv = RESULTS_ROOT / "lora_sft" / "multivariate_fixed" / "metrics.csv"

    if not mv_zs_csv.exists() or not mv_lora_csv.exists():
        lines.append("\n*Multivariate evaluation or training currently in progress...*\n")
        summary_file = RESULTS_ROOT / "univariate_vs_multivariate_summary.md"
        summary_file.write_text("\n".join(lines), encoding="utf-8")
        print(f"[INTERIM] Summary written to: {summary_file}")
        return

    df_mv_zs = pd.read_csv(mv_zs_csv)
    df_mv_lora = pd.read_csv(mv_lora_csv)

    # Load Univariate Results
    uv_pri_zs = pd.read_csv(RESULTS_ROOT / "zero_shot" / "univariate_fixed" / "pri" / "metrics.csv")
    uv_pri_lora = pd.read_csv(RESULTS_ROOT / "lora_sft" / "univariate_fixed" / "pri" / "metrics.csv")
    uv_rf_lora = pd.read_csv(RESULTS_ROOT / "lora_sft" / "univariate_fixed" / "frequency" / "metrics.csv")

    merged = pd.merge(
        uv_pri_lora[["radar_type", "error_level", "mae_us", "gate_hit_rate_pct"]].rename(
            columns={"mae_us": "uv_pri_mae", "gate_hit_rate_pct": "uv_pri_hit"}
        ),
        df_mv_lora[["radar_type", "error_level", "mae_pri", "hit_rate_pri", "mae_frequency", "hit_rate_frequency"]].rename(
            columns={"mae_pri": "mv_pri_mae", "hit_rate_pri": "mv_pri_hit", "mae_frequency": "mv_rf_mae", "hit_rate_frequency": "mv_rf_hit"}
        ),
        on=["radar_type", "error_level"],
    )

    uv_rf_mae_col = [c for c in uv_rf_lora.columns if c.lower().startswith("mae_")][0]
    merged = pd.merge(
        merged,
        uv_rf_lora[["radar_type", "error_level", uv_rf_mae_col]].rename(columns={uv_rf_mae_col: "uv_rf_mae"}),
        on=["radar_type", "error_level"],
    )

    lines.append("\n## LoRA Fine-Tuned: Univariate vs. Joint Multivariate Performance\n")
    lines.append("| Radar Type | Error Level | UV PRI MAE (μs) | MV PRI MAE (μs) | PRI Δ | UV PRI Hit | MV PRI Hit | UV RF MAE (MHz) | MV RF MAE (MHz) |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")

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

    summary_file = RESULTS_ROOT / "univariate_vs_multivariate_summary.md"
    summary_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SAVED] Univariate vs Multivariate Master Summary: {summary_file}")

if __name__ == "__main__":
    compile_comparison()

