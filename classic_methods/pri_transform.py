#!/usr/bin/env python3
"""Method 9: PRI Transform (Nishiguchi & Kobayashi, 2000) with subharmonic suppression.

EE / Signal Processing Rationale:
---------------------------------
The autocorrelation of a pulse train (which CDIF / SDIF histograms approximate) has peaks
at the PRI AND at all its multiples 2 * PRI, 3 * PRI, ... (subharmonics). The PRI
transform adds a phase factor to every pulse pair:

    D(tau) = sum_{n > m, t_n - t_m = tau}  exp( 2*pi*j * t_n / tau )

For the true PRI every pair contributes the same phase, so |D| equals the pair count.
For tau = 2 * PRI the pairs alternate between phase 0 and pi and cancel. The result is a
"PRI spectrum" with the subharmonics removed.

This implementation follows the *modified* PRI transform of the same paper:
  - shifting time origin: the phase of bin k is measured from an origin O_k that follows
    the pulse train, so the phase error does not grow with observation time;
  - overlapping bins (each pair is written to the 3 nearest bins).
A bin is a detected PRI when |D_k| exceeds all three thresholds of the paper:
  1. observation time:   alpha * T_obs / tau_k
  2. subharmonics:       beta  * C_k           (C_k = pair count of the bin)
  3. noise:              gamma * sqrt(T_obs * rho^2 * b_k)   (rho = pulse density)

Limitation that shows in the benchmark: the phase factor that suppresses subharmonics
also suppresses the FRAME period of a multi-position pattern. The M pulse positions of a
stagger frame have different phases o_m / T, so their phasors partly cancel
(|D| / C = |sum_m exp(2*pi*j*o_m/T)| / M, about 0.1 for the 850/1000/1150 stagger).
The transform is therefore reliable for stable PRI and detects stagger / dwell / sliding
frames only when the positions happen to add up. Detected PRIs are passed to the shared
TOA-grid back end; the first one that forms a valid grid is used.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict, List

import numpy as np

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.toa_utils import differences_near, periodic_forecast, run_cli, tuned

# Tuned on the validation split (see tune_robust_methods.py).
BIN_WIDTH_US = 2.0
ALPHA = tuned("pri_transform.ALPHA", 0.8)   # observation-time threshold factor
BETA = tuned("pri_transform.BETA", 0.02)    # subharmonic threshold factor (|D| / C)
GAMMA = 3.0            # noise threshold factor
ZETA0 = 0.03           # tolerance for moving the time origin
MAX_CANDIDATES = 6
MIN_PERIODS = tuned("pri_transform.MIN_PERIODS", 4.0)  # tau is searched up to T_obs / MIN_PERIODS: with fewer periods in the
                       # observation the phasors of a subharmonic do not complete a cycle and
                       # the suppression fails


def pri_transform(
    toas: np.ndarray,
    bin_width: float = BIN_WIDTH_US,
    zeta0: float = ZETA0,
    min_periods: float = MIN_PERIODS,
) -> Dict[str, np.ndarray]:
    """Modified PRI transform of a TOA sequence.

    Returns {"tau": bin centres, "D": |D_k|, "C": pair counts}.
    """
    n = len(toas)
    span = float(toas[-1] - toas[0])
    tau_max = span / min_periods
    n_bins = int(tau_max / bin_width) + 2
    centres = (np.arange(n_bins) + 0.5) * bin_width
    d = np.zeros(n_bins, dtype=np.complex128)
    c = np.zeros(n_bins)
    origin = np.full(n_bins, np.nan)

    for i in range(1, n):
        t_n = toas[i]
        for m in range(i - 1, -1, -1):
            tau = t_n - toas[m]
            if tau > tau_max:
                break
            if tau <= bin_width:
                continue
            b0 = int(tau / bin_width)
            for b in (b0 - 1, b0, b0 + 1):
                if b < 1 or b >= n_bins:
                    continue
                tau_k = centres[b]
                if np.isnan(origin[b]):
                    origin[b] = toas[m]
                eta0 = (t_n - origin[b]) / tau_k
                nu = np.floor(eta0 + 0.49999)
                d[b] += np.exp(2j * np.pi * eta0)
                c[b] += 1.0
                if nu == 1.0 and toas[m] == origin[b]:
                    origin[b] = t_n
                elif nu >= 2.0 and abs(eta0 / nu - 1.0) <= zeta0:
                    origin[b] = t_n
    return {"tau": centres, "D": np.abs(d), "C": c}


def pri_transform_periods(
    toas: np.ndarray,
    alpha: float = ALPHA,
    beta: float = BETA,
    gamma: float = GAMMA,
    bin_width: float = BIN_WIDTH_US,
    max_candidates: int = MAX_CANDIDATES,
    min_periods: float = MIN_PERIODS,
) -> List[float]:
    """Detected PRI values, strongest spectral peak (largest |D|) first."""
    n = len(toas)
    span = float(toas[-1] - toas[0])
    if n < 8 or span <= 0:
        return []
    spec = pri_transform(toas, bin_width=bin_width, min_periods=min_periods)
    tau, mag, cnt = spec["tau"], spec["D"], spec["C"]
    density = n / span
    thr = np.maximum.reduce([
        alpha * span / tau,
        beta * cnt,
        np.full_like(tau, gamma * np.sqrt(span * density ** 2 * 3 * bin_width)),
    ])
    above = np.nonzero(mag >= thr)[0]
    if len(above) == 0:
        return []
    runs = np.split(above, np.nonzero(np.diff(above) > 1)[0] + 1)
    peaks = [int(r[np.argmax(mag[r])]) for r in runs]
    peaks.sort(key=lambda b: -mag[b])
    out = []
    for b in peaks[:max_candidates]:
        dd = differences_near(toas, tau[b], 1.5 * bin_width)
        out.append(float(np.median(dd)) if len(dd) else float(tau[b]))
    return out


def pri_transform_forecast(context: np.ndarray, horizon_len: int = 32, target_param: str = "PRI") -> np.ndarray:
    """Forecast from the PRI-transform peaks (rolling median if none forms a grid)."""
    return periodic_forecast(context, horizon_len, target_param, pri_transform_periods)


if __name__ == "__main__":
    run_cli("PULSAR Classic Baseline 9: PRI Transform", "PRI Transform + TOA Grid",
            "pri_transform", pri_transform_forecast)
