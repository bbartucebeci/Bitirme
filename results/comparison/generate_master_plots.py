"""PULSAR: Master Comparison Visualization Suite.

Generates four publication-grade benchmark figures:
1. `master_benchmark_pri_bars.png`: 6-panel grouped bar chart comparing all foundation
   models and classic baselines across radar types and noise levels.
2. `noise_degradation_curves.png`: 6-panel noise degradation curves (Clean -> Lv3)
   highlighting model stability and error growth slopes.
3. `auxiliary_rf_aoa_comparison.png`: Carrier Frequency (RF) and Angle of Arrival (AOA)
   tracking comparison across models and error regimes.
4. `univariate_vs_multivariate_comparison.png`: Univariate vs. 5-Channel Multivariate
   joint forecasting illustrating the auxiliary channel temporal anchoring effect.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Paths
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
    "axes.edgecolor": "#cccccc",
    "axes.linewidth": 0.8,
    "grid.color": "#e0e0e0",
    "grid.linestyle": "--",
    "grid.alpha": 0.7,
})

RADAR_TYPES = ["stable", "jitter", "stagger", "dwell_and_switch", "sliding"]
RADAR_TITLES = {
    "stable": "Stable PRI (Constant)",
    "jitter": "Jittered PRI (Gaussian)",
    "stagger": "Staggered PRI (Multi-Position)",
    "dwell_and_switch": "Dwell & Switch PRI (Step-Agile)",
    "sliding": "Sliding PRI (Linear Chirp)",
}
ERROR_LEVELS = ["clean", "error_lv1", "error_lv2", "error_lv3"]
ERROR_LABELS = ["Clean", "Error Lv1", "Error Lv2", "Error Lv3"]

MODEL_CONFIGS = [
    {
        "id": "timesfm_lora",
        "label": "TimesFM 3.0 (LoRA SFT)",
        "color": "#0F9D58",  # Vibrant Google Green
        "path": RESULTS_ROOT / "timesfm" / "lora_sft" / "univariate_fixed" / "pri" / "metrics.csv",
        "col": "mae_us",
        "marker": "o",
    },
    {
        "id": "timesfm_zs",
        "label": "TimesFM 3.0 (Zero-Shot)",
        "color": "#4285F4",  # Google Blue
        "path": RESULTS_ROOT / "timesfm" / "zero_shot" / "univariate_fixed" / "pri" / "metrics.csv",
        "col": "mae_us",
        "marker": "s",
    },
    {
        "id": "chronos2_lora",
        "label": "Chronos-2 (LoRA SFT)",
        "color": "#E91E63",  # Magenta / Deep Pink
        "path": RESULTS_ROOT / "chronos2" / "lora_sft" / "univariate_fixed" / "pri" / "metrics.csv",
        "col": "mae",
        "marker": "^",
    },
    {
        "id": "chronos2_zs",
        "label": "Chronos-2 (Zero-Shot)",
        "color": "#9C27B0",  # Vivid Purple
        "path": RESULTS_ROOT / "chronos2" / "zero_shot" / "univariate_fixed" / "pri" / "metrics.csv",
        "col": "mae",
        "marker": "v",
    },
    {
        "id": "tirex2_zs",
        "label": "TiRex-2 (Zero-Shot)",
        "color": "#FF9800",  # Amber / Warm Orange
        "path": RESULTS_ROOT / "tirex2" / "zero_shot" / "univariate_fixed" / "pri" / "metrics.csv",
        "col": "mae",
        "marker": "D",
    },
    {
        "id": "toto2_zs",
        "label": "Toto 2.0 (Zero-Shot)",
        "color": "#00BCD4",  # Cyan / Teal
        "path": RESULTS_ROOT / "toto2" / "zero_shot" / "univariate_fixed" / "pri" / "metrics.csv",
        "col": "mae_us",
        "marker": "p",
    },
    {
        "id": "t0_gamma_zs",
        "label": "t0-gamma (Zero-Shot)",
        "color": "#795548",  # Deep Copper / Warm Brown
        "path": RESULTS_ROOT / "t0_gamma" / "zero_shot" / "univariate_fixed" / "pri" / "metrics.csv",
        "col": "mae_us",
        "marker": "h",
    },
    {
        "id": "period_est",
        "label": "Period Estimation (Classic)",
        "color": "#607D8B",  # Slate Blue-Grey
        "path": RESULTS_ROOT / "classic" / "comparison_fixed_pri.csv",
        "col": "period_estimation_mae",
        "marker": "x",
    },
    {
        "id": "kalman",
        "label": "Kalman Filter (Classic)",
        "color": "#3F51B5",  # Classic Indigo
        "path": RESULTS_ROOT / "classic" / "comparison_fixed_pri.csv",
        "col": "kalman_filter_mae",
        "marker": "+",
    },
]


def load_model_pri_data():
    """Builds a structured dictionary: data[model_id][(radar_type, error_level)] = mae."""
    data = {}
    for m in MODEL_CONFIGS:
        mid = m["id"]
        data[mid] = {}
        if not m["path"].exists():
            print(f"[WARN] Path missing for {mid}: {m['path']}")
            continue
        df = pd.read_csv(m["path"])
        val_col = m["col"]
        for _, row in df.iterrows():
            rtype = str(row["radar_type"]).strip()
            elevel = str(row["error_level"]).strip()
            val = float(row[val_col]) if val_col in row and pd.notnull(row[val_col]) else np.nan
            data[mid][(rtype, elevel)] = val
    return data


def plot_master_bars(data):
    """Plot 1: 6-Panel Grouped Bar Chart for PRI MAE (5 Radars + Macro Average)."""
    fig, axes = plt.subplots(2, 3, figsize=(21, 12))
    axes = axes.flatten()

    num_models = len(MODEL_CONFIGS)
    x = np.arange(len(ERROR_LEVELS))
    bar_width = 0.85 / num_models

    for idx, rtype in enumerate(RADAR_TYPES):
        ax = axes[idx]
        for m_idx, m in enumerate(MODEL_CONFIGS):
            mid = m["id"]
            vals = [data[mid].get((rtype, elevel), np.nan) for elevel in ERROR_LEVELS]
            offset = (m_idx - (num_models - 1) / 2) * bar_width
            ax.bar(
                x + offset,
                vals,
                width=bar_width,
                label=m["label"] if idx == 0 else "",
                color=m["color"],
                alpha=0.92,
                edgecolor="white",
                linewidth=0.5,
            )

        ax.set_title(f"({chr(97+idx)}) {RADAR_TITLES[rtype]}", fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(ERROR_LABELS)
        ax.set_ylabel("PRI MAE (μs)")
        ax.set_yscale("log")
        ax.set_ylim(bottom=0.005, top=250.0)
        ax.grid(True, which="both", axis="y", linestyle="--", alpha=0.5)

    # 6th Panel: Macro Average Across All Radar Types
    ax_macro = axes[5]
    for m_idx, m in enumerate(MODEL_CONFIGS):
        mid = m["id"]
        avg_vals = []
        for elevel in ERROR_LEVELS:
            r_vals = [data[mid].get((r, elevel), np.nan) for r in RADAR_TYPES]
            avg_vals.append(np.nanmean(r_vals))
        offset = (m_idx - (num_models - 1) / 2) * bar_width
        ax_macro.bar(
            x + offset,
            avg_vals,
            width=bar_width,
            color=m["color"],
            alpha=0.92,
            edgecolor="white",
            linewidth=0.5,
        )

    ax_macro.set_title("(f) Macro Average (All 5 Radar Profiles)", fontweight="bold")
    ax_macro.set_xticks(x)
    ax_macro.set_xticklabels(ERROR_LABELS)
    ax_macro.set_ylabel("Macro Mean PRI MAE (μs)")
    ax_macro.set_yscale("log")
    ax_macro.set_ylim(bottom=0.005, top=250.0)
    ax_macro.grid(True, which="both", axis="y", linestyle="--", alpha=0.5)

    # Global Legend and Title
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.98),
        ncol=5,
        frameon=True,
        facecolor="#f9f9f9",
        edgecolor="#cccccc",
        fontsize=10,
    )

    fig.suptitle(
        "PULSAR Master Benchmark: PRI Forecast Error across EW Modulation Profiles & Noise Regimes",
        fontsize=16,
        fontweight="bold",
        y=1.02,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    out_path = COMPARISON_DIR / "master_benchmark_pri_bars.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[SAVED] {out_path}")


def plot_degradation_curves(data):
    """Plot 2: 6-Panel Noise Degradation Curves (Clean -> Lv3)."""
    fig, axes = plt.subplots(2, 3, figsize=(21, 12))
    axes = axes.flatten()

    x = np.arange(len(ERROR_LEVELS))

    for idx, rtype in enumerate(RADAR_TYPES):
        ax = axes[idx]
        for m in MODEL_CONFIGS:
            mid = m["id"]
            vals = [data[mid].get((rtype, elevel), np.nan) for elevel in ERROR_LEVELS]
            linestyle = "--" if "Classic" in m["label"] else "-"
            linewidth = 2.2 if "LoRA" in m["label"] else 1.6
            ax.plot(
                x,
                vals,
                marker=m["marker"],
                markersize=6.5,
                label=m["label"] if idx == 0 else "",
                color=m["color"],
                linestyle=linestyle,
                linewidth=linewidth,
                alpha=0.9,
            )

        ax.set_title(f"({chr(97+idx)}) {RADAR_TITLES[rtype]}", fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(ERROR_LABELS)
        ax.set_ylabel("PRI MAE (μs)")
        ax.grid(True, linestyle="--", alpha=0.6)

    # 6th Panel: Macro Average Curves
    ax_macro = axes[5]
    for m in MODEL_CONFIGS:
        mid = m["id"]
        avg_vals = []
        for elevel in ERROR_LEVELS:
            r_vals = [data[mid].get((r, elevel), np.nan) for r in RADAR_TYPES]
            avg_vals.append(np.nanmean(r_vals))
        linestyle = "--" if "Classic" in m["label"] else "-"
        linewidth = 2.4 if "LoRA" in m["label"] else 1.7
        ax_macro.plot(
            x,
            avg_vals,
            marker=m["marker"],
            markersize=7,
            color=m["color"],
            linestyle=linestyle,
            linewidth=linewidth,
            alpha=0.9,
        )

    ax_macro.set_title("(f) Macro Noise Degradation Slope", fontweight="bold")
    ax_macro.set_xticks(x)
    ax_macro.set_xticklabels(ERROR_LABELS)
    ax_macro.set_ylabel("Macro Mean PRI MAE (μs)")
    ax_macro.grid(True, linestyle="--", alpha=0.6)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.98),
        ncol=5,
        frameon=True,
        facecolor="#f9f9f9",
        edgecolor="#cccccc",
        fontsize=10,
    )

    fig.suptitle(
        "PULSAR Noise Robustness: Error Growth Trajectories from Clean to Severe Corruptions",
        fontsize=16,
        fontweight="bold",
        y=1.02,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.94])

    out_path = COMPARISON_DIR / "noise_degradation_curves.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[SAVED] {out_path}")


def plot_auxiliary_rf_aoa():
    """Plot 3: Carrier Frequency (RF) and Angle of Arrival (AOA) Performance."""
    fig, (ax_rf, ax_aoa) = plt.subplots(1, 2, figsize=(18, 6.5))

    # 1. RF (MHz) Data
    rf_zs_path = RESULTS_ROOT / "timesfm" / "zero_shot" / "univariate_fixed" / "frequency" / "metrics.csv"
    rf_lora_path = RESULTS_ROOT / "timesfm" / "lora_sft" / "univariate_fixed" / "frequency" / "metrics.csv"

    # 2. AOA (deg) Data
    aoa_zs_path = RESULTS_ROOT / "timesfm" / "zero_shot" / "univariate_fixed" / "aoa" / "metrics.csv"
    aoa_lora_path = RESULTS_ROOT / "timesfm" / "lora_sft" / "univariate_fixed" / "aoa" / "metrics.csv"

    radar_abbrevs = ["Stable", "Jitter", "Stagger", "Dwell&Sw", "Sliding"]
    x = np.arange(len(RADAR_TYPES))
    width = 0.38

    if rf_zs_path.exists() and rf_lora_path.exists():
        df_rf_zs = pd.read_csv(rf_zs_path)
        df_rf_lora = pd.read_csv(rf_lora_path)
        rf_col_zs = [c for c in df_rf_zs.columns if c.lower() == "mae_mhz"][0]
        rf_col_lora = [c for c in df_rf_lora.columns if c.lower() == "mae_mhz"][0]

        # Average across error levels for each radar type
        rf_zs_means = [df_rf_zs[df_rf_zs["radar_type"] == r][rf_col_zs].mean() for r in RADAR_TYPES]
        rf_lora_means = [df_rf_lora[df_rf_lora["radar_type"] == r][rf_col_lora].mean() for r in RADAR_TYPES]

        ax_rf.bar(x - width/2, rf_zs_means, width, label="TimesFM 3.0 (Zero-Shot)", color="#4285F4", alpha=0.9, edgecolor="white")
        ax_rf.bar(x + width/2, rf_lora_means, width, label="TimesFM 3.0 (LoRA SFT)", color="#0F9D58", alpha=0.9, edgecolor="white")

        # Tolerance reference line (±2 MHz)
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

        aoa_zs_means = [df_aoa_zs[df_aoa_zs["radar_type"] == r]["mae_deg"].mean() for r in RADAR_TYPES]
        aoa_lora_means = [df_aoa_lora[df_aoa_lora["radar_type"] == r]["mae_deg"].mean() for r in RADAR_TYPES]

        ax_aoa.bar(x - width/2, aoa_zs_means, width, label="TimesFM 3.0 (Zero-Shot)", color="#4285F4", alpha=0.9, edgecolor="white")
        ax_aoa.bar(x + width/2, aoa_lora_means, width, label="TimesFM 3.0 (LoRA SFT)", color="#0F9D58", alpha=0.9, edgecolor="white")

        # Tolerance reference line (±2.0 deg)
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
    """Plot 4: Univariate vs. 5-Channel Multivariate Joint Forecasting."""
    fig, (ax_tfm, ax_chr) = plt.subplots(1, 2, figsize=(18, 6.5))

    tfm_uni_path = RESULTS_ROOT / "timesfm" / "lora_sft" / "univariate_fixed" / "pri" / "metrics.csv"
    tfm_mv_path = RESULTS_ROOT / "timesfm" / "lora_sft" / "multivariate_fixed" / "metrics.csv"

    chr_uni_path = RESULTS_ROOT / "chronos2" / "lora_sft" / "univariate_fixed" / "pri" / "metrics.csv"
    chr_mv_path = RESULTS_ROOT / "chronos2" / "lora_sft" / "multivariate_fixed" / "metrics.csv"

    x = np.arange(len(ERROR_LEVELS))
    width = 0.35

    # Panel 1: TimesFM Univariate vs Multivariate
    if tfm_uni_path.exists() and tfm_mv_path.exists():
        df_uni = pd.read_csv(tfm_uni_path)
        df_mv = pd.read_csv(tfm_mv_path)

        uni_means = [df_uni[df_uni["error_level"] == e]["mae_us"].mean() for e in ERROR_LEVELS]
        mv_means = [df_mv[df_mv["error_level"] == e]["mae_pri"].mean() for e in ERROR_LEVELS]

        ax_tfm.bar(x - width/2, uni_means, width, label="Univariate PRI (Delta-TOA only)", color="#0F9D58", alpha=0.85, edgecolor="white")
        ax_tfm.bar(x + width/2, mv_means, width, label="Multivariate 5-Channel (Joint)", color="#202124", alpha=0.85, edgecolor="white")

        # Highlight temporal anchoring margin
        for i in range(len(ERROR_LEVELS)):
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

    # Panel 2: Chronos-2 Univariate vs Multivariate
    if chr_uni_path.exists() and chr_mv_path.exists():
        df_chr_uni = pd.read_csv(chr_uni_path)
        df_chr_mv = pd.read_csv(chr_mv_path)

        chr_uni_means = [df_chr_uni[df_chr_uni["error_level"] == e]["mae"].mean() for e in ERROR_LEVELS]
        chr_mv_means = [df_chr_mv[df_chr_mv["error_level"] == e]["mae_pri"].mean() for e in ERROR_LEVELS]

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
    print("[1/4] Loading PRI metric matrices...")
    data = load_model_pri_data()

    print("[2/4] Generating master benchmark bar chart...")
    plot_master_bars(data)

    print("[3/4] Generating noise degradation curves...")
    plot_degradation_curves(data)

    print("[4/4] Generating auxiliary & multivariate comparison figures...")
    plot_auxiliary_rf_aoa()
    plot_univariate_vs_multivariate()

    print("\n[SUCCESS] Master comparison visualization suite generated successfully.")


if __name__ == "__main__":
    main()
