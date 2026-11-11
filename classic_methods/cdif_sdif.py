#!/usr/bin/env python3
"""Methods 7 & 8: CDIF and SDIF TOA-difference histograms (frame-period estimators).

EE / Signal Processing Rationale:
---------------------------------
CDIF (Mardia, 1989) and SDIF (Milojevic & Popovic, 1992) are the two classic ESM
deinterleaving histograms. Both work on c-th order TOA differences

    d_c[n] = TOA[n + c] - TOA[n],        c = 1, 2, 3, ...  (the "difference level")

A stable PRI piles up in one bin at level 1. A stagger with M elements piles up in M
bins at level 1 (the elements) and in ONE bin at level M: every pulse has a partner
exactly one frame period T later. Dwell-and-switch and sliding PRI behave the same with
M = pulses per pattern cycle. So the smallest tau that (a) exceeds the histogram
threshold and (b) survives the sequence search is the frame period T.

  CDIF  - the histogram is accumulated over the levels 1..c (cumulative).
          Threshold: gamma * T_obs / tau  (a fraction gamma of the largest possible
          number of intervals tau in the observation time T_obs).
          A candidate needs both tau and 2 * tau above the threshold.
  SDIF  - each level has its own histogram (sequential, not accumulated).
          Threshold: x * (E - c) * exp(-tau_bin / (k * N)), E = pulses, N = bins.
          At level 1 a candidate is tested only if it is the single peak; several
          level-1 peaks mean a multi-element pattern, so the search moves up a level.
          No 2 * tau test is needed, which is why SDIF stops at a lower level than CDIF.

Sequence search (both): tau is accepted when at least `rho` of the pulses have a pulse at
t + tau. This rejects sums of stagger elements (e.g. 850 + 1150 = 2000), which pass the
histogram threshold but connect only one pulse in M.

The histograms run on TOAs, so a missed pulse only removes a few counts and a false pulse
only adds isolated counts; neither shifts the pile-up. The estimated T is passed to the
shared TOA-grid back end (toa_utils.periodic_forecast) to forecast the next pulses.
The PRI elements are reported from the level-1 histogram.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict, Iterator, List, Optional

import numpy as np

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.toa_utils import (
    MIN_FRAMES,
    differences_near,
    level_differences,
    periodic_forecast,
    run_cli,
    successor_fraction,
    tuned,
)

# Tuned on the validation split (see tune_robust_methods.py).
BIN_WIDTH_US = tuned("cdif_sdif.BIN_WIDTH_US", 2.0)  # histogram bin width; peaks are read from a 3-bin window
MAX_LEVEL = 64         # highest difference level (CDIF needs 2 frames: 2 * 24 pulses)
CDIF_GAMMA = tuned("cdif_sdif.CDIF_GAMMA", 0.8)      # CDIF threshold factor
SDIF_X = tuned("cdif_sdif.SDIF_X", 0.15)              # SDIF threshold factor
SDIF_K = 1.0           # SDIF threshold decay constant
MAX_CANDIDATES = 8     # periods handed to the grid test, in the order they are found
SEARCH_RHO = tuned("cdif_sdif.SEARCH_RHO", 0.7)      # sequence search: share of pulses with a successor at t + tau


def _histogram(d: np.ndarray, n_bins: int, bin_width: float) -> np.ndarray:
    idx = np.floor(d / bin_width).astype(int)
    idx = idx[(idx >= 0) & (idx < n_bins)]
    return np.bincount(idx, minlength=n_bins).astype(np.float64)


def _smooth3(h: np.ndarray) -> np.ndarray:
    """Count in a 3-bin window, so a pile-up on a bin edge is not split in two."""
    out = h.copy()
    out[1:] += h[:-1]
    out[:-1] += h[1:]
    return out


def _peaks_above(hs: np.ndarray, thr: np.ndarray, lo_bin: int, hi_bin: int) -> List[int]:
    """Bin index of the maximum of every run of bins above the threshold (ascending tau)."""
    above = np.nonzero(hs[lo_bin:hi_bin] >= thr[lo_bin:hi_bin])[0] + lo_bin
    if len(above) == 0:
        return []
    runs = np.split(above, np.nonzero(np.diff(above) > 1)[0] + 1)
    return [int(r[np.argmax(hs[r])]) for r in runs]


def _tau_of_bin(toas: np.ndarray, b: int, bin_width: float) -> float:
    centre = (b + 0.5) * bin_width
    d = differences_near(toas, centre, 1.5 * bin_width)
    return float(np.median(d)) if len(d) else centre


def pri_elements(toas: np.ndarray, bin_width: float = BIN_WIDTH_US) -> List[float]:
    """PRI elements = peaks of the level-1 difference histogram (at least 5% of the pulses)."""
    d = level_differences(toas, 1)
    if len(d) == 0:
        return []
    n_bins = int(np.max(d) / bin_width) + 3
    hs = _smooth3(_histogram(d, n_bins, bin_width))
    thr = np.full(n_bins, max(3.0, 0.05 * len(d)))
    return [_tau_of_bin(toas, b, bin_width) for b in _peaks_above(hs, thr, 1, n_bins)]


def cdif_candidates(
    toas: np.ndarray,
    gamma: float = CDIF_GAMMA,
    bin_width: float = BIN_WIDTH_US,
    max_level: int = MAX_LEVEL,
    rho: float = SEARCH_RHO,
) -> Iterator[Dict]:
    """Cumulative difference histogram. Yields {"period", "level"} in the order found.

    The first result is the CDIF frame period. Later ones are only needed when the first
    turns out to be a coincidence: e.g. dwell PRIs in a 3:4 ratio (3 x 1148.6 = 4 x 862.5)
    give a tau that links most pulses to another pulse but is not the frame period. The
    caller detects that with the TOA-grid test and asks for the next candidate.
    """
    n = len(toas)
    span = float(toas[-1] - toas[0])
    if n < 8 or span <= 0:
        return
    n_bins = int(span / bin_width) + 3
    centres = (np.arange(n_bins) + 0.5) * bin_width
    thr = gamma * span / centres
    hi_bin = min(n_bins, int(span / MIN_FRAMES / bin_width) + 1)
    hist = np.zeros(n_bins)
    rejected = set()

    for c in range(1, min(max_level, n - 2) + 1):
        hist += _histogram(level_differences(toas, c), n_bins, bin_width)
        hs = _smooth3(hist)
        for b in _peaks_above(hs, thr, 1, hi_bin):
            if b in rejected or (b - 1) in rejected or (b + 1) in rejected:
                continue
            b2 = 2 * b + 1  # bin of 2 * tau
            if b2 + 2 >= n_bins or hs[b2 - 2:b2 + 3].max() < thr[b2]:
                continue  # may still pass at a higher level
            tau = _tau_of_bin(toas, b, bin_width)
            if successor_fraction(toas, tau) >= rho:
                yield {"period": tau, "level": c}
            rejected.add(b)


def sdif_candidates(
    toas: np.ndarray,
    x: float = SDIF_X,
    k: float = SDIF_K,
    bin_width: float = BIN_WIDTH_US,
    max_level: int = MAX_LEVEL,
    rho: float = SEARCH_RHO,
) -> Iterator[Dict]:
    """Sequential difference histogram. Yields {"period", "level"} in the order found
    (see cdif_candidates for why more than one may be needed)."""
    n = len(toas)
    span = float(toas[-1] - toas[0])
    if n < 8 or span <= 0:
        return
    n_bins = int(span / bin_width) + 3
    decay = np.exp(-np.arange(n_bins) / (k * n_bins))
    hi_bin = min(n_bins, int(span / MIN_FRAMES / bin_width) + 1)
    rejected = set()

    for c in range(1, min(max_level, n - 2) + 1):
        hs = _smooth3(_histogram(level_differences(toas, c), n_bins, bin_width))
        thr = x * (n - c) * decay
        peaks = _peaks_above(hs, thr, 1, hi_bin)
        if c == 1 and len(peaks) != 1:
            continue  # no PRI or several PRI elements: go to the next difference level
        for b in peaks:
            if b in rejected or (b - 1) in rejected or (b + 1) in rejected:
                continue
            tau = _tau_of_bin(toas, b, bin_width)
            if successor_fraction(toas, tau) >= rho:
                yield {"period": tau, "level": c}
            rejected.add(b)


def cdif_frame_period(toas: np.ndarray, **kwargs) -> Optional[Dict]:
    """CDIF frame period: first accepted tau, {"period", "level"} or None."""
    return next(cdif_candidates(toas, **kwargs), None)


def sdif_frame_period(toas: np.ndarray, **kwargs) -> Optional[Dict]:
    """SDIF frame period: first accepted tau, {"period", "level"} or None."""
    return next(sdif_candidates(toas, **kwargs), None)


def candidate_periods(fn, toas: np.ndarray, max_candidates: int = MAX_CANDIDATES) -> Iterator[float]:
    """Up to `max_candidates` periods of a candidate generator (evaluated lazily)."""
    for i, res in enumerate(fn(toas)):
        if i >= max_candidates:
            break
        yield res["period"]


def cdif_forecast(context: np.ndarray, horizon_len: int = 32, target_param: str = "PRI") -> np.ndarray:
    """Forecast from the CDIF frame period (rolling median if none is found)."""
    return periodic_forecast(context, horizon_len, target_param, lambda t: candidate_periods(cdif_candidates, t))


def sdif_forecast(context: np.ndarray, horizon_len: int = 32, target_param: str = "PRI") -> np.ndarray:
    """Forecast from the SDIF frame period (rolling median if none is found)."""
    return periodic_forecast(context, horizon_len, target_param, lambda t: candidate_periods(sdif_candidates, t))


if __name__ == "__main__":
    which = "cdif"
    if "--sdif" in sys.argv:
        sys.argv.remove("--sdif")
        which = "sdif"
    elif "--cdif" in sys.argv:
        sys.argv.remove("--cdif")
    if which == "cdif":
        run_cli("PULSAR Classic Baseline 7: CDIF histogram (use --sdif for SDIF)",
                "CDIF Histogram + TOA Grid", "cdif", cdif_forecast)
    else:
        run_cli("PULSAR Classic Baseline 8: SDIF histogram",
                "SDIF Histogram + TOA Grid", "sdif", sdif_forecast)
