#!/usr/bin/env python3
"""Method 11: Lomb-Scargle Periodogram (alternative frame-period estimator).

EE / Signal Processing Rationale:
---------------------------------
The PRI modulation of a stagger, dwell-and-switch or sliding radar is a periodic function
of TIME with period T (the frame period). The receiver samples it once per received
pulse, i.e. at the uneven instants TOA[n]; missed pulses leave holes and false pulses
give samples that carry no information. An FFT needs uniform sampling, so index-domain
spectra slip at every missed pulse. The Lomb-Scargle periodogram is the least-squares
spectrum for unevenly sampled data and needs no resampling:

    samples:  (t_n, y_n) = (TOA[n], TOA[n] - TOA[n-1])
    P(f) = normalised power of the best-fitting sinusoid of frequency f

Procedure:
  1. Drop samples that are obviously not one PRI (outside 0.55 .. 1.65 x median): these
     are the intervals touched by a missed or false pulse. No interpolation is needed.
  2. Evaluate P(f) for periods between 1.9 x median PRI and T_obs / 2.5.
  3. If the highest peak exceeds `MIN_POWER`, 1 / f_peak is the frame period. It is then
     snapped onto the nearest pile-up of TOA differences, because the periodogram
     resolves the period only to a fraction of T^2 / T_obs.
  4. If there is no significant peak the PRI is unmodulated: the candidate is the median
     interval itself (stable PRI). A jittered PRI fails the grid test and falls back to
     the rolling median.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import List

import numpy as np
from scipy.signal import lombscargle

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.toa_utils import MIN_FRAMES, periodic_forecast, run_cli, snap_period, tuned

# Tuned on the validation split (see tune_robust_methods.py).
MIN_POWER = tuned("lomb_scargle.MIN_POWER", 0.05)  # normalised peak power required to call the PRI periodic
OVERSAMPLING = 8       # frequency grid points per resolution cell 1 / T_obs
N_PEAKS = 3            # number of periodogram peaks handed to the grid test


def lomb_scargle_spectrum(toas: np.ndarray, oversampling: int = OVERSAMPLING):
    """Returns (frequencies [1/us], normalised power, median interval)."""
    t = toas[1:]
    y = np.diff(toas)
    med = float(np.median(y))
    keep = (y >= 0.55 * med) & (y < 1.65 * med)
    t, y = t[keep], y[keep]
    span = float(toas[-1] - toas[0])
    if len(y) < 12 or float(np.std(y)) < 1e-9:
        return np.empty(0), np.empty(0), med
    f_min = MIN_FRAMES / span
    f_max = 1.0 / (1.9 * med)
    if f_max <= f_min:
        return np.empty(0), np.empty(0), med
    freqs = np.arange(f_min, f_max, 1.0 / (oversampling * span))
    power = lombscargle(t, y - np.mean(y), 2.0 * np.pi * freqs, normalize=True)
    return freqs, power, med


def lomb_scargle_periods(toas: np.ndarray, min_power: float = MIN_POWER, n_peaks: int = N_PEAKS) -> List[float]:
    """Candidate frame periods from the periodogram peaks, strongest first."""
    if len(toas) < 16:
        return []
    freqs, power, med = lomb_scargle_spectrum(toas)
    out: List[float] = []
    if len(power) >= 3:
        is_peak = np.r_[False, (power[1:-1] >= power[:-2]) & (power[1:-1] >= power[2:]), False]
        idx = np.nonzero(is_peak & (power >= min_power))[0]
        idx = idx[np.argsort(-power[idx])][:n_peaks]
        for i in idx:
            # Parabolic interpolation of the peak, then snap to the TOA-difference pile-up.
            a, b, c = power[i - 1], power[i], power[i + 1]
            denom = a - 2 * b + c
            shift = 0.5 * (a - c) / denom if abs(denom) > 1e-12 else 0.0
            f_peak = freqs[i] + shift * (freqs[1] - freqs[0])
            base = 1.0 / f_peak
            # The fundamental 1 / T is the usual peak; 2 * base covers a peak on the 2nd harmonic.
            for mult in (1.0, 2.0):
                out.append(snap_period(toas, mult * base))
    out.append(med)  # unmodulated PRI
    return out


def lomb_scargle_forecast(context: np.ndarray, horizon_len: int = 32, target_param: str = "PRI") -> np.ndarray:
    """Forecast from the Lomb-Scargle frame period (rolling median if no grid is found)."""
    return periodic_forecast(context, horizon_len, target_param, lomb_scargle_periods)


if __name__ == "__main__":
    run_cli("PULSAR Classic Baseline 11: Lomb-Scargle periodogram", "Lomb-Scargle + TOA Grid",
            "lomb_scargle", lomb_scargle_forecast)
