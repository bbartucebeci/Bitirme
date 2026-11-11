"""Template-based gap filling: an optional ESM gate for the index-domain baselines.

The default gate (`common.clean_pri_context`) knows only the median interval:
  - an interval of about 2x the median is split into two EQUAL halves,
  - an interval that matches nothing is replaced by the median.
That is exact for a stable PRI but wrong for a pattern. In an 850 / 1000 / 1150 stagger a
missed pulse produces 850 + 1000 = 1850, which the default gate turns into 925 + 925,
i.e. two values that do not exist in the pattern, and a false pulse can leave the cleaned
sequence one sample longer or shorter than the true one (a cycle slip).

The template gate uses the detected pattern instead (TOA grid fit, toa_grid_fit.py):

  1. Detect the pattern: frame period T and the pulse positions inside the frame, which
     give the ordered PRI elements d_0 .. d_{M-1} (the template).
  2. Every received pulse is assigned to a grid point or marked as a false pulse.
  3. Intervals that fit no combination of template elements (they start or end at a
     false pulse) are removed; the two pieces around a false pulse are merged.
  4. A long interval that spans r grid steps is split into the r template intervals of
     exactly those positions (scaled so that they still add up to the measured interval).
  5. Pulses missed at the very end of the context are filled with template intervals up
     to the last context TOA, so the cleaned sequence ends at the true "now".

The output is a Delta-TOA sequence with exactly one sample per transmitted pulse: no
cycle slips are left for the downstream forecaster. If no pattern is detected (jittered
PRI, too few pulses) the default gate is used.

Usage in the existing baselines (their default behaviour is unchanged):
    kalman_forecast(ctx, gate="template")
    period_estimation_forecast(ctx, gate="template")
"""

from __future__ import annotations

from typing import List

import numpy as np

from classic_methods.common import clean_pri_context
from classic_methods.toa_utils import PHASE_TOL_US, toas_from_context

GATES = ("esm", "template")


def template_gap_fill(context: np.ndarray) -> np.ndarray:
    """Cleans an observed Delta-TOA context with the detected PRI pattern."""
    from classic_methods.toa_grid_fit import fit_toa_grid

    raw = np.asarray(context, dtype=np.float64)
    if len(raw) < 16:
        return clean_pri_context(raw)

    toas = toas_from_context(raw)
    model = fit_toa_grid(toas)
    if model is None:
        return clean_pri_context(raw)

    inl = model.inlier_mask()
    t_in = toas[inl]
    flat = model.flat_index()
    m_count = model.n_positions
    template = model.intervals  # template[m] = interval that ends at position m
    if len(t_in) < 4:
        return clean_pri_context(raw)

    out: List[float] = []
    for a in range(len(t_in) - 1):
        steps = int(flat[a + 1] - flat[a])
        total = float(t_in[a + 1] - t_in[a])
        if steps == 1:
            out.append(total)
        else:
            parts = template[(int(flat[a]) + 1 + np.arange(steps)) % m_count]
            out.extend(parts * (total / parts.sum()))

    # Grid points after the last received emitter pulse that are still inside the context.
    j = int(flat[-1]) + 1
    t = float(t_in[-1])
    while t + template[j % m_count] <= toas[-1] + PHASE_TOL_US:
        out.append(float(template[j % m_count]))
        t += template[j % m_count]
        j += 1

    return np.asarray(out, dtype=np.float64)


def apply_gate(context: np.ndarray, gate: str = "esm") -> np.ndarray:
    """Dispatches to the selected ESM gate ("esm" = default median gate)."""
    if gate == "esm":
        return clean_pri_context(context)
    if gate == "template":
        return template_gap_fill(context)
    raise ValueError(f"Unknown gate '{gate}'. Choose from {GATES}.")
