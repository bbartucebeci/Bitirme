"""Seasonal-period candidate screening shared by Exponential Smoothing and ARIMA.

Holt-Winters and seasonal ARIMA need the season length S as a fixed input. Fitting every
S in [2, 24] is wasteful, so candidates are screened with the sample autocorrelation
function (ACF), the standard Box-Jenkins identification step: a periodic PRI law with
period P produces ACF peaks at lags P, 2P, 3P, ...

The ACF is computed on a winsorised copy of the series (clipped to median +/- 5 robust
standard deviations) so that residual missing / false-pulse outliers do not mask peaks.
"""

from __future__ import annotations

from typing import List

import numpy as np


def winsorize(x: np.ndarray, k: float = 5.0) -> np.ndarray:
    """Clips x to median +/- k * 1.4826 * MAD (no-op if MAD is zero)."""
    med = float(np.median(x))
    mad = 1.4826 * float(np.median(np.abs(x - med)))
    if mad <= 0:
        return x.copy()
    return np.clip(x, med - k * mad, med + k * mad)


def acf(x: np.ndarray, max_lag: int) -> np.ndarray:
    """Biased sample autocorrelation r[0..max_lag] (r[0] = 1)."""
    z = x - np.mean(x)
    denom = float(np.dot(z, z))
    r = np.zeros(max_lag + 1)
    if denom <= 0:
        return r
    r[0] = 1.0
    for lag in range(1, max_lag + 1):
        r[lag] = float(np.dot(z[:-lag], z[lag:])) / denom
    return r


def seasonal_candidates(
    x: np.ndarray,
    max_period: int = 24,
    top_k: int = 3,
    min_acf: float = 0.2,
    min_cycles: int = 3,
) -> List[int]:
    """Returns up to `top_k` candidate season lengths, strongest ACF peak first.

    A lag qualifies if it is a local maximum of the ACF, exceeds `min_acf`, and at
    least `min_cycles` full cycles fit in the series (needed to estimate a season).
    """
    n = len(x)
    max_lag = int(min(max_period, n // min_cycles))
    if max_lag < 2:
        return []
    r = acf(winsorize(np.asarray(x, dtype=np.float64)), max_lag + 1)
    peaks = []
    for lag in range(2, max_lag + 1):
        if r[lag] > min_acf and r[lag] >= r[lag - 1] and r[lag] >= r[lag + 1]:
            peaks.append((r[lag], lag))
    # Strongest peak first; near-ties (within 0.05) go to the shorter lag, so the
    # fundamental period P is preferred over its harmonics 2P, 3P (which have ACF ~ r[P]).
    peaks.sort(key=lambda rl: (-round(rl[0] / 0.05), rl[1]))
    return [lag for _, lag in peaks[:top_k]]
