"""PULSAR: Master Benchmark Visualization Suite (Primary Operational Benchmark: Varying Profile).

Generates publication-grade figures inspired by executive leaderboard aesthetics:
1. `macro_pri_benchmark_leaderboard.png`:
   - Left: Overall PRI Gate Hit Rate (%) & MAE Leaderboard (Horizontal Bars, ranked).
     Features distinct textures/hatches distinguishing Classical (///), LoRA SFT (solid), and Zero-Shot (..).
   - Right: PRI Modulation Matrix with Diagonal Split Triangles:
     - Upper-Left Triangle: Gate Hit Rate (%) [YlGnBu cmap]
     - Lower-Right Triangle: Mean Absolute Error (μs) [YlOrRd cmap]
2. `noise_level_pri_benchmark_leaderboard.png`:
   - Left: Overall PRI Gate Hit Rate (%) & MAE Leaderboard (Horizontal Bars, ranked).
   - Right: PRI Noise Degradation Matrix with Diagonal Split Triangles (Clean -> Lv3).
3. `auxiliary_rf_aoa_comparison.png`: Carrier Frequency (RF) and Angle of Arrival (AOA)
   tracking comparison across models.
4. `univariate_vs_multivariate_comparison.png`: Univariate vs. 5-Channel Multivariate
   joint forecasting illustrating the auxiliary channel temporal anchoring effect.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors
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
    "legend.fontsize": 9.5,
    "figure.dpi": 300,
})

PROFILE_MODE = "varying"

# Load Benchmark Metric CSVs (Varying Profile)
classic_df = pd.read_csv(RESULTS_ROOT / f"classic/comparison_{PROFILE_MODE}_pri.csv")
tfm_zs_df = pd.read_csv(RESULTS_ROOT / f"timesfm/zero_shot/univariate_{PROFILE_MODE}/pri/metrics.csv")
tfm_lora_df = pd.read_csv(RESULTS_ROOT / f"timesfm/lora_sft/univariate_{PROFILE_MODE}/pri/metrics.csv")
tfm_mv_zs_df = pd.read_csv(RESULTS_ROOT / f"timesfm/zero_shot/multivariate_{PROFILE_MODE}/metrics.csv")
tfm_mv_lora_df = pd.read_csv(RESULTS_ROOT / f"timesfm/lora_sft/multivariate_{PROFILE_MODE}/metrics.csv")

chr_zs_df = pd.read_csv(RESULTS_ROOT / f"chronos2/zero_shot/univariate_{PROFILE_MODE}/pri/metrics.csv")
chr_lora_df = pd.read_csv(RESULTS_ROOT / f"chronos2/lora_sft/univariate_{PROFILE_MODE}/pri/metrics.csv")
chr_mv_zs_df = pd.read_csv(RESULTS_ROOT / f"chronos2/zero_shot/multivariate_{PROFILE_MODE}/metrics.csv")
chr_mv_lora_df = pd.read_csv(RESULTS_ROOT / f"chronos2/lora_sft/multivariate_{PROFILE_MODE}/metrics.csv")

tirex_df = pd.read_csv(RESULTS_ROOT / f"tirex2/zero_shot/univariate_{PROFILE_MODE}/pri/metrics.csv")
toto_df = pd.read_csv(RESULTS_ROOT / f"toto2/zero_shot/univariate_{PROFILE_MODE}/pri/metrics.csv")
t0_df = pd.read_csv(RESULTS_ROOT / f"t0_gamma/zero_shot/univariate_{PROFILE_MODE}/pri/metrics.csv")

RADAR_ORDER = ["stable", "dwell_and_switch", "sliding", "stagger", "jitter"]
RADAR_LABELS = ["Stable", "Dwell & Switch", "Sliding", "Stagger", "Jitter"]
ERROR_ORDER = ["clean", "error_lv1", "error_lv2", "error_lv3"]
ERROR_LABELS = ["Clean", "Error Lv1", "Error Lv2", "Error Lv3"]

MODELS = [
    {
        "name": "[Classic] Period Estimation (P_max=24)",
        "color": "#2c3e50",  # Classical: Dark Slate Steel
        "df": classic_df,
        "hit_col": "period_estimation_hit",
        "mae_col": "period_estimation_mae",
        "category": "classic",
        "hatch": "///",
        "edgecolor": "#1a252f",
        "linewidth": 1.2,
    },
    {
        "name": "[Classic] Kalman Filter (Bank)",
        "color": "#34495e",  # Classical: Medium Slate Steel
        "df": classic_df,
        "hit_col": "kalman_filter_hit",
        "mae_col": "kalman_filter_mae",
        "category": "classic",
        "hatch": "///",
        "edgecolor": "#1a252f",
        "linewidth": 1.2,
    },
    {
        "name": "[LoRA] Chronos-2 (Uni)",
        "color": "#1565c0",  # Chronos LoRA: Deep Royal Blue
        "df": chr_lora_df,
        "hit_col": "hit_rate_pct",
        "mae_col": "mae",
        "category": "lora",
        "hatch": "",
        "edgecolor": "#0d47a1",
        "linewidth": 1.1,
    },
    {
        "name": "[LoRA] TimesFM 3.0 (Uni)",
        "color": "#c62828",  # TimesFM LoRA: Deep Crimson Terracotta
        "df": tfm_lora_df,
        "hit_col": "gate_hit_rate_pct",
        "mae_col": "mae_us",
        "category": "lora",
        "hatch": "",
        "edgecolor": "#b71c1c",
        "linewidth": 1.1,
    },
    {
        "name": "[LoRA] Chronos-2 (Multi)",
        "color": "#1976d2",  # Chronos LoRA: Vivid Cobalt Blue
        "df": chr_mv_lora_df,
        "hit_col": "hit_rate_pri",
        "mae_col": "mae_pri",
        "category": "lora",
        "hatch": "",
        "edgecolor": "#0d47a1",
        "linewidth": 1.1,
    },
    {
        "name": "[Zero-Shot] t0-gamma (Uni)",
        "color": "#7b1fa2",  # Zero-Shot: Rich Amethyst Violet
        "df": t0_df,
        "hit_col": "gate_hit_rate_pct",
        "mae_col": "mae_us",
        "category": "zero_shot",
        "hatch": "..",
        "edgecolor": "#4a148c",
        "linewidth": 0.9,
    },
    {
        "name": "[Zero-Shot] Chronos-2 (Uni)",
        "color": "#64b5f6",  # Chronos ZS: Light Sky Blue
        "df": chr_zs_df,
        "hit_col": "hit_rate_pct",
        "mae_col": "mae",
        "category": "zero_shot",
        "hatch": "..",
        "edgecolor": "#1976d2",
        "linewidth": 0.9,
    },
    {
        "name": "[Zero-Shot] Toto 2.0 (Uni)",
        "color": "#00acc1",  # Zero-Shot: Cyan / Teal
        "df": toto_df,
        "hit_col": "gate_hit_rate_pct",
        "mae_col": "mae_us",
        "category": "zero_shot",
        "hatch": "..",
        "edgecolor": "#00838f",
        "linewidth": 0.9,
    },
    {
        "name": "[Zero-Shot] Chronos-2 (Multi)",
        "color": "#90caf9",  # Chronos ZS: Soft Ice Blue
        "df": chr_mv_zs_df,
        "hit_col": "hit_rate_pri",
        "mae_col": "mae_pri",
        "category": "zero_shot",
        "hatch": "..",
        "edgecolor": "#1976d2",
        "linewidth": 0.9,
    },
    {
        "name": "[Classic] HMM (Baum-Welch + Viterbi)",
        "color": "#455a64",  # Classical: Slate Grey
        "df": classic_df,
        "hit_col": "hidden_markov_model_hit",
        "mae_col": "hidden_markov_model_mae",
        "category": "classic",
        "hatch": "///",
        "edgecolor": "#1a252f",
        "linewidth": 1.2,
    },
    {
        "name": "[LoRA] TimesFM 3.0 (Multi)",
        "color": "#d84315",  # TimesFM LoRA: Rust / Burnt Orange
        "df": tfm_mv_lora_df,
        "hit_col": "hit_rate_pri",
        "mae_col": "mae_pri",
        "category": "lora",
        "hatch": "",
        "edgecolor": "#bf360c",
        "linewidth": 1.1,
    },
    {
        "name": "[Zero-Shot] TiRex-2 (Uni)",
        "color": "#ff8f00",  # Zero-Shot: Vivid Amber
        "df": tirex_df,
        "hit_col": "hit_rate_pct",
        "mae_col": "mae",
        "category": "zero_shot",
        "hatch": "..",
        "edgecolor": "#e65100",
        "linewidth": 0.9,
    },
    {
        "name": "[Zero-Shot] TimesFM 3.0 (Multi)",
        "color": "#f57c00",  # TimesFM ZS: Warm Orange-Gold
        "df": tfm_mv_zs_df,
        "hit_col": "hit_rate_pri",
        "mae_col": "mae_pri",
        "category": "zero_shot",
        "hatch": "..",
        "edgecolor": "#e65100",
        "linewidth": 0.9,
    },
    {
        "name": "[Zero-Shot] TimesFM 3.0 (Uni)",
        "color": "#ffb74d",  # TimesFM ZS: Light Golden Sand
        "df": tfm_zs_df,
        "hit_col": "gate_hit_rate_pct",
        "mae_col": "mae_us",
        "category": "zero_shot",
        "hatch": "..",
        "edgecolor": "#ef6c00",
        "linewidth": 0.9,
    },
    {
        "name": "[Classic] Rolling Median (W=32)",
        "color": "#607d8b",  # Classical: Light Slate
        "df": classic_df,
        "hit_col": "rolling_median_hit",
        "mae_col": "rolling_median_mae",
        "category": "classic",
        "hatch": "///",
        "edgecolor": "#1a252f",
        "linewidth": 1.2,
    },
]


def render_benchmark_graphic(group_by="radar", out_filename="macro_pri_benchmark_leaderboard.png"):
    """Renders 2-part graphic: Left Leaderboard + Right Aligned Diagonal Split Triangles."""
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
            "category": m["category"],
            "hatch": m["hatch"],
            "edgecolor": m["edgecolor"],
            "linewidth": m["linewidth"],
            "macro_hit": macro_hit,
            "macro_mae": macro_mae,
            "cells": cell_stats,
        })

    # Sort descending by overall Macro Hit Rate
    parsed_models.sort(key=lambda x: x["macro_hit"], reverse=True)

    N = len(parsed_models)
    M = len(cols)
    fig = plt.figure(figsize=(23, 10.5), dpi=300)
    gs = fig.add_gridspec(1, 2, width_ratios=[0.44, 0.56], wspace=0.18)
    ax_bar = fig.add_subplot(gs[0, 0])
    ax_heat = fig.add_subplot(gs[0, 1])

    # Left: Horizontal Bar Chart
    y_pos = np.arange(N)[::-1]
    hits = [m["macro_hit"] for m in parsed_models]
    maes = [m["macro_mae"] for m in parsed_models]
    colors = [m["color"] for m in parsed_models]
    hatches = [m["hatch"] for m in parsed_models]
    edgecolors = [m["edgecolor"] for m in parsed_models]
    linewidths = [m["linewidth"] for m in parsed_models]
    names = [m["name"] for m in parsed_models]

    ax_bar.set_axisbelow(True)
    ax_bar.grid(axis="x", linestyle=":", color="#d6d6d6", alpha=0.8, zorder=0)

    for idx in range(N):
        ax_bar.barh(
            y_pos[idx],
            hits[idx],
            color=colors[idx],
            height=0.74,
            edgecolor=edgecolors[idx],
            hatch=hatches[idx],
            linewidth=linewidths[idx],
            alpha=0.95,
            zorder=2,
        )

    ax_bar.set_yticks(y_pos)
    ax_bar.set_yticklabels(names, fontsize=10.5, fontweight="semibold", color="#202124")
    ax_bar.set_xlim(0, 105)
    ax_bar.set_xlabel("Mean PRI Gate Hit Rate (%) [±10 μs Gate Corridor]", fontsize=11, fontweight="bold", labelpad=8)
    ax_bar.set_title("A. Overall Tactical PRI Gate Hit Rate & MAE Leaderboard", fontsize=12.5, fontweight="bold", loc="left", pad=12)

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

    # Legend for Paradigm Differentiation (Classic vs LoRA vs Zero-Shot)
    legend_handles = [
        patches.Patch(facecolor="#34495e", edgecolor="#1a252f", hatch="///", label="Classical Signal Processing Baselines"),
        patches.Patch(facecolor="#1565c0", edgecolor="#0d47a1", label="Fine-Tuned Foundation Models (LoRA SFT)"),
        patches.Patch(facecolor="#90caf9", edgecolor="#37474f", hatch="..", label="Pre-Trained Foundation Models (Zero-Shot)"),
    ]
    ax_bar.legend(
        handles=legend_handles,
        loc="lower right",
        frameon=True,
        facecolor="#ffffff",
        edgecolor="#cccccc",
        framealpha=0.95,
        fontsize=9.2,
    )

    # Right: Aligned Diagonal Split Triangles
    cmap_hit = plt.cm.YlGnBu
    norm_hit = mcolors.Normalize(vmin=0, vmax=100)

    cmap_mae = plt.cm.YlOrRd
    norm_mae = mcolors.Normalize(vmin=0, vmax=60)

    for r_idx, m in enumerate(parsed_models):
        for c_idx in range(M):
            c_hit, c_mae = m["cells"][c_idx]

            color_hit = cmap_hit(norm_hit(c_hit))
            color_mae = cmap_mae(norm_mae(np.clip(c_mae, 0, 60)))

            # Upper-Left Triangle (Hit Rate %)
            poly_top = patches.Polygon(
                [
                    (c_idx - 0.5, r_idx - 0.5),
                    (c_idx + 0.5, r_idx - 0.5),
                    (c_idx - 0.5, r_idx + 0.5),
                ],
                facecolor=color_hit,
                edgecolor="#ffffff",
                linewidth=0.75,
                zorder=2,
            )
            # Lower-Right Triangle (MAE μs)
            poly_bot = patches.Polygon(
                [
                    (c_idx + 0.5, r_idx - 0.5),
                    (c_idx + 0.5, r_idx + 0.5),
                    (c_idx - 0.5, r_idx + 0.5),
                ],
                facecolor=color_mae,
                edgecolor="#ffffff",
                linewidth=0.75,
                zorder=2,
            )

            ax_heat.add_patch(poly_top)
            ax_heat.add_patch(poly_bot)

            # High-contrast dynamic text
            hit_text_color = "white" if c_hit > 60 else "#141414"
            mae_text_color = "white" if c_mae > 35 else "#141414"

            # Top-left label: Hit Rate %
            ax_heat.text(
                c_idx - 0.16,
                r_idx - 0.14,
                f"{c_hit:.1f}%",
                ha="center",
                va="center",
                fontsize=9.2,
                fontweight="bold",
                color=hit_text_color,
                zorder=3,
            )
            # Bottom-right label: MAE μs
            ax_heat.text(
                c_idx + 0.16,
                r_idx + 0.18,
                f"{c_mae:.1f} μs",
                ha="center",
                va="center",
                fontsize=8.4,
                fontweight="semibold",
                color=mae_text_color,
                zorder=3,
            )

    ax_heat.set_xlim(-0.5, M - 0.5)
    ax_heat.set_ylim(N - 0.5, -0.5)  # Rank 1 at top, matching leaderboard
    ax_heat.set_xticks(np.arange(M))
    ax_heat.set_xticklabels(col_labels, fontsize=11, fontweight="bold", color="#202124")
    ax_heat.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False, left=False, right=False)
    ax_heat.set_yticks([])

    sub_title = (
        "B. PRI Hit Rate (Upper-Left) & MAE (Lower-Right) by Radar Modulation Type"
        if is_radar
        else "B. PRI Hit Rate (Upper-Left) & MAE (Lower-Right) by Noise Error Level"
    )
    ax_heat.set_title(sub_title, fontsize=12.0, fontweight="bold", loc="left", pad=28)
    ax_heat.spines[:].set_color("#888888")
    ax_heat.spines[:].set_linewidth(1.0)

    # Dual Colorbars
    sm_hit = plt.cm.ScalarMappable(cmap=cmap_hit, norm=norm_hit)
    sm_mae = plt.cm.ScalarMappable(cmap=cmap_mae, norm=norm_mae)

    cax_hit = fig.add_axes([0.915, 0.55, 0.016, 0.33])
    cbar_hit = fig.colorbar(sm_hit, cax=cax_hit)
    cbar_hit.set_label("Upper-Left: Gate Hit Rate (%)", fontsize=9.5, fontweight="bold")
    cbar_hit.ax.tick_params(labelsize=8.5)

    cax_mae = fig.add_axes([0.915, 0.14, 0.016, 0.33])
    cbar_mae = fig.colorbar(sm_mae, cax=cax_mae)
    cbar_mae.set_label("Lower-Right: Mean Absolute Error (μs)", fontsize=9.5, fontweight="bold")
    cbar_mae.ax.tick_params(labelsize=8.5)

    main_title = (
        "Operational Benchmark (Varying Profile): Periodicity Search vs. Foundation Models Across Radar Modulations"
        if is_radar
        else "Operational Benchmark (Varying Profile): Noise Degradation & Error Resilience (Clean → Error Level 3)"
    )
    fig.suptitle(main_title, fontsize=15.5, fontweight="bold", y=0.98, color="#1a1a1a")

    out_path = COMPARISON_DIR / out_filename
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[SAVED] {out_path}")


def plot_auxiliary_rf_aoa():
    """Carrier Frequency (RF) and Angle of Arrival (AOA) Performance (Varying Profile)."""
    fig, (ax_rf, ax_aoa) = plt.subplots(1, 2, figsize=(18, 6.5), dpi=300)

    rf_zs_path = RESULTS_ROOT / f"timesfm/zero_shot/univariate_{PROFILE_MODE}/frequency/metrics.csv"
    rf_lora_path = RESULTS_ROOT / f"timesfm/lora_sft/univariate_{PROFILE_MODE}/frequency/metrics.csv"
    aoa_zs_path = RESULTS_ROOT / f"timesfm/zero_shot/univariate_{PROFILE_MODE}/aoa/metrics.csv"
    aoa_lora_path = RESULTS_ROOT / f"timesfm/lora_sft/univariate_{PROFILE_MODE}/aoa/metrics.csv"

    radar_abbrevs = ["Stable", "Dwell&Sw", "Sliding", "Stagger", "Jitter"]
    x = np.arange(len(RADAR_ORDER))
    width = 0.38

    if rf_zs_path.exists() and rf_lora_path.exists():
        df_rf_zs = pd.read_csv(rf_zs_path)
        df_rf_lora = pd.read_csv(rf_lora_path)
        rf_col_zs = [c for c in df_rf_zs.columns if c.lower() == "mae_mhz"][0]
        rf_col_lora = [c for c in df_rf_lora.columns if c.lower() == "mae_mhz"][0]

        rf_zs_means = [df_rf_zs[df_rf_zs["radar_type"] == r][rf_col_zs].mean() for r in RADAR_ORDER]
        rf_lora_means = [df_rf_lora[df_rf_lora["radar_type"] == r][rf_col_lora].mean() for r in RADAR_ORDER]

        ax_rf.bar(x - width/2, rf_zs_means, width, label="TimesFM 3.0 (Zero-Shot)", color="#4285F4", alpha=0.9, edgecolor="white", hatch="..")
        ax_rf.bar(x + width/2, rf_lora_means, width, label="TimesFM 3.0 (LoRA SFT)", color="#0F9D58", alpha=0.9, edgecolor="white")

        for i in range(len(RADAR_ORDER)):
            diff = rf_zs_means[i] - rf_lora_means[i]
            if diff > 0.05:
                pct = (diff / rf_zs_means[i]) * 100
                ax_rf.annotate(
                    f"-{pct:.1f}%",
                    xy=(x[i] + width/2, rf_lora_means[i]),
                    xytext=(x[i] + width/2, rf_lora_means[i] + 0.15),
                    ha="center",
                    fontsize=8.5,
                    fontweight="bold",
                    color="#0F9D58",
                )

        ax_rf.set_title("Carrier Frequency (RF) Tracking Error by Radar Type", fontweight="bold", fontsize=12)
        ax_rf.set_xticks(x)
        ax_rf.set_xticklabels(radar_abbrevs, fontweight="semibold")
        ax_rf.set_ylabel("RF MAE (MHz)", fontweight="bold")
        ax_rf.grid(True, linestyle=":", alpha=0.6)
        ax_rf.legend(loc="upper right", frameon=True)

    if aoa_zs_path.exists() and aoa_lora_path.exists():
        df_aoa_zs = pd.read_csv(aoa_zs_path)
        df_aoa_lora = pd.read_csv(aoa_lora_path)
        aoa_col_zs = [c for c in df_aoa_zs.columns if "deg" in c.lower() or "mae" in c.lower()][0]
        aoa_col_lora = [c for c in df_aoa_lora.columns if "deg" in c.lower() or "mae" in c.lower()][0]

        aoa_zs_means = [df_aoa_zs[df_aoa_zs["radar_type"] == r][aoa_col_zs].mean() for r in RADAR_ORDER]
        aoa_lora_means = [df_aoa_lora[df_aoa_lora["radar_type"] == r][aoa_col_lora].mean() for r in RADAR_ORDER]

        ax_aoa.bar(x - width/2, aoa_zs_means, width, label="TimesFM 3.0 (Zero-Shot)", color="#4285F4", alpha=0.9, edgecolor="white", hatch="..")
        ax_aoa.bar(x + width/2, aoa_lora_means, width, label="TimesFM 3.0 (LoRA SFT)", color="#0F9D58", alpha=0.9, edgecolor="white")

        for i in range(len(RADAR_ORDER)):
            diff = aoa_zs_means[i] - aoa_lora_means[i]
            if diff > 0.05:
                pct = (diff / aoa_zs_means[i]) * 100
                ax_aoa.annotate(
                    f"-{pct:.1f}%",
                    xy=(x[i] + width/2, aoa_lora_means[i]),
                    xytext=(x[i] + width/2, aoa_lora_means[i] + 0.15),
                    ha="center",
                    fontsize=8.5,
                    fontweight="bold",
                    color="#0F9D58",
                )

        ax_aoa.set_title("Circular Angle of Arrival (AOA) Error by Radar Type", fontweight="bold", fontsize=12)
        ax_aoa.set_xticks(x)
        ax_aoa.set_xticklabels(radar_abbrevs, fontweight="semibold")
        ax_aoa.set_ylabel("AOA MAE (Degrees)", fontweight="bold")
        ax_aoa.grid(True, linestyle=":", alpha=0.6)
        ax_aoa.legend(loc="upper right", frameon=True)

    fig.suptitle(
        f"Auxiliary Modality Multi-Task Tracking: Spectral (RF) & Spatial (AOA) Performance ({PROFILE_MODE.capitalize()} Profile)",
        fontsize=15,
        fontweight="bold",
        y=1.02,
    )
    plt.tight_layout()
    out_path = COMPARISON_DIR / "auxiliary_rf_aoa_comparison.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[SAVED] {out_path}")


def plot_univariate_vs_multivariate():
    """Univariate vs. 5-Channel Multivariate Joint Forecasting (Varying Profile)."""
    fig, (ax_tfm, ax_chr) = plt.subplots(1, 2, figsize=(18, 6.5), dpi=300)

    tfm_uni_path = RESULTS_ROOT / f"timesfm/lora_sft/univariate_{PROFILE_MODE}/pri/metrics.csv"
    tfm_mv_path = RESULTS_ROOT / f"timesfm/lora_sft/multivariate_{PROFILE_MODE}/metrics.csv"
    chr_uni_path = RESULTS_ROOT / f"chronos2/lora_sft/univariate_{PROFILE_MODE}/pri/metrics.csv"
    chr_mv_path = RESULTS_ROOT / f"chronos2/lora_sft/multivariate_{PROFILE_MODE}/metrics.csv"

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
        ax_tfm.set_xticklabels(ERROR_LABELS, fontweight="semibold")
        ax_tfm.set_ylabel("PRI MAE (μs)", fontweight="bold")
        ax_tfm.grid(True, linestyle=":", alpha=0.6)
        ax_tfm.legend(loc="upper left", frameon=True)

    if chr_uni_path.exists() and chr_mv_path.exists():
        df_chr_uni = pd.read_csv(chr_uni_path)
        df_chr_mv = pd.read_csv(chr_mv_path)
        chr_uni_means = [df_chr_uni[df_chr_uni["error_level"] == e]["mae"].mean() for e in ERROR_ORDER]
        chr_mv_means = [df_chr_mv[df_chr_mv["error_level"] == e]["mae_pri"].mean() for e in ERROR_ORDER]

        ax_chr.bar(x - width/2, chr_uni_means, width, label="Univariate PRI (Delta-TOA only)", color="#1565c0", alpha=0.85, edgecolor="white")
        ax_chr.bar(x + width/2, chr_mv_means, width, label="Multivariate 5-Channel (Joint)", color="#455a64", alpha=0.85, edgecolor="white")

        for i in range(len(ERROR_ORDER)):
            diff = chr_uni_means[i] - chr_mv_means[i]
            if abs(diff) > 0.05:
                symbol = "▼" if diff > 0 else "▲"
                color = "#2e7d32" if diff > 0 else "#c62828"
                ax_chr.annotate(
                    f"{symbol} {abs(diff):.2f} μs",
                    xy=(x[i] + width/2, chr_mv_means[i]),
                    xytext=(x[i] + width/2, chr_mv_means[i] + 3.0),
                    ha="center",
                    fontsize=8.5,
                    color=color,
                    fontweight="bold",
                )

        ax_chr.set_title("Chronos-2 LoRA: Univariate vs. 5-Channel Multivariate", fontweight="bold")
        ax_chr.set_xticks(x)
        ax_chr.set_xticklabels(ERROR_LABELS, fontweight="semibold")
        ax_chr.set_ylabel("PRI MAE (μs)", fontweight="bold")
        ax_chr.grid(True, linestyle=":", alpha=0.6)
        ax_chr.legend(loc="upper left", frameon=True)

    fig.suptitle(
        f"Auxiliary Channel Temporal Anchoring: Univariate vs. 5-Channel Multivariate Joint Recovery ({PROFILE_MODE.capitalize()} Profile)",
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
    print("Generating master benchmark figures (Varying Profile - Primary Operational Benchmark)...")
    render_benchmark_graphic(group_by="radar", out_filename="macro_pri_benchmark_leaderboard.png")
    render_benchmark_graphic(group_by="error", out_filename="noise_level_pri_benchmark_leaderboard.png")
    plot_auxiliary_rf_aoa()
    plot_univariate_vs_multivariate()
    print("All master benchmark figures generated successfully.")


if __name__ == "__main__":
    main()
