"""Cascaded Hybrid Deinterleaver (DBSCAN + SDIF Fallback).

Combines spatial-spectral clustering with temporal difference histogram analysis:
1. Multi-parameter DBSCAN clusters incoming pulses by RF, PW, AOA, and Amplitude.
2. SDIF (Sequential Difference Histogram) inspects each cluster: if multiple PRI modes
   or co-channel frequency collisions are detected, SDIF splits the cluster into sub-tracks.
3. SDIF processes residual unassigned pulses to recover periodic pulse trains.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from .dbscan_deinterleaver import DBSCANDeinterleaver
from .sdif_deinterleaver import SDIFDeinterleaver


class HybridCascadeDeinterleaver:
    """Cascaded hybrid architecture uniting multi-parameter clustering with SDIF temporal deinterleaving."""

    def __init__(
        self,
        dbscan_eps: float = 2.0,
        dbscan_min_samples: int = 8,
        sdif_max_order: int = 4,
        sdif_threshold_factor: float = 0.015,
        sdif_min_pulses: int = 8,
        use_amplitude: bool = True,
    ):
        self.dbscan = DBSCANDeinterleaver(
            eps=dbscan_eps,
            min_samples=dbscan_min_samples,
            include_amplitude=use_amplitude,
        )
        self.sdif = SDIFDeinterleaver(
            max_order=sdif_max_order,
            threshold_factor=sdif_threshold_factor,
            min_pulses_per_train=sdif_min_pulses,
        )

    def deinterleave(
        self, df_pulses: pd.DataFrame
    ) -> Tuple[np.ndarray, Dict[int, pd.DataFrame], float]:
        """Runs the two-stage cascaded deinterleaving pipeline."""
        if df_pulses.empty:
            return np.array([]), {}, 0.0

        t0 = time.perf_counter()

        # Step 1: Spatial-Spectral DBSCAN
        db_labels, db_tracks, _ = self.dbscan.deinterleave(df_pulses)
        
        n_pulses = len(df_pulses)
        final_labels = np.full(n_pulses, -1, dtype=int)
        next_track_id = 0

        # Step 2: Validate each DBSCAN cluster with SDIF if complex/overcrowded
        for c_id, track_df in db_tracks.items():
            cluster_indices = df_pulses.index[db_labels == c_id].to_numpy()
            
            # Check if this cluster has signs of multi-emitter collision (e.g. >200 pulses in a 5-radar scenario)
            if len(track_df) > 180:
                sub_labels, sub_tracks, _ = self.sdif.deinterleave(track_df)
                unique_sub = np.unique(sub_labels[sub_labels >= 0])
                if len(unique_sub) > 1:
                    # Successfully split co-channel collision!
                    for s_id in unique_sub:
                        sub_mask = cluster_indices[sub_labels == s_id]
                        final_labels[sub_mask] = next_track_id
                        next_track_id += 1
                    continue

            # Standard clean single-emitter cluster
            final_labels[cluster_indices] = next_track_id
            next_track_id += 1

        # Step 3: Check residual noise pulses with SDIF
        residual_mask = final_labels == -1
        if np.sum(residual_mask) >= self.sdif.min_pulses_per_train:
            res_df = df_pulses[residual_mask].copy()
            res_indices = df_pulses.index[residual_mask].to_numpy()
            sub_labels, sub_tracks, _ = self.sdif.deinterleave(res_df)
            unique_sub = np.unique(sub_labels[sub_labels >= 0])
            for s_id in unique_sub:
                sub_mask = res_indices[sub_labels == s_id]
                final_labels[sub_mask] = next_track_id
                next_track_id += 1

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        # Build final tracks dictionary
        tracks = {}
        for trk_id in range(next_track_id):
            mask = final_labels == trk_id
            if np.sum(mask) == 0:
                continue
            trk_df = df_pulses[mask].copy().sort_values(by="TOA").reset_index(drop=True)
            t_vals = trk_df["TOA"].to_numpy()
            intra_pri = np.concatenate([[t_vals[1] - t_vals[0]], np.diff(t_vals)]) if len(t_vals) > 1 else np.array([0.0])
            trk_df["Intra_Track_PRI"] = intra_pri
            tracks[trk_id] = trk_df

        return final_labels, tracks, elapsed_ms
