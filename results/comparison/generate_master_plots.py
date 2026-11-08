"""PULSAR: Master Benchmark Visualization Suite.

Generates publication-grade figures inspired by executive leaderboard aesthetics:
1. `macro_pri_benchmark_leaderboard.png`:
   - Left: Overall PRI Gate Hit Rate (%) & MAE Leaderboard (Horizontal Bars, ranked).
   - Right: PRI Hit Rate (%) & [MAE μs] Heatmap Table by Radar Modulation Type.
2. `noise_level_pri_benchmark_leaderboard.png`:
   - Left: Overall PRI Gate Hit Rate (%) & MAE Leaderboard (Horizontal Bars, ranked).
   - Right: PRI Hit Rate (%) & [MAE μs] Heatmap Table by Noise Error Level (Clean -> Lv3).
3. `auxiliary_rf_aoa_comparison.png`: Carrier Frequency (RF) and Angle of Arrival (AOA)
   tracking comparison across models.
4. `univariate_vs_multivariate_comparison.png`: Univariate vs. 5-Channel Multivariate
   joint forecasting illustrating the auxiliary channel temporal anchoring effect.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

COMPARISON_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = COMPARISON_DIR.parent.parent
RESULTS_ROOT = PROJECT_ROOT / "results"

# Visual Theme & Typography
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial"],
    "font.family": "sans-serif",
    "figure.titlesize": 16,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 9,
    "figure.dpi": 300,
})

# Load Benchmark Metric CSVs
classic_df = pd.read_csv(RESULTS_ROOT / "classic/comparison_fixed_pri.csv")
tfm_zs_df = pd.read_csv(RESULTS_ROOT / "timesfm/zero_shot/univariate_fixed/pri/metrics.csv")
tfm_lora_df = pd.read_csv(RESULTS_ROOT / "timesfm/lora_sft/univariate_fixed/pri/metrics.csv")
tfm_mv_zs_df = pd.read_csv(RESULTS_ROOT / "timesfm/zero_shot/multivariate_fixed/metrics.csv")
tfm_mv_lora_df = pd.read_csv(RESULTS_ROOT / "timesfm/lora_sft/multivariate_fixed/metrics.csv")

chr_zs_df = pd.read_csv(RESULTS_ROOT / "chronos2/zero_shot/univariate_fixed/pri/metrics.csv")
chr_lora_df = pd.read_csv(RESULTS_ROOT / "chronos2/lora_sft/univariate_fixed/pri/metrics.csv")
chr_mv_zs_df = pd.read_csv(RESULTS_ROOT / "chronos2/zero_shot/multivariate_fixed/metrics.csv")
chr_mv_lora_df = pd.read_csv(RESULTS_ROOT / "chronos2/lora_sft/multivariate_fixed/metrics.csv")

tirex_df = pd.read_csv(RESULTS_ROOT / "tirex2/zero_shot/univariate_fixed/pri/metrics.csv")
toto_df = pd.read_csv(RESULTS_ROOT / "toto2/zero_shot/univariate_fixed/pri/metrics.csv")
t0_df = pd.read_csv(RESULTS_ROOT / "t0_gamma/zero_shot/univariate_fixed/pri/metrics.csv")

RADAR_ORDER = ["stable", "dwell_and_switch", "sliding", "stagger", "jitter"]
RADAR_LABELS = ["Stable", "Dwell & Switch", "Sliding", "Stagger", "Jitter"]
ERROR_ORDER = ["clean", "error_lv1", "error_lv2", "error_lv3"]
ERROR_LABELS = ["Clean", "Error Lv1", "Error Lv2", "Error Lv3"]

MODELS = [
    {
        "name": "Classic: Period Estimation (P_max=24)",
        "color": "#107c78",  # Classical: Deep Forest Teal
        "df": classic_df,
        "hit_col": "period_estimation_hit",
        "mae_col": "period_estimation_mae",
        "category": "classic",
    },
    {
        "name": "Classic: Kalman Filter (Bank)",
        "color": "#288a85",  # Classical: Medium Slate Teal
        "df": classic_df,
        "hit_col": "kalman_filter_hit",
        "mae_col": "kalman_filter_mae",
        "category": "classic",
    },
    {
        "name": "Chronos-2 (LoRA SFT, Uni)",
        "color": "#1565c0",  # Chronos LoRA: Deep Royal Blue
        "df": chr_lora_df,
        "hit_col": "hit_rate_pct",
        "mae_col": "mae",
        "category": "chronos_lora",
    },
    {
        "name": "TimesFM 3.0 (LoRA SFT, Uni)",
        "color": "#c62828",  # TimesFM LoRA: Deep Crimson Terracotta
        "df": tfm_lora_df,
        "hit_col": "gate_hit_rate_pct",
        "mae_col": "mae_us",
        "category": "timesfm_lora",
    },
    {
        "name": "Chronos-2 (LoRA SFT, Multi)",
        "color": "#1976d2",  # Chronos LoRA: Vivid Cobalt Blue
        "df": chr_mv_lora_df,
        "hit_col": "hit_rate_pri",
        "mae_col": "mae_pri",
        "category": "chronos_lora",
    },
    {
        "name": "t0-gamma (Zero-Shot, Uni)",
        "color": "#7b1fa2",  # Zero-Shot: Rich Amethyst Violet
        "df": t0_df,
        "hit_col": "gate_hit_rate_pct",
        "mae_col": "mae_us",
        "category": "zs_other",
    },
    {
        "name": "Chronos-2 (Zero-Shot, Uni)",
        "color": "#64b5f6",  # Chronos ZS: Light Sky Blue (matching Chronos family)
        "df": chr_zs_df,
        "hit_col": "hit_rate_pct",
        "mae_col": "mae",
        "category": "chronos_zs",
    },
    {
        "name": "Toto 2.0 (Zero-Shot, Uni)",
        "color": "#00acc1",  # Zero-Shot: Cyan / Teal
        "df": toto_df,
        "hit_col": "gate_hit_rate_pct",
        "mae_col": "mae_us",
        "category": "zs_other",
    },
    {
        "name": "Chronos-2 (Zero-Shot, Multi)",
        "color": "#90caf9",  # Chronos ZS: Soft Ice Blue (matching Chronos family)
        "df": chr_mv_zs_df,
        "hit_col": "hit_rate_pri",
        "mae_col": "mae_pri",
        "category": "chronos_zs",
    },
    {
        "name": "Classic: HMM (Baum-Welch + Viterbi)",
        "color": "#546e7a",  # Classical: Slate Grey
        "df": classic_df,
        "hit_col": "hidden_markov_model_hit",
        "mae_col": "hidden_markov_model_mae",
        "category": "classic",
    },
    {
        "name": "TimesFM 3.0 (LoRA SFT, Multi)",
        "color": "#d84315",  # TimesFM LoRA: Rust / Burnt Orange
        "df": tfm_mv_lora_df,
        "hit_col": "hit_rate_pri",
        "mae_col": "mae_pri",
        "category": "timesfm_lora",
    },
    {
        "name": "TiRex-2 (Zero-Shot, Uni)",
        "color": "#ff8f00",  # Zero-Shot: Vivid Amber
        "df": tirex_df,
        "hit_col": "hit_rate_pct",
        "mae_col": "mae",
        "category": "zs_other",
    },
    {
        "name": "TimesFM 3.0 (Zero-Shot, Multi)",
        "color": "#f57c00",  # TimesFM ZS: Warm Orange-Gold (matching TimesFM family)
        "df": tfm_mv_zs_df,
        "hit_col": "hit_rate_pri",
        "mae_col": "mae_pri",
        "category": "timesfm_zs",
    },
    {
        "name": "TimesFM 3.0 (Zero-Shot, Uni)",
        "color": "#ffb74d",  # TimesFM ZS: Light Golden Sand (matching TimesFM family)
        "df": tfm_zs_df,
        "hit_col": "gate_hit_rate_pct",
        "mae_col": "mae_us",
        "category": "timesfm_zs",
    },
    {
        "name": "Classic: Rolling Median (W=32)",
        "color": "#90a4ae",  # Classical: Light Slate
        "df": classic_df,
        "hit_col": "rolling_median_hit",
        "mae_col": "rolling_median_mae",
        "category": "classic",
    },
]


def render_benchmark_graphic(group_by="radar", out_filename="macro_pri_benchmark_leaderboard.png"):
    """Renders 2-part graphic: Left Leaderboard + Right Aligned Heatmap."""
    is_radar = (group_by == "radar")
    cols = RADAR_ORDER if is_radar else ERROR_ORDER
    col_labels = RADAR_LABELS if is_radar else ERROR_LABELS
    group_col = "radar_type" if is_radar else "error_level"

    parsed_models = []
    for m in MODELS:
        df = m["df"]
        h_col = m["hit_col"]
        m_col = m["mae_col"]

        macro_hit = float(df[h_col].mean())
        macro_mae = float(df[m_col].mean())

        cell_stats = []
        for c in cols:
            sub = df[df[group_col] == c]
            c_hit = float(sub[h_col].mean())
            c_mae = float(sub[m_col].mean())
            cell_stats.append((c_hit, c_mae))

        parsed_models.append({
            "name": m["name"],
            "color": m["color"],
            "macro_hit": macro_hit,
            "macro_mae": macro_mae,
            "cells": cell_stats,
        })

    parsed_models.sort(key=lambda x: x["macro_hit"], reverse=True)

    N = len(parsed_models)
    fig = plt.figure(figsize=(22, 10), dpi=300)
    gs = fig.add_gridspec(1, 2, width_ratios=[0.45, 0.55], wspace=0.18)
    ax_bar = fig.add_subplot(gs[0, 0])
    ax_heat = fig.add_subplot(gs[0, 1])

    # Left: Horizontal Bar Chart
    y_pos = np.arange(N)[::-1]
    hits = [m["macro_hit"] for m in parsed_models]
    maes = [m["macro_mae"] for m in parsed_models]
    colors = [m["color"] for m in parsed_models]
    names = [m["name"] for m in parsed_models]

    ax_bar.set_axisbelow(True)
    ax_bar.grid(axis="x", linestyle=":", color="#e0e0e0", alpha=0.8, zorder=0)

    ax_bar.barh(y_pos, hits, color=colors, height=0.72, edgecolor="none", alpha=0.95, zorder=2)
    ax_bar.set_yticks(y_pos)
    ax_bar.set_yticklabels(names, fontsize=10.5, fontweight="semibold", color="#202124")
    ax_bar.set_xlim(0, 105)
    ax_bar.set_xlabel("Mean PRI Gate Hit Rate (%) [±10 μs Gate]", fontsize=11, fontweight="bold", labelpad=8)
    ax_bar.set_title("A. Overall PRI Gate Hit Rate & MAE Leaderboard", fontsize=12.5, fontweight="bold", loc="left", pad=12)

    for idx, (hit, mae) in enumerate(zip(hits, maes)):
        y = y_pos[idx]
        ax_bar.text(
            hit + 1.2,
            y,
            f"{hit:.1f}% (MAE: {mae:.1f} μs)",
            va="center",
            ha="left",
            fontsize=9.5,
            fontweight="bold",
            color="#202124",
        )

    ax_bar.spines["top"].set_visible(False)
    ax_bar.spines["right"].set_visible(False)
    ax_bar.spines["left"].set_color("#cccccc")
    ax_bar.spines["bottom"].set_color("#cccccc")

    # Right: Aligned Heatmap
    heat_matrix = np.zeros((N, len(cols)))
    for r_idx, m in enumerate(parsed_models):
        for c_idx in range(len(cols)):
            heat_matrix[r_idx, c_idx] = m["cells"][c_idx][0]

    cmap = plt.cm.YlGnBu
    im = ax_heat.imshow(heat_matrix, cmap=cmap, aspect="auto", vmin=0, vmax=100)

    ax_heat.set_xticks(np.arange(len(cols)))
    ax_heat.set_xticklabels(col_labels, fontsize=11, fontweight="bold", color="#202124")
    ax_heat.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False, left=False, right=False)
    ax_heat.set_yticks([])

    sub_title = (
        "B. PRI Hit Rate (%) & [MAE μs] by Radar Modulation Type"
        if is_radar
        else "B. PRI Hit Rate (%) & [MAE μs] by Noise Error Level"
    )
    ax_heat.set_title(sub_title, fontsize=12.5, fontweight="bold", loc="left", pad=28)

    for r_idx, m in enumerate(parsed_models):
        for c_idx in range(len(cols)):
            c_hit, c_mae = m["cells"][c_idx]
            text_color = "white" if c_hit > 55 else "#102027"
            ax_heat.text(
                c_idx,
                r_idx - 0.12,
                f"{c_hit:.1f}%",
                ha="center",
                va="center",
                fontsize=9.5,
                fontweight="bold",
                color=text_color,
            )
            ax_heat.text(
                c_idx,
                r_idx + 0.18,
                f"[{c_mae:.1f} μs]",
                ha="center",
                va="center",
                fontsize=8.5,
                color=text_color,
                alpha=0.92,
            )

    cbar = fig.colorbar(im, ax=ax_heat, fraction=0.035, pad=0.03)
    cbar.set_label("PRI Gate Hit Rate (%)", fontsize=10, fontweight="bold")
    cbar.ax.tick_params(labelsize=9)

    ax_heat.spines[:].set_visible(False)
    ax_heat.set_xticks(np.arange(len(cols) + 1) - 0.5, minor=True)
    ax_heat.set_yticks(np.arange(N + 1) - 0.5, minor=True)
    ax_heat.grid(which="minor", color="white", linestyle="-", linewidth=1.0)
    ax_heat.tick_params(which="minor", bottom=False, left=False, top=False, right=False)

    main_title = (
        "Macro PRI Benchmark: Explicit Periodicity Search vs. Foundation Models Across Radar Modulations"
        if is_radar
        else "Macro PRI Benchmark: Noise Degradation & Error Resilience (Clean → Error Level 3)"
    )
    fig.suptitle(main_title, fontsize=15.5, fontweight="bold", y=0.98, color="#1a1a1a")

    out_path = COMPARISON_DIR / out_filename
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[SAVED] {out_path}")


def plot_auxiliary_rf_aoa():
    """Carrier Frequency (RF) and Angle of Arrival (AOA) Performance."""
    fig, (ax_rf, ax_aoa) = plt.subplots(1, 2, figsize=(18, 6.5))

    rf_zs_path = RESULTS_ROOT / "timesfm/zero_shot/univariate_fixed/frequency/metrics.csv"
    rf_lora_path = RESULTS_ROOT / "timesfm/lora_sft/univariate_fixed/frequency/metrics.csv"
    aoa_zs_path = RESULTS_ROOT / "timesfm/zero_shot/univariate_fixed/aoa/metrics.csv"
    aoa_lora_path = RESULTS_ROOT / "timesfm/lora_sft/univariate_fixed/aoa/metrics.csv"

    radar_abbrevs = ["Stable", "Jitter", "Stagger", "Dwell&Sw", "Sliding"]
    x = np.arange(len(RADAR_ORDER))
    width = 0.38

    if rf_zs_path.exists() and rf_lora_path.exists():
        df_rf_zs = pd.read_csv(rf_zs_path)
        df_rf_lora = pd.read_csv(rf_lora_path)
        rf_col_zs = [c for c in df_rf_zs.columns if c.lower() == "mae_mhz"][0]
        rf_col_lora = [c for c in df_rf_lora.columns if c.lower() == "mae_mhz"][0]

        rf_zs_means = [df_rf_zs[df_rf_zs["radar_type"] == r][rf_col_zs].mean() for r in RADAR_ORDER]
        rf_lora_means = [df_rf_lora[df_rf_lora["radar_type"] == r][rf_col_lora].mean() for r in RADAR_ORDER]

        ax_rf.bar(x - width/2, rf_zs_means, width, label="TimesFM 3.0 (Zero-Shot)", color="#4285F4", alpha=0.9, edgecolor="white")
        ax_rf.bar(x + width/2, rf_lora_means, width, label="TimesFM 3.0 (LoRA SFT)", color="#0F9D58", alpha=0.9, edgecolor="white")
        ax_rf.axhline(2.0, color="#d32f2f", linestyle="--", linewidth=1.2, label="Acceptance Gate (±2.0 MHz)")
        ax_rf.set_title("Carrier Frequency (RF) Tracking Error", fontweight="bold")
        ax_rf.set_xticks(x)
        ax_rf.set_xticklabels(radar_abbrevs)
        ax_rf.set_ylabel("RF MAE (MHz)")
        ax_rf.grid(True, linestyle="--", alpha=0.6)
        ax_rf.legend(loc="upper right", frameon=True)

    if aoa_zs_path.exists() and aoa_lora_path.exists():
        df_aoa_zs = pd.read_csv(aoa_zs_path)
        df_aoa_lora = pd.read_csv(aoa_lora_path)

        aoa_zs_means = [df_aoa_zs[df_aoa_zs["radar_type"] == r]["mae_deg"].mean() for r in RADAR_ORDER]
        aoa_lora_means = [df_aoa_lora[df_aoa_lora["radar_type"] == r]["mae_deg"].mean() for r in RADAR_ORDER]

        ax_aoa.bar(x - width/2, aoa_zs_means, width, label="TimesFM 3.0 (Zero-Shot)", color="#4285F4", alpha=0.9, edgecolor="white")
        ax_aoa.bar(x + width/2, aoa_lora_means, width, label="TimesFM 3.0 (LoRA SFT)", color="#0F9D58", alpha=0.9, edgecolor="white")
        ax_aoa.axhline(2.0, color="#d32f2f", linestyle="--", linewidth=1.2, label="Acceptance Gate (±2.0°)")
        ax_aoa.set_title("Angle of Arrival (AOA) Bearing Tracking Error", fontweight="bold")
        ax_aoa.set_xticks(x)
        ax_aoa.set_xticklabels(radar_abbrevs)
        ax_aoa.set_ylabel("AOA Circular MAE (deg)")
        ax_aoa.grid(True, linestyle="--", alpha=0.6)
        ax_aoa.legend(loc="upper right", frameon=True)

    fig.suptitle("PULSAR Auxiliary Electronic Warfare Channels: Spectral (RF) & Spatial (AOA) Performance", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()

    out_path = COMPARISON_DIR / "auxiliary_rf_aoa_comparison.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[SAVED] {out_path}")


def plot_univariate_vs_multivariate():
    """Univariate vs. 5-Channel Multivariate Joint Forecasting."""
    fig, (ax_tfm, ax_chr) = plt.subplots(1, 2, figsize=(18, 6.5))

    tfm_uni_path = RESULTS_ROOT / "timesfm/lora_sft/univariate_fixed/pri/metrics.csv"
    tfm_mv_path = RESULTS_ROOT / "timesfm/lora_sft/multivariate_fixed/metrics.csv"
    chr_uni_path = RESULTS_ROOT / "chronos2/lora_sft/univariate_fixed/pri/metrics.csv"
    chr_mv_path = RESULTS_ROOT / "chronos2/lora_sft/multivariate_fixed/metrics.csv"

    x = np.arange(len(ERROR_ORDER))
    width = 0.35

    if tfm_uni_path.exists() and tfm_mv_path.exists():
        df_uni = pd.read_csv(tfm_uni_path)
        df_mv = pd.read_csv(tfm_mv_path)
        uni_means = [df_uni[df_uni["error_level"] == e]["mae_us"].mean() for e in ERROR_ORDER]
        mv_means = [df_mv[df_mv["error_level"] == e]["mae_pri"].mean() for e in ERROR_ORDER]

        ax_tfm.bar(x - width/2, uni_means, width, label="Univariate PRI (Delta-TOA only)", color="#0F9D58", alpha=0.85, edgecolor="white")
        ax_tfm.bar(x + width/2, mv_means, width, label="Multivariate 5-Channel (Joint)", color="#202124", alpha=0.85, edgecolor="white")

        for i in range(len(ERROR_ORDER)):
            diff = uni_means[i] - mv_means[i]
            if abs(diff) > 0.05:
                symbol = "▼" if diff > 0 else "▲"
                color = "#2e7d32" if diff > 0 else "#c62828"
                ax_tfm.annotate(
                    f"{symbol} {abs(diff):.2f} μs",
                    xy=(x[i] + width/2, mv_means[i]),
                    xytext=(x[i] + width/2, mv_means[i] + 3.0),
                    ha="center",
                    fontsize=8.5,
                    color=color,
                    fontweight="bold",
                )

        ax_tfm.set_title("TimesFM 3.0 LoRA: Univariate vs. 5-Channel Multivariate", fontweight="bold")
        ax_tfm.set_xticks(x)
        ax_tfm.set_xticklabels(ERROR_LABELS)
        ax_tfm.set_ylabel("PRI MAE (μs)")
        ax_tfm.grid(True, linestyle="--", alpha=0.6)
        ax_tfm.legend(loc="upper left", frameon=True)

    if chr_uni_path.exists() and chr_mv_path.exists():
        df_chr_uni = pd.read_csv(chr_uni_path)
        df_chr_mv = pd.read_csv(chr_mv_path)
        chr_uni_means = [df_chr_uni[df_chr_uni["error_level"] == e]["mae"].mean() for e in ERROR_ORDER]
        chr_mv_means = [df_chr_mv[df_chr_mv["error_level"] == e]["mae_pri"].mean() for e in ERROR_ORDER]

        ax_chr.bar(x - width/2, chr_uni_means, width, label="Univariate PRI (Delta-TOA only)", color="#E91E63", alpha=0.85, edgecolor="white")
        ax_chr.bar(x + width/2, chr_mv_means, width, label="Multivariate 5-Channel (Joint)", color="#4A148C", alpha=0.85, edgecolor="white")

        ax_chr.set_title("Chronos-2 LoRA: Univariate vs. 5-Channel Multivariate", fontweight="bold")
        ax_chr.set_xticks(x)
        ax_chr.set_xticklabels(ERROR_LABELS)
        ax_chr.set_ylabel("PRI MAE (μs)")
        ax_chr.grid(True, linestyle="--", alpha=0.6)
        ax_chr.legend(loc="upper left", frameon=True)

    fig.suptitle(
        "Auxiliary Channel Temporal Anchoring: Univariate vs. 5-Channel Multivariate Joint Recovery",
        fontsize=15,
        fontweight="bold",
        y=1.02,
    )
    plt.tight_layout()

    out_path = COMPARISON_DIR / "univariate_vs_multivariate_comparison.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[SAVED] {out_path}")


def main():
    print("[1/4] Generating screenshot-style Macro Leaderboard & Radar Modulation Heatmap...")
    render_benchmark_graphic("radar", "macro_pri_benchmark_leaderboard.png")

    print("[2/4] Generating screenshot-style Macro Leaderboard & Noise Error Level Heatmap...")
    render_benchmark_graphic("error", "noise_level_pri_benchmark_leaderboard.png")

    print("[3/4] Generating auxiliary spectral & spatial comparison figure...")
    plot_auxiliary_rf_aoa()

    print("[4/4] Generating univariate vs multivariate anchoring comparison figure...")
    plot_univariate_vs_multivariate()

    print("\n[SUCCESS] Master comparison visualization suite generated successfully.")


if __name__ == "__main__":
    main()
