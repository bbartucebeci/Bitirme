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

