"""Online Streaming Pulse Deinterleaver (FPGA FIFO Emulation).

Emulates real-time hardware receiver track association:
- Sequential pulse-by-pulse arrival
- Rolling BRAM FIFO buffer (64-128 pulses)
- Gated nearest-track association with running alpha-beta centroid updates
- Automatic track initiation (tentative -> confirmed) and timeout pruning
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from .distance_metrics import DEFAULT_EW_SCALES, circular_angle_diff


class EmitterTrackState:
    """Hardware track state register maintained in receiver memory."""
    def __init__(self, track_id: int, initial_pdw: Dict[str, float]):
        self.track_id = track_id
        self.rf = float(initial_pdw["Frequency"])
        self.pw = float(initial_pdw["PW"])
        self.aoa = float(initial_pdw["AOA"])
        self.amp = float(initial_pdw.get("Amplitude", -50.0))
        self.last_toa = float(initial_pdw["TOA"])
        
        self.pulse_count = 1
        self.confirmed = False
        self.pri_history: List[float] = []
        self.estimated_pri: Optional[float] = None
        self.pulse_indices: List[int] = [int(initial_pdw["pulse_idx"])]

    def update(self, pdw: Dict[str, float], alpha: float = 0.15) -> None:
        """Updates track parameters with an incoming pulse using EW alpha-beta filtering."""
        curr_toa = float(pdw["TOA"])
        delta_toa = curr_toa - self.last_toa
        self.last_toa = curr_toa
        self.pulse_indices.append(int(pdw["pulse_idx"]))
        self.pulse_count += 1

        # Smooth running averages for physical parameters
        self.rf = (1.0 - alpha) * self.rf + alpha * float(pdw["Frequency"])
        self.pw = (1.0 - alpha) * self.pw + alpha * float(pdw["PW"])
        
        # Circular AOA update
        aoa_diff = (float(pdw["AOA"]) - self.aoa + 180.0) % 360.0 - 180.0
        self.aoa = (self.aoa + alpha * aoa_diff) % 360.0

        if "Amplitude" in pdw:
            self.amp = (1.0 - alpha) * self.amp + alpha * float(pdw["Amplitude"])

        # Track PRI history
        if delta_toa > 0:
            self.pri_history.append(delta_toa)
            if len(self.pri_history) > 10:
                self.pri_history.pop(0)
            self.estimated_pri = float(np.median(self.pri_history))

        if self.pulse_count >= 5:
            self.confirmed = True


class OnlineStreamDeinterleaver:
    """Simulates real-time FPGA streaming track association over an asynchronous PDW stream."""

    def __init__(
        self,
        gate_threshold: float = 2.5,
        alpha: float = 0.15,
        min_confirm_pulses: int = 5,
        timeout_us: float = 50000.0,
        scales: Optional[Dict[str, float]] = None,
        use_amplitude: bool = True,
    ):
        """
        Args:
            gate_threshold: Maximum normalized EW distance to associate a pulse to an existing track.
            alpha: Alpha smoothing coefficient for online parameter tracking.
            min_confirm_pulses: Pulses required to promote tentative track to confirmed.
            timeout_us: Inactive duration after which a track is retired.
            scales: Physical measurement resolutions.
        """
        self.gate_threshold = gate_threshold
        self.alpha = alpha
        self.min_confirm_pulses = min_confirm_pulses
        self.timeout_us = timeout_us
        self.scales = scales or DEFAULT_EW_SCALES
        self.use_amplitude = use_amplitude

    def _compute_gate_distance(self, pdw: Dict[str, float], track: EmitterTrackState) -> float:
        """Computes normalized EW Euclidean distance from a single PDW to a track state."""
        d_rf = (float(pdw["Frequency"]) - track.rf) / self.scales["rf_mhz"]
        d_pw = (float(pdw["PW"]) - track.pw) / self.scales["pw_us"]
        
        ang_diff = circular_angle_diff(np.array([float(pdw["AOA"])]), np.array([track.aoa]))[0]
        d_aoa = ang_diff / self.scales["aoa_deg"]

        dist_sq = d_rf ** 2 + d_pw ** 2 + d_aoa ** 2

        if self.use_amplitude and "Amplitude" in pdw:
            d_amp = (float(pdw["Amplitude"]) - track.amp) / self.scales["amp_dbm"]
            dist_sq += (0.5 * d_amp) ** 2

        return float(np.sqrt(dist_sq))

    def deinterleave(
        self, df_pulses: pd.DataFrame
    ) -> Tuple[np.ndarray, Dict[int, pd.DataFrame], float]:
        """Processes pulses sequentially, assigning each to an emitter track in real time."""
        if df_pulses.empty:
            return np.array([]), {}, 0.0

        t0 = time.perf_counter()

        # Ensure pulses are ordered by TOA as they would be at the receiver antenna
        df_sorted = df_pulses.sort_values(by="TOA").reset_index()
        original_indices = df_sorted["index"].to_numpy()
        n_pulses = len(df_sorted)

        active_tracks: List[EmitterTrackState] = []
        retired_tracks: List[EmitterTrackState] = []
        track_counter = 0

        # Assigned track ID per pulse in sorted order
        assigned_tracks = np.full(n_pulses, -1, dtype=int)

        # Pulse-by-pulse sequential processing
        for i, row in df_sorted.iterrows():
            pdw = {
                "TOA": row["TOA"],
                "Frequency": row["Frequency"],
                "PW": row["PW"],
                "AOA": row["AOA"],
                "Amplitude": row.get("Amplitude", -50.0),
                "pulse_idx": i,
            }

            curr_toa = pdw["TOA"]

            # 1. Prune timed-out active tracks
            still_active = []
            for trk in active_tracks:
                if (curr_toa - trk.last_toa) > self.timeout_us:
                    retired_tracks.append(trk)
                else:
                    still_active.append(trk)
            active_tracks = still_active

            # 2. Find best matching track within gate
            best_track: Optional[EmitterTrackState] = None
            best_dist = float("inf")

            for trk in active_tracks:
                dist = self._compute_gate_distance(pdw, trk)
                if dist < self.gate_threshold and dist < best_dist:
                    best_dist = dist
                    best_track = trk

            # 3. Association or Track Initiation
            if best_track is not None:
                best_track.update(pdw, alpha=self.alpha)
                assigned_tracks[i] = best_track.track_id
            else:
                # Initiate tentative track
                new_trk = EmitterTrackState(track_counter, pdw)
                active_tracks.append(new_trk)
                assigned_tracks[i] = track_counter
                track_counter += 1

        all_tracks = active_tracks + retired_tracks
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        # Re-map assigned_tracks back to original DataFrame order
        labels = np.full(n_pulses, -1, dtype=int)
        labels[original_indices] = assigned_tracks

        # Construct tracks dictionary
        tracks = {}
        for trk in all_tracks:
            if trk.pulse_count >= self.min_confirm_pulses:
                mask = labels == trk.track_id
                track_df = df_pulses[mask].copy().sort_values(by="TOA").reset_index(drop=True)
                t_vals = track_df["TOA"].to_numpy()
                intra_pri = np.concatenate([[t_vals[1] - t_vals[0]], np.diff(t_vals)]) if len(t_vals) > 1 else np.array([0.0])
                track_df["Intra_Track_PRI"] = intra_pri
                tracks[trk.track_id] = track_df

        return labels, tracks, elapsed_ms
