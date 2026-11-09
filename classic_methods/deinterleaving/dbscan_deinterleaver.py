"""Multi-Parameter DBSCAN Pulse Deinterleaver.

Clusters interleaved pulse streams using domain-calibrated spatial-spectral distance
(RF, PW, AOA, and optionally Amplitude) with circular angle handling.
Extracts individual emitter tracks sorted chronologically by TOA.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

from .distance_metrics import ew_feature_transform, DEFAULT_EW_SCALES


class DBSCANDeinterleaver:
    """Deinterleaver using Density-Based Spatial Clustering of Applications with Noise (DBSCAN)
    in normalized EW sensor tolerance space.
    """

    def __init__(
        self,
        eps: float = 2.0,
        min_samples: int = 8,
        scales: Optional[Dict[str, float]] = None,
        include_amplitude: bool = True,
        feature_weights: Optional[Dict[str, float]] = None,
    ):
        """
        Args:
            eps: Maximum distance in normalized EW units between two samples for one to be considered as in the neighborhood.
            min_samples: The number of samples in a neighborhood for a point to be considered a core point.
            scales: Physical tolerance scaling per feature (RF in MHz, PW in us, AOA in deg, AMP in dBm).
            include_amplitude: Whether to use amplitude in clustering.
            feature_weights: Importance weights per feature.
        """
        self.eps = eps
        self.min_samples = min_samples
        self.scales = scales or DEFAULT_EW_SCALES
        self.include_amplitude = include_amplitude
        self.feature_weights = feature_weights

    def deinterleave(
        self, df_pulses: pd.DataFrame
    ) -> Tuple[np.ndarray, Dict[int, pd.DataFrame], float]:
        """Deinterleaves an interleaved sequence into separate emitter tracks.
        
        Args:
            df_pulses: DataFrame containing ['TOA', 'Frequency', 'PW', 'AOA', ('Amplitude')].
            
        Returns:
            cluster_labels: Array of cluster indices (-1 = unassigned/noise, 0..K-1 = emitter tracks).
            tracks: Dictionary mapping cluster_id -> DataFrame of pulses sorted by TOA.
            elapsed_ms: Clustering computation time in milliseconds.
        """
        if df_pulses.empty:
            return np.array([]), {}, 0.0

        t0 = time.perf_counter()

        # Transform features to normalized Euclidean EW space
        X = ew_feature_transform(
            df_pulses,
            scales=self.scales,
            include_amplitude=self.include_amplitude,
            feature_weights=self.feature_weights,
        )

        # Run DBSCAN
        db = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric="euclidean", n_jobs=-1)
        labels = db.fit_predict(X)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        # Segregate pulses into sorted emitter tracks
        tracks = {}
        unique_clusters = np.unique(labels[labels >= 0])

        for c_id in unique_clusters:
            mask = labels == c_id
            track_df = df_pulses[mask].copy()
            track_df = track_df.sort_values(by="TOA").reset_index(drop=True)
            
            # Compute intra-track PRI (Delta TOA)
            toas = track_df["TOA"].to_numpy()
            if len(toas) > 1:
                intra_pri = np.concatenate([[toas[1] - toas[0]], np.diff(toas)])
            else:
                intra_pri = np.array([0.0])
            track_df["Intra_Track_PRI"] = intra_pri
            
            tracks[int(c_id)] = track_df

        return labels, tracks, elapsed_ms
