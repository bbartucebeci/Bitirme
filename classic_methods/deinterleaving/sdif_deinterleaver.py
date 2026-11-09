"""Sequential Difference Histogram (SDIF) / PRI Transform Deinterleaver.

Separates interleaved pulse trains based on TOA differences when spatial/spectral
parameters (RF, PW, AOA) are identical, overlapping, or noisy.
Implements multi-order TOA difference histograms, dynamic exponential thresholding,
and sequential pulse train extraction.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple, Set
import numpy as np
import pandas as pd


class SDIFDeinterleaver:
    """Sequential Difference Histogram (SDIF) deinterleaver for TOA-based emitter separation."""

    def __init__(
        self,
        max_order: int = 4,
        pri_min_us: float = 200.0,
        pri_max_us: float = 2500.0,
        bin_width_us: float = 2.0,
        threshold_factor: float = 0.015,
        min_pulses_per_train: int = 8,
        match_tolerance_us: float = 5.0,
    ):
        """
        Args:
            max_order: Maximum difference order (k = 1..max_order).
            pri_min_us: Minimum PRI to search (us).
            pri_max_us: Maximum PRI to search (us).
            bin_width_us: Histogram bin width (us).
            threshold_factor: Multiplier 'x' for dynamic threshold curve.
            min_pulses_per_train: Minimum confirmed pulses to extract a pulse train.
            match_tolerance_us: Tolerance gate for pulse association during sequential search.
        """
        self.max_order = max_order
        self.pri_min_us = pri_min_us
        self.pri_max_us = pri_max_us
        self.bin_width_us = bin_width_us
        self.threshold_factor = threshold_factor
        self.min_pulses_per_train = min_pulses_per_train
        self.match_tolerance_us = match_tolerance_us

    def compute_sdif_histogram(
        self, toas: np.ndarray, order: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Computes k-th order difference histogram and dynamic threshold curve."""
        N = len(toas)
        if N <= order:
            return np.array([]), np.array([]), np.array([])

        diffs = toas[order:] - toas[:-order]
        mask = (diffs >= self.pri_min_us) & (diffs <= self.pri_max_us)
        valid_diffs = diffs[mask]

        bins = np.arange(self.pri_min_us, self.pri_max_us + self.bin_width_us, self.bin_width_us)
        hist, bin_edges = np.histogram(valid_diffs, bins=bins)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

        # Dynamic exponential threshold curve (Mardia model):
        # T(tau) = x * (N - k) * exp(-tau / (k * B))
        # where B = total time span
        total_time = max(toas[-1] - toas[0], 1.0)
        B = total_time / max(N, 1)
        decay = np.clip(bin_centers / (order * B * 5.0), 0.0, 50.0)
        threshold = self.threshold_factor * (N - order) * np.exp(-decay)
        # Ensure a minimum baseline threshold
        threshold = np.maximum(threshold, 2.0)

        return bin_centers, hist, threshold

    def extract_pulse_train(
        self, toas: np.ndarray, active_indices: np.ndarray, pri_estimate: float
    ) -> np.ndarray:
        """Extracts a pulse train with regular or harmonic PRI intervals."""
        active_toas = toas[active_indices]
        N = len(active_toas)
        if N < self.min_pulses_per_train:
            return np.array([], dtype=int)

        best_chain: List[int] = []

        # Iterate over possible anchor pulses
        for i in range(min(N - self.min_pulses_per_train + 1, 20)):
            anchor_idx = active_indices[i]
            anchor_toa = toas[anchor_idx]
            chain = [anchor_idx]
            last_toa = anchor_toa

            for j in range(i + 1, N):
                curr_idx = active_indices[j]
                curr_toa = toas[curr_idx]
                delta = curr_toa - last_toa

                # Check if delta is an integer multiple of PRI estimate (allowing for 1-2 dropped pulses)
                m = round(delta / pri_estimate)
                if 1 <= m <= 4:
                    err = abs(delta - m * pri_estimate)
                    if err <= self.match_tolerance_us * m:
                        chain.append(curr_idx)
                        last_toa = curr_toa

            if len(chain) > len(best_chain):
                best_chain = chain

        if len(best_chain) >= self.min_pulses_per_train:
            return np.array(best_chain, dtype=int)
        return np.array([], dtype=int)

    def deinterleave(
        self, df_pulses: pd.DataFrame
    ) -> Tuple[np.ndarray, Dict[int, pd.DataFrame], float]:
        """Runs SDIF algorithm to separate pulses into tracks by PRI periodicity.
        
        Returns:
            labels: Pulse cluster IDs (-1 for residual).
            tracks: Dict mapping track_id -> DataFrame of pulses.
            elapsed_ms: Execution time in milliseconds.
        """
        if df_pulses.empty:
            return np.array([]), {}, 0.0

        t0 = time.perf_counter()
        toas = df_pulses["TOA"].to_numpy(dtype=np.float64)
        n_pulses = len(toas)
        labels = np.full(n_pulses, -1, dtype=int)
        unassigned_mask = np.ones(n_pulses, dtype=bool)

        current_track_id = 0

        # Iteratively extract pulse trains across difference orders
        for order in range(1, self.max_order + 1):
            if np.sum(unassigned_mask) < self.min_pulses_per_train:
                break

            active_indices = np.where(unassigned_mask)[0]
            bin_centers, hist, threshold = self.compute_sdif_histogram(toas[active_indices], order)

            if len(hist) == 0:
                continue

            # Detect peaks exceeding threshold
            peak_mask = hist > threshold
            if not np.any(peak_mask):
                continue

            peak_indices = np.where(peak_mask)[0]
            # Sort peaks by prominence (hist - threshold)
            prominences = hist[peak_indices] - threshold[peak_indices]
            sorted_peak_indices = peak_indices[np.argsort(-prominences)]

            for p_idx in sorted_peak_indices:
                candidate_pri = bin_centers[p_idx] / order
                active_indices = np.where(unassigned_mask)[0]
                if len(active_indices) < self.min_pulses_per_train:
                    break

                train_indices = self.extract_pulse_train(toas, active_indices, candidate_pri)
                if len(train_indices) >= self.min_pulses_per_train:
                    labels[train_indices] = current_track_id
                    unassigned_mask[train_indices] = False
                    current_track_id += 1

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        # Build tracks dictionary
        tracks = {}
        for c_id in range(current_track_id):
            mask = labels == c_id
            track_df = df_pulses[mask].copy().sort_values(by="TOA").reset_index(drop=True)
            t_vals = track_df["TOA"].to_numpy()
            intra_pri = np.concatenate([[t_vals[1] - t_vals[0]], np.diff(t_vals)]) if len(t_vals) > 1 else np.array([0.0])
            track_df["Intra_Track_PRI"] = intra_pri
            tracks[c_id] = track_df

        return labels, tracks, elapsed_ms
