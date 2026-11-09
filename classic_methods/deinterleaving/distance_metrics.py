"""EW Domain-Specific Distance Metrics and Feature Scaling.

Transforms raw PDW features (RF, PW, AOA, AMP) into an EW-calibrated Euclidean space
where 1 unit of distance corresponds to 1 standard measurement resolution boundary.
Handles circular angle-of-arrival (AOA) wrapping naturally in O(N) using trigonometric projection.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple


DEFAULT_EW_SCALES: Dict[str, float] = {
    "rf_mhz": 60.0,      # Carrier frequency tolerance (~60 MHz radar agility bandwidth)
    "pw_us": 0.35,       # Pulse width tolerance (~0.35 us pulse shape jitter)
    "aoa_deg": 4.0,      # Angle of arrival tolerance (~4.0 deg interferometer resolution)
    "amp_dbm": 8.0,      # Amplitude tolerance (~8 dBm RSSI variation)
}


def circular_angle_diff(a1: np.ndarray, a2: np.ndarray) -> np.ndarray:
    """Computes minimal angular difference in degrees across 0-360 deg wrap."""
    diff = np.abs(a1 - a2) % 360.0
    return np.minimum(diff, 360.0 - diff)


def ew_feature_transform(
    df_or_pdw: pd.DataFrame | np.ndarray,
    scales: Optional[Dict[str, float]] = None,
    include_amplitude: bool = False,
    feature_weights: Optional[Dict[str, float]] = None,
) -> np.ndarray:
    """Transforms raw PDWs into a normalized EW feature space suitable for Euclidean KD-Tree / DBSCAN.
    
    Features produced:
      1. Normalized RF: rf / (scale_rf / weight_rf)
      2. Normalized PW: pw / (scale_pw / weight_pw)
      3. AOA Cosine component: R * cos(theta_rad)
      4. AOA Sine component:   R * sin(theta_rad)
         where R = (180 / (pi * scale_aoa)) * weight_aoa
      5. (Optional) Normalized AMP: amp / (scale_amp / weight_amp)
      
    Args:
        df_or_pdw: DataFrame containing ['Frequency', 'PW', 'AOA', ('Amplitude')] or (N, 4/5) ndarray.
        scales: Mapping of feature names to physical tolerances.
        include_amplitude: Whether to include amplitude (useful if stable, omit if antenna scanning).
        feature_weights: Multiplicative relative importance weight for each feature (default 1.0).
        
    Returns:
        np.ndarray of shape (N, D) where Euclidean distance matches EW sensor uncertainty units.
    """
    sc = dict(DEFAULT_EW_SCALES)
    if scales:
        sc.update(scales)
        
    w = {"rf": 1.0, "pw": 1.0, "aoa": 1.0, "amp": 0.5}
    if feature_weights:
        w.update(feature_weights)

    if isinstance(df_or_pdw, pd.DataFrame):
        rf = df_or_pdw["Frequency"].to_numpy(dtype=np.float64)
        pw = df_or_pdw["PW"].to_numpy(dtype=np.float64)
        aoa = df_or_pdw["AOA"].to_numpy(dtype=np.float64)
        amp = df_or_pdw["Amplitude"].to_numpy(dtype=np.float64) if "Amplitude" in df_or_pdw.columns else None
    else:
        arr = np.asarray(df_or_pdw, dtype=np.float64)
        # Expected column ordering if ndarray: [TOA, Frequency, PW, Amplitude, AOA] or [Frequency, PW, AOA]
        if arr.shape[1] >= 5:
            rf = arr[:, 1]
            pw = arr[:, 2]
            amp = arr[:, 3]
            aoa = arr[:, 4]
        elif arr.shape[1] == 3:
            rf = arr[:, 0]
            pw = arr[:, 1]
            aoa = arr[:, 2]
            amp = None
        else:
            raise ValueError(f"Unrecognized ndarray shape: {arr.shape}")

    # 1. Scaled RF
    norm_rf = (rf / sc["rf_mhz"]) * w["rf"]
    
    # 2. Scaled PW
    norm_pw = (pw / sc["pw_us"]) * w["pw"]
    
    # 3. Circular AOA Projection
    # Chord length 2*sin(dtheta/2) approximates arc length dtheta in radians for small angles.
    # Radius R = (1 / sigma_rad) = 180 / (pi * sigma_deg)
    aoa_rad = np.radians(aoa % 360.0)
    radius = (180.0 / (np.pi * sc["aoa_deg"])) * w["aoa"]
    norm_aoa_x = radius * np.cos(aoa_rad)
    norm_aoa_y = radius * np.sin(aoa_rad)

    feature_cols = [norm_rf[:, None], norm_pw[:, None], norm_aoa_x[:, None], norm_aoa_y[:, None]]
    
    if include_amplitude and amp is not None:
        norm_amp = (amp / sc["amp_dbm"]) * w["amp"]
        feature_cols.append(norm_amp[:, None])

    return np.hstack(feature_cols)


def compute_ew_distance_matrix(
    pdw_features: pd.DataFrame,
    scales: Optional[Dict[str, float]] = None,
    include_amplitude: bool = False,
) -> np.ndarray:
    """Computes exact pairwise EW distance matrix between all PDWs in a sequence."""
    X = ew_feature_transform(pdw_features, scales=scales, include_amplitude=include_amplitude)
    # Euclidean distance in transformed space
    diff = X[:, np.newaxis, :] - X[np.newaxis, :, :]
    return np.sqrt(np.sum(diff ** 2, axis=-1))
