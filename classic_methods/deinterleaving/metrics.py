"""Evaluation metrics for pulse deinterleaving and track association.

Provides standard EW cluster quality metrics:
- Cluster Purity (Weighted)
- Homogeneity, Completeness, and V-Measure
- Adjusted Rand Index (ARI) and Normalized Mutual Information (NMI)
- Emitter Track Recovery Yield (Detection of all unique emitters)
- False Pulse Association Rate (Contamination within emitter tracks)
- Missing Pulse Rate
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from sklearn.metrics import (
    homogeneity_completeness_v_measure,
    adjusted_rand_score,
    normalized_mutual_info_score,
)


@dataclass
class DeinterleavingResult:
    """Summary of deinterleaving performance on a sequence or dataset."""
    cluster_purity: float
    v_measure: float
    homogeneity: float
    completeness: float
    ari: float
    nmi: float
    noise_ratio: float
    emitter_count_true: int
    emitter_count_pred: int
    track_recovery_yield: float  # Fraction of true emitters successfully isolated
    false_association_rate: float # Contamination rate in valid tracks
    latency_ms: float
    cluster_details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_purity": round(self.cluster_purity * 100.0, 2),
            "v_measure": round(self.v_measure * 100.0, 2),
            "homogeneity": round(self.homogeneity * 100.0, 2),
            "completeness": round(self.completeness * 100.0, 2),
            "ari": round(self.ari * 100.0, 2),
            "nmi": round(self.nmi * 100.0, 2),
            "noise_ratio": round(self.noise_ratio * 100.0, 2),
            "emitters_true": self.emitter_count_true,
            "emitters_pred": self.emitter_count_pred,
            "track_recovery_yield": round(self.track_recovery_yield * 100.0, 2),
            "false_association_rate": round(self.false_association_rate * 100.0, 2),
            "latency_ms": round(self.latency_ms, 3),
        }


def evaluate_clustering_quality(
    ground_truth_labels: np.ndarray,
    predicted_labels: np.ndarray,
    latency_ms: float = 0.0,
) -> DeinterleavingResult:
    """Computes comprehensive EW deinterleaving metrics comparing predicted tracks to true Radar IDs.
    
    Args:
        ground_truth_labels: Array of true emitter labels (e.g. ['R_STABLE', 'R_JITTER', ...]).
        predicted_labels: Array of cluster IDs (integers, -1 indicates noise/unassigned).
        latency_ms: Execution runtime in milliseconds.
    """
    ground_truth_labels = np.asarray(ground_truth_labels)
    predicted_labels = np.asarray(predicted_labels)
    n_total = len(ground_truth_labels)

    if n_total == 0:
        return DeinterleavingResult(
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0.0, 0.0, latency_ms, {}
        )

    # Convert string labels to unique integers for sklearn metrics
    unique_true, true_int_labels = np.unique(ground_truth_labels, return_inverse=True)
    n_emitters_true = len(unique_true)

    # Separate non-noise pulses for clustering metrics
    valid_mask = predicted_labels >= 0
    n_valid = int(np.sum(valid_mask))
    n_noise = n_total - n_valid
    noise_ratio = n_noise / n_total

    # Unique predicted valid clusters
    unique_pred = np.unique(predicted_labels[valid_mask]) if n_valid > 0 else np.array([])
    n_emitters_pred = len(unique_pred)

    if n_valid == 0:
        # All pulses dropped / marked as noise
        return DeinterleavingResult(
            cluster_purity=0.0,
            v_measure=0.0,
            homogeneity=0.0,
            completeness=0.0,
            ari=0.0,
            nmi=0.0,
            noise_ratio=1.0,
            emitter_count_true=n_emitters_true,
            emitter_count_pred=0,
            track_recovery_yield=0.0,
            false_association_rate=0.0,
            latency_ms=latency_ms,
            cluster_details={},
        )

    # Standard Sklearn metrics on valid pulses
    homo, comp, v_meas = homogeneity_completeness_v_measure(
        true_int_labels[valid_mask], predicted_labels[valid_mask]
    )
    ari = adjusted_rand_score(true_int_labels, predicted_labels)
    nmi = normalized_mutual_info_score(true_int_labels[valid_mask], predicted_labels[valid_mask])

    # 1. Cluster Purity Calculation
    # Purity_c = max_j |C_c \cap Radar_j| / |C_c|
    cluster_details = {}
    weighted_purity_sum = 0.0
    total_false_pulses = 0

    # Map each cluster to its dominant emitter
    cluster_to_dominant = {}
    for c_id in unique_pred:
        c_mask = predicted_labels == c_id
        c_size = int(np.sum(c_mask))
        c_true = ground_truth_labels[c_mask]
        vals, counts = np.unique(c_true, return_counts=True)
        best_idx = int(np.argmax(counts))
        dominant_emitter = vals[best_idx]
        dominant_count = counts[best_idx]
        purity_c = dominant_count / c_size
        
        weighted_purity_sum += dominant_count
        false_pulses = c_size - dominant_count
        total_false_pulses += false_pulses
        
        cluster_to_dominant[c_id] = dominant_emitter
        cluster_details[str(c_id)] = {
            "size": c_size,
            "dominant_emitter": dominant_emitter,
            "dominant_count": int(dominant_count),
            "purity": float(purity_c),
            "false_pulses": int(false_pulses),
        }

    overall_purity = weighted_purity_sum / n_valid if n_valid > 0 else 0.0
    false_association_rate = total_false_pulses / n_valid if n_valid > 0 else 0.0

    # 2. Emitter Track Recovery Yield
    # An emitter is successfully recovered if there is at least one cluster where it is dominant
    # and that cluster contains at least 30% of that emitter's total emitted pulses.
    recovered_emitters = set()
    for e_name in unique_true:
        e_total = np.sum(ground_truth_labels == e_name)
        if e_total == 0:
            continue
        # Find clusters where e_name is dominant
        for c_id, dom_e in cluster_to_dominant.items():
            if dom_e == e_name:
                dom_count = cluster_details[str(c_id)]["dominant_count"]
                if dom_count >= 0.30 * e_total:
                    recovered_emitters.add(e_name)
                    break

    track_recovery_yield = len(recovered_emitters) / n_emitters_true if n_emitters_true > 0 else 0.0

    return DeinterleavingResult(
        cluster_purity=float(overall_purity),
        v_measure=float(v_meas),
        homogeneity=float(homo),
        completeness=float(comp),
        ari=float(ari),
        nmi=float(nmi),
        noise_ratio=float(noise_ratio),
        emitter_count_true=n_emitters_true,
        emitter_count_pred=n_emitters_pred,
        track_recovery_yield=float(track_recovery_yield),
        false_association_rate=float(false_association_rate),
        latency_ms=latency_ms,
        cluster_details=cluster_details,
    )
