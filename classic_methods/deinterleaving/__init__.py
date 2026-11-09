"""Multi-radar pulse deinterleaving algorithms and evaluation framework.

Includes:
- EW distance metrics with physical sensor resolution scaling
- Multi-parameter DBSCAN deinterleaving (RF, PW, AOA, Amplitude)
- Sequential Difference Histogram (SDIF) for co-channel TOA deinterleaving
- Cascaded Hybrid Deinterleaving (DBSCAN + SDIF Fallback)
- Online FIFO sliding-window streaming deinterleaving (FPGA emulation)
- Deinterleaving evaluation metrics (Purity, V-Measure, ARI, False Association)
"""

from .distance_metrics import ew_feature_transform, compute_ew_distance_matrix
from .dbscan_deinterleaver import DBSCANDeinterleaver
from .sdif_deinterleaver import SDIFDeinterleaver
from .hybrid_cascade_deinterleaver import HybridCascadeDeinterleaver
from .online_stream_deinterleaver import OnlineStreamDeinterleaver
from .metrics import evaluate_clustering_quality, DeinterleavingResult

__all__ = [
    "ew_feature_transform",
    "compute_ew_distance_matrix",
    "DBSCANDeinterleaver",
    "SDIFDeinterleaver",
    "HybridCascadeDeinterleaver",
    "OnlineStreamDeinterleaver",
    "evaluate_clustering_quality",
    "DeinterleavingResult",
]
