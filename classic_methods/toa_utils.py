"""Shared TOA-domain tools for the robust-periodicity classic methods.

The existing baselines work in the pulse-index domain: they see the Delta-TOA sequence
y[n] and assume y[n] = y[n + P]. A missed pulse or a false pulse shifts every later
sample by one index (a cycle slip), so the index-domain period is only locally valid.

In the TOA domain there are no cycle slips. A periodic emitter (stable, stagger,
dwell-and-switch, sliding) transmits on a time grid

    TOA = t_ref + k * T + o_m,      k = frame number, m = position inside the frame,

where T is the frame period (sum of all PRI elements of one pattern cycle) and o_m are
the M pulse positions inside the frame. A missed pulse is an empty grid point and a false
pulse is a pulse that lies on no grid point; neither moves the other pulses.

This module holds the pieces every TOA-domain method needs:

  - TOA reconstruction from the Delta-TOA context,
  - level-c TOA differences and the "sequence search" check used by CDIF / SDIF,
  - frame-period refinement, folding the TOAs modulo T and clustering the phases,
  - the `GridModel` and its forecast (the next grid points after the context).

Only the context is used. Ground-truth labels never reach this module.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from math import lgamma, log
from typing import Callable, List, Optional, Sequence

import numpy as np


def tuned(name: str, default):
    """Value of a tunable constant.

    The defaults in the source are the values selected on the validation split.
    tune_robust_methods.py re-runs the methods with other values by passing a JSON
    dictionary in the environment variable PULSAR_ROBUST_PARAMS (read at import time).
    """
    overrides = json.loads(os.environ.get("PULSAR_ROBUST_PARAMS", "{}"))
    return type(default)(overrides[name]) if name in overrides else default


# Tuned on the validation split (see tune_robust_methods.py).
PHASE_TOL_US = tuned("toa.PHASE_TOL_US", 4.0)   # pulses share a grid position if their folded phases differ by < this
MIN_INLIER_FRACTION = tuned("toa.MIN_INLIER_FRACTION", 0.80)  # share of context pulses that must lie on the grid
MIN_COVERAGE = tuned("toa.MIN_COVERAGE", 0.70)  # share of grid points inside the context that must be observed
FALLBACK_WINDOW = tuned("toa.FALLBACK_WINDOW", 96)  # rolling-median window when no periodicity is found
MIN_FRAMES = 2.5          # the context must span at least this many frames
SEARCH_TOL_US = 5.0       # tolerance of the sequence search (pulse expected at t + tau)
MAX_POSITIONS = 32        # largest number of pulse positions per frame


def is_pri_target(target_param: str) -> bool:
    return target_param.upper() in ("PRI", "MEASURED_DELTA_TOA")


def toas_from_context(context: np.ndarray) -> np.ndarray:
    """Rebuilds the TOAs of the context pulses from their Delta-TOAs (first pulse at t = 0)."""
    x = np.asarray(context, dtype=np.float64)
    return np.concatenate(([0.0], np.cumsum(x)))


def level_differences(toas: np.ndarray, level: int) -> np.ndarray:
    """c-th order TOA differences t[n + c] - t[n] (the CDIF / SDIF difference level c)."""
    if level >= len(toas):
        return np.empty(0, dtype=np.float64)
    return toas[level:] - toas[:-level]


def successor_fraction(toas: np.ndarray, tau: float, tol: float = SEARCH_TOL_US) -> float:
    """Sequence search: share of pulses that have another pulse at t + tau (+/- tol).

    Only pulses whose successor would still fall inside the context are counted. A true
    (frame) period gives a value close to 1 - miss rate; a sum of two stagger elements
    gives about 1 / M.
    """
    t_end = toas[-1]
    eligible = toas[toas + tau <= t_end + tol]
    if len(eligible) < 4:
        return 0.0
    lo = np.searchsorted(toas, eligible + tau - tol, side="left")
    hi = np.searchsorted(toas, eligible + tau + tol, side="right")
    return float(np.mean(hi > lo))


def differences_near(toas: np.ndarray, target: float, tol: float) -> np.ndarray:
    """All pairwise TOA differences t[j] - t[i] that lie within +/- tol of `target`."""
    lo = np.searchsorted(toas, toas + target - tol, side="left")
    hi = np.searchsorted(toas, toas + target + tol, side="right")
    out: List[float] = []
    for i in np.nonzero(hi > lo)[0]:
        out.extend(toas[lo[i]:hi[i]] - toas[i])
    return np.asarray(out, dtype=np.float64)


def refine_period(toas: np.ndarray, period: float, tol: float = SEARCH_TOL_US) -> float:
    """Sharpens a frame-period estimate with differences over 1, 2, 4, ... frames.

    The median of the differences close to j * T, divided by j, has an error j times
    smaller than a single-frame difference, so the estimate improves at every doubling
    while the search window stays fixed.
    """
    span = toas[-1] - toas[0]
    t_est = float(period)
    j = 1
    while j * t_est <= 0.8 * span:
        d = differences_near(toas, j * t_est, tol)
        if len(d) < 3:
            break
        t_est = float(np.median(d)) / j
        j *= 2
    return t_est


# ---------------------------------------------------------------------------
# Grid model
# ---------------------------------------------------------------------------

@dataclass
class GridModel:
    """TOA = t_ref + k * period + offsets[m]."""

    period: float
    t_ref: float
    offsets: np.ndarray                      # sorted, in [0, period)
    frame_idx: np.ndarray = field(repr=False, default=None)   # k per context pulse (-1 = not on grid)
    pos_idx: np.ndarray = field(repr=False, default=None)     # m per context pulse (-1 = not on grid)
    inlier_fraction: float = 0.0
    coverage: float = 0.0

    @property
    def n_positions(self) -> int:
        return len(self.offsets)

    @property
    def intervals(self) -> np.ndarray:
        """PRI elements of one frame; intervals[m] is the interval that ends at position m."""
        o = self.offsets
        prev = np.concatenate(([o[-1] - self.period], o[:-1]))
        return o - prev

    def inlier_mask(self) -> np.ndarray:
        return self.pos_idx >= 0

    def grid_points(self, t_start: float, t_stop: float) -> np.ndarray:
        """All grid TOAs in [t_start, t_stop], sorted."""
        k0 = int(np.floor((t_start - self.t_ref) / self.period)) - 1
        k1 = int(np.ceil((t_stop - self.t_ref) / self.period)) + 1
        ks = np.arange(k0, k1 + 1)
        pts = (self.t_ref + ks[:, None] * self.period + self.offsets[None, :]).ravel()
        return pts[(pts >= t_start) & (pts <= t_stop)]

    def flat_index(self) -> np.ndarray:
        """Running grid index k * M + m of every inlier pulse."""
        m = self.inlier_mask()
        return self.frame_idx[m] * self.n_positions + self.pos_idx[m]


def fold_and_cluster(
    toas: np.ndarray,
    period: float,
    tol: float = PHASE_TOL_US,
    min_frames: float = MIN_FRAMES,
) -> Optional[GridModel]:
    """Folds the TOAs modulo `period` and extracts the pulse positions of one frame.

    Pulses of a periodic emitter pile up at M phases; false pulses are spread uniformly.
    A phase cluster is accepted as a grid position if it is narrow (< 3 * tol) and holds
    a pulse in at least half of the frames that the context covers.
    Returns None if the context is shorter than `min_frames` frames or nothing clusters.
    """
    n = len(toas)
    span = toas[-1] - toas[0]
    if period <= 0 or span < min_frames * period:
        return None

    # Put the fold boundary in the middle of the largest empty phase gap, so no cluster
    # is cut in two by the wrap-around.
    phase0 = np.sort(np.mod(toas - toas[0], period))
    gaps = np.diff(np.concatenate((phase0, [phase0[0] + period])))
    g = int(np.argmax(gaps))
    t_ref = toas[0] + phase0[g] + 0.5 * gaps[g] - period

    rel = toas - t_ref
    k = np.floor(rel / period).astype(int)
    phase = rel - k * period

    order = np.argsort(phase, kind="stable")
    ph_sorted = phase[order]
    breaks = np.nonzero(np.diff(ph_sorted) > tol)[0] + 1
    groups = np.split(order, breaks)

    n_frames = span / period
    min_count = max(2, int(np.ceil(0.5 * n_frames)))

    offsets: List[float] = []
    members: List[np.ndarray] = []
    for grp in groups:
        if len(grp) < min_count:
            continue
        ph = phase[grp]
        if ph.max() - ph.min() > 3.0 * tol:
            continue
        offsets.append(float(np.median(ph)))
        members.append(grp)
    if not offsets or len(offsets) > MAX_POSITIONS:
        return None

    frame_idx = np.full(n, -1, dtype=int)
    pos_idx = np.full(n, -1, dtype=int)
    for m, grp in enumerate(members):
        # One pulse per grid point: of several pulses in the same cell (e.g. a multipath
        # echo right behind the direct pulse) keep the one closest to the position.
        dist = np.abs(phase[grp] - offsets[m])
        for kk in np.unique(k[grp]):
            cell = grp[k[grp] == kk]
            best = cell[np.argmin(dist[k[grp] == kk])]
            frame_idx[best] = kk
            pos_idx[best] = m

    model = GridModel(period=float(period), t_ref=float(t_ref), offsets=np.asarray(offsets),
                      frame_idx=frame_idx, pos_idx=pos_idx)
    _score(model, toas)
    return model


def _score(model: GridModel, toas: np.ndarray) -> None:
    inl = model.inlier_mask()
    model.inlier_fraction = float(np.mean(inl))
    if inl.any():
        t_in = toas[inl]
        n_grid = len(model.grid_points(t_in[0] - 1e-6, t_in[-1] + 1e-6))
        model.coverage = float(inl.sum() / max(n_grid, 1))
    else:
        model.coverage = 0.0


def refit_least_squares(model: GridModel, toas: np.ndarray) -> GridModel:
    """Least-squares refit of (period, offsets) on the inlier pulses.

    The model t = k * T + o_m is linear in the unknowns [T, o_0 .. o_{M-1}].
    """
    inl = model.inlier_mask()
    m_count = model.n_positions
    if inl.sum() < m_count + 2 or len(np.unique(model.frame_idx[inl])) < 2:
        return model
    a = np.zeros((int(inl.sum()), m_count + 1))
    a[:, 0] = model.frame_idx[inl]
    a[np.arange(a.shape[0]), 1 + model.pos_idx[inl]] = 1.0
    b = toas[inl] - model.t_ref
    sol, *_ = np.linalg.lstsq(a, b, rcond=None)
    period, offsets = float(sol[0]), sol[1:]
    if period <= 0 or np.any(np.diff(offsets) <= 0):
        return model
    out = GridModel(period=period, t_ref=model.t_ref, offsets=offsets,
                    frame_idx=model.frame_idx, pos_idx=model.pos_idx)
    _score(out, toas)
    return out


def is_acceptable(
    model: Optional[GridModel],
    min_inlier_fraction: float = MIN_INLIER_FRACTION,
    min_coverage: float = MIN_COVERAGE,
) -> bool:
    return (
        model is not None
        and model.inlier_fraction >= min_inlier_fraction
        and model.coverage >= min_coverage
    )


def fit_grid_from_period(toas: np.ndarray, period: float, tol: float = PHASE_TOL_US) -> Optional[GridModel]:
    """Frame period -> grid model (refine T, fold, cluster). None if the pulses do not fit."""
    if not np.isfinite(period) or period <= 0:
        return None
    t_est = refine_period(toas, period)
    model = fold_and_cluster(toas, t_est, tol=tol)
    return model if is_acceptable(model) else None


# ---------------------------------------------------------------------------
# Forecast
# ---------------------------------------------------------------------------

def grid_forecast(model: GridModel, t_end: float, horizon_len: int, tol: float = PHASE_TOL_US) -> np.ndarray:
    """PRI of the next `horizon_len` emitter pulses = spacing of the next grid points.

    The target of horizon pulse h is the transmitter interval that ends at that pulse, so
    it is the distance between consecutive grid points whether or not the earlier point
    was received. Grid points up to `t_end` (last context TOA) are already in the past.
    """
    m_count = model.n_positions
    t_stop = t_end + (horizon_len / m_count + 3) * model.period
    pts = model.grid_points(t_end - 2 * model.period, t_stop)
    first = int(np.searchsorted(pts, t_end + tol, side="right"))
    first = max(first, 1)
    return np.diff(pts)[first - 1:first - 1 + horizon_len]


def estimate_slip_rates(model: GridModel, toas: np.ndarray) -> tuple:
    """Miss probability per grid point and false-pulse probability per received pulse.

    Both are estimated from the context only, with add-half smoothing so that a context
    without any error still gives a small non-zero rate.
    """
    inl = model.inlier_mask()
    n_in = int(inl.sum())
    t_in = toas[inl]
    n_grid = len(model.grid_points(t_in[0] - 1e-6, t_in[-1] + 1e-6))
    p_miss = (max(n_grid - n_in, 0) + 0.5) / (n_grid + 1.0)
    p_false = (len(toas) - n_in + 0.5) / (len(toas) + 1.0)
    return float(p_miss), float(p_false)


def weighted_median(values: Sequence[float], weights: Sequence[float]) -> float:
    v = np.asarray(values, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    order = np.argsort(v, kind="stable")
    v, w = v[order], w[order]
    cw = np.cumsum(w)
    return float(v[int(np.searchsorted(cw, 0.5 * cw[-1]))])


def hedged_grid_forecast(
    model: GridModel,
    toas: np.ndarray,
    horizon_len: int,
    tol: float = PHASE_TOL_US,
    max_shift: int = 6,
) -> np.ndarray:
    """Grid forecast that accounts for pulses that will be missed inside the horizon.

    Horizon row h is the (h + 1)-th *received* pulse. If s grid points before it are
    missed, it sits s positions further along the pattern; if f false pulses were received
    before it, it sits f positions earlier. With miss probability p per grid point,
    s ~ NegativeBinomial(h + 1, p); f ~ Binomial(h, p_false). The forecast is the median
    of the PRI over that shift distribution. While no pulse loss is likely
    (P(shift = 0) > 0.5) it equals the plain grid forecast. Experimental: it did not
    lower the validation MAE, see toa_grid_fit.py.
    """
    p_miss, p_false = estimate_slip_rates(model, toas)
    t_end = toas[-1]
    base = grid_forecast(model, t_end, horizon_len + max_shift, tol=tol)   # base[j] = PRI at grid step j
    out = np.empty(horizon_len)
    shifts_s = np.arange(0, max_shift + 1)
    for h in range(horizon_len):
        # P(s misses before the (h+1)-th received pulse)
        log_ps = np.array([
            lgamma(h + s + 1) - lgamma(s + 1) - lgamma(h + 1) + s * log(p_miss) + (h + 1) * log(1.0 - p_miss)
            for s in shifts_s
        ])
        ps = np.exp(log_ps)
        # P(f false pulses among the h rows before this one), f in {0, 1, 2}
        fs = np.arange(0, min(h, 2) + 1)
        log_pf = np.array([
            lgamma(h + 1) - lgamma(f + 1) - lgamma(h - f + 1) + f * log(p_false) + (h - f) * log(1.0 - p_false)
            for f in fs
        ])
        pf = np.exp(log_pf)
        vals, wts = [], []
        for s, w_s in zip(shifts_s, ps):
            for f, w_f in zip(fs, pf):
                j = h + s - f
                if 0 <= j < len(base):
                    vals.append(base[j])
                    wts.append(w_s * w_f)
        out[h] = weighted_median(vals, wts) if vals else base[h]
    return out


def fallback_forecast(
    context: np.ndarray, horizon_len: int, target_param: str = "PRI", window: int = FALLBACK_WINDOW
) -> np.ndarray:
    """Gated rolling median, used when no periodicity is found."""
    from classic_methods.rolling_median import rolling_median_forecast

    return rolling_median_forecast(context, horizon_len=horizon_len, target_param=target_param, window_size=window)


def snap_period(toas: np.ndarray, period: float, rel_search: float = 0.03, window: float = 6.0) -> float:
    """Moves a coarse period estimate onto the nearest pile-up of TOA differences.

    Spectral estimators (Lomb-Scargle) locate the frame period only to a fraction of
    their resolution cell. The densest `window`-wide cluster of pairwise TOA differences
    inside period * (1 +/- rel_search) is the actual frame spacing.
    """
    half = rel_search * period
    d = np.sort(differences_near(toas, period, half))
    if len(d) < 3:
        return float(period)
    hi = np.searchsorted(d, d + window, side="right")
    counts = hi - np.arange(len(d))
    i = int(np.argmax(counts))
    return float(np.median(d[i:hi[i]]))


def periodic_forecast(
    context: np.ndarray,
    horizon_len: int,
    target_param: str,
    period_fn: Callable[[np.ndarray], Sequence[float]],
    fallback_window: int = FALLBACK_WINDOW,
) -> np.ndarray:
    """Common back end of the frame-period estimators (CDIF, SDIF, PRI transform, Lomb-Scargle).

    `period_fn(toas)` returns candidate frame periods, best first. The first candidate
    whose folded TOAs form an acceptable grid is used to forecast; otherwise the method
    falls back to the gated rolling median.
    """
    raw = np.asarray(context, dtype=np.float64)
    if len(raw) == 0:
        return np.zeros(horizon_len, dtype=np.float64)
    if is_pri_target(target_param) and len(raw) >= 16:
        toas = toas_from_context(raw)
        for period in period_fn(toas):
            model = fit_grid_from_period(toas, period)
            if model is not None:
                preds = grid_forecast(model, toas[-1], horizon_len)
                if len(preds) == horizon_len and np.all(np.isfinite(preds)):
                    return preds
    return fallback_forecast(raw, horizon_len, target_param, window=fallback_window)


def run_cli(description: str, method_name: str, method_slug: str, predict_fn) -> None:
    """Command-line entry point shared by the robust-periodicity methods.

    Same arguments and output layout as the existing baselines
    (results/classic_methods/<method_slug>/<profile>_pri/metrics.csv).
    """
    import argparse

    from classic_methods.common import ERROR_LEVELS, PARAM_SPECS, RADAR_TYPES, evaluate_method_across_benchmarks

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--profile-mode", choices=["fixed", "varying"], default="fixed")
    parser.add_argument("--target-param", choices=list(PARAM_SPECS.keys()), default="PRI")
    parser.add_argument("--radar-type", choices=RADAR_TYPES + ["all"], default="all")
    parser.add_argument("--error-level", choices=ERROR_LEVELS + ["all"], default="all")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--max-test-seqs", type=int, default=200)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    evaluate_method_across_benchmarks(
        method_name=method_name,
        method_slug=method_slug,
        predict_fn=predict_fn,
        profile_mode=args.profile_mode,
        target_param=args.target_param,
        radar_types=RADAR_TYPES if args.radar_type == "all" else [args.radar_type],
        error_levels=ERROR_LEVELS if args.error_level == "all" else [args.error_level],
        context_len=args.context_len,
        horizon_len=args.horizon,
        max_test_seqs=args.max_test_seqs,
        smoke_test=args.smoke_test,
    )
