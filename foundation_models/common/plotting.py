"""Diagnostic plotting routines for electronic warfare pulse forecasts."""

from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


def save_forecast_plot(
    plot_path: Path,
    title: str,
    context: np.ndarray,
    ground_truth: np.ndarray,
    predictions: np.ndarray,
    tolerance: float = 10.0,
    param_label: str = "PRI",
    unit: str = "μs",
    show_ctx_pts: int = 40,
    tolerance_us: float | None = None,
):
    """Renders and saves a diagnostic parameter forecast plot.

    Includes:
    - Observed context pulses
    - Ground truth future pulses
    - Model forecast curve
    - Tactical Tolerance corridor (+/- tolerance around ground truth)
    - Shaded prediction error gap
    - Protected y-axis span to prevent deceptive auto-zoom on flat signals
    """
    if tolerance_us is not None:
        tolerance = tolerance_us

    context_len = len(context)
    horizon_len = len(ground_truth)

    plt.figure(figsize=(13, 5))

    actual_ctx_pts = min(show_ctx_pts, context_len)
    x_ctx = np.arange(context_len - actual_ctx_pts, context_len)
    x_horiz = np.arange(context_len, context_len + horizon_len)

    # 1. Observed history
    plt.plot(
        x_ctx,
        context[-actual_ctx_pts:],
        "o-",
        color="tab:blue",
        markersize=4,
        label=f"Observed Context ({param_label})",
    )

    # 2. Ground truth
    plt.plot(
        x_horiz,
        ground_truth,
        "s-",
        color="tab:green",
        markersize=4,
        label="Ground Truth (Actual Future)",
    )

    # 3. Model prediction
    plt.plot(
        x_horiz,
        predictions,
        "^--",
        color="tab:red",
        markersize=5,
        label="Model Forecast",
    )

    # 4. Forecast boundary
    plt.axvline(
        x=context_len - 0.5,
        color="black",
        linestyle="--",
        alpha=0.6,
        label="Forecast Horizon Boundary",
    )

    # 5. Tactical Tolerance Corridor (shaded green)
    plt.fill_between(
        x_horiz,
        ground_truth - tolerance,
        ground_truth + tolerance,
        color="tab:green",
        alpha=0.18,
        label=f"Tactical Gate (±{tolerance:g} {unit})",
    )

    # 6. Prediction Error Gap (shaded red)
    plt.fill_between(
        x_horiz,
        ground_truth,
        predictions,
        color="tab:red",
        alpha=0.15,
        label="Prediction Error Gap",
    )

    # Prevent micro-scale auto-zoom illusion on flat signals (e.g. stable radar)
    all_visible = np.concatenate([context[-actual_ctx_pts:], ground_truth, predictions])
    y_min, y_max = float(all_visible.min()), float(all_visible.max())
    min_span = max(tolerance * 3.0, 1.0)
    if (y_max - y_min) < min_span:
        y_center = (y_max + y_min) / 2.0
        plt.ylim(y_center - min_span * 0.6, y_center + min_span * 0.6)

    plt.title(title, fontsize=13, fontweight="bold")
    plt.xlabel("Pulse Index (n)")
    plt.ylabel(f"{param_label} ({unit})")
    plt.legend(loc="upper right", frameon=True)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()

    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=180)
    plt.close()


def save_multivariate_forecast_plot(
    plot_path: Path,
    title: str,
    context_5xN: np.ndarray,
    ground_truth_5xN: np.ndarray,
    predictions_5xN: np.ndarray,
    tolerances: list[float] | None = None,
    param_names: list[str] | None = None,
    units: list[str] | None = None,
    show_ctx_pts: int = 40,
):
    """Renders a synchronized 5-panel tactical dashboard forecast plot.

    Panels:
    1. Pulse Repetition Interval (PRI, us)
    2. Carrier Frequency (RF, MHz)
    3. Pulse Width (PW, us)
    4. Angle of Arrival (AOA, deg)
    5. Received Peak Power (Amplitude, dBm)
    """
    if tolerances is None:
        tolerances = [10.0, 2.0, 0.1, 2.0, 2.0]
    if param_names is None:
        param_names = ["PRI", "Frequency", "PW", "AOA", "Amplitude"]
    if units is None:
        units = ["μs", "MHz", "μs", "°", "dBm"]

    num_channels = context_5xN.shape[0]
    context_len = context_5xN.shape[1]
    horizon_len = ground_truth_5xN.shape[1]

    actual_ctx_pts = min(show_ctx_pts, context_len)
    x_ctx = np.arange(context_len - actual_ctx_pts, context_len)
    x_horiz = np.arange(context_len, context_len + horizon_len)

    fig, axes = plt.subplots(num_channels, 1, figsize=(14, 3.2 * num_channels), sharex=True)
    if num_channels == 1:
        axes = [axes]

    for c in range(num_channels):
        ax = axes[c]
        p_name = param_names[c]
        p_unit = units[c]
        tol = tolerances[c]

        ctx_c = context_5xN[c]
        gt_c = ground_truth_5xN[c]
        pred_c = predictions_5xN[c]

        # 1. Observed Context
        ax.plot(
            x_ctx,
            ctx_c[-actual_ctx_pts:],
            "o-",
            color="tab:blue",
            markersize=3.5,
            linewidth=1.2,
            label="Observed Context" if c == 0 else None,
        )

        # 2. Ground Truth
        ax.plot(
            x_horiz,
            gt_c,
            "s-",
            color="tab:green",
            markersize=3.5,
            linewidth=1.2,
            label="Ground Truth (Emitter)" if c == 0 else None,
        )

        # 3. Model Prediction
        ax.plot(
            x_horiz,
            pred_c,
            "^--",
            color="tab:red",
            markersize=4.0,
            linewidth=1.2,
            label="Multivariate Forecast" if c == 0 else None,
        )

        # 4. Boundary
        ax.axvline(x=context_len - 0.5, color="black", linestyle="--", alpha=0.5)

        # 5. Tactical Tolerance Corridor
        ax.fill_between(
            x_horiz,
            gt_c - tol,
            gt_c + tol,
            color="tab:green",
            alpha=0.18,
            label=f"Tactical Gate (±{tol:g} {p_unit})" if c == 0 else None,
        )

        # 6. Prediction Error Gap
        ax.fill_between(
            x_horiz,
            gt_c,
            pred_c,
            color="tab:red",
            alpha=0.15,
        )

        # Dynamic range guard
        all_vis = np.concatenate([ctx_c[-actual_ctx_pts:], gt_c, pred_c])
        y_min, y_max = float(all_vis.min()), float(all_vis.max())
        min_span = max(tol * 3.0, 1.0)
        if (y_max - y_min) < min_span:
            y_ctr = (y_max + y_min) / 2.0
            ax.set_ylim(y_ctr - min_span * 0.6, y_ctr + min_span * 0.6)

        ax.set_ylabel(f"{p_name} ({p_unit})", fontsize=10, fontweight="bold")
        ax.grid(True, linestyle=":", alpha=0.6)
        if c == 0:
            ax.legend(loc="upper right", frameon=True, fontsize=9)

    axes[-1].set_xlabel("Pulse Index (n)", fontsize=11, fontweight="bold")
    fig.suptitle(title, fontsize=13, fontweight="bold", y=0.995)
    plt.tight_layout()

    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=180, bbox_inches="tight")
    plt.close()


