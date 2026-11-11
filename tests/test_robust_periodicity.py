"""Unit tests for the robust-periodicity classic methods.

Small hand-built pulse trains with known answers:
  - a stagger with one missed pulse,
  - a stagger with one false pulse,
  - a dwell-and-switch pattern (clean, and with a missed + a false pulse).

Run from the repository root:  python -m pytest tests -q
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.cdif_sdif import cdif_forecast, cdif_frame_period, pri_elements, sdif_forecast, sdif_frame_period
from classic_methods.common import clean_pri_context
from classic_methods.kalman_filter import kalman_forecast
from classic_methods.lomb_scargle import lomb_scargle_forecast, lomb_scargle_periods
from classic_methods.period_estimation import period_estimation_forecast
from classic_methods.pri_transform import pri_transform, pri_transform_periods
from classic_methods.template_gate import template_gap_fill
from classic_methods.toa_grid_fit import fit_toa_grid, toa_grid_forecast
from classic_methods.toa_utils import fit_grid_from_period, toas_from_context

STAGGER = np.array([850.0, 1000.0, 1150.0])
DWELL = np.array([850.0] * 8 + [1150.0] * 8)
CONTEXT_PULSES = 97   # 97 TOAs -> 96 Delta-TOA samples
HORIZON = 32
TOL = 1.0             # us


def make_train(pattern, n_pulses, drop=(), false_at=(), noise_std=0.0, seed=0):
    """Builds a pulse train.

    Returns (context Delta-TOAs, true PRI of the next HORIZON transmitted pulses, clean
    Delta-TOAs of the transmitted context pulses). `drop` lists transmitted-pulse indices
    that are not received; `false_at` lists TOAs of false pulses.
    """
    rng = np.random.default_rng(seed)
    total = n_pulses + HORIZON
    pris = np.resize(pattern, total)          # pris[i] = interval ending at pulse i (i >= 1)
    toas = np.concatenate(([0.0], np.cumsum(pris[1:])))
    received = np.delete(toas[:n_pulses], list(drop))
    if noise_std > 0:
        received = received + rng.normal(0.0, noise_std, len(received))
    observed = np.sort(np.concatenate((received, np.asarray(false_at, dtype=float))))
    context = np.diff(observed)
    future_pri = pris[n_pulses:n_pulses + HORIZON]
    return context, future_pri, pris[1:n_pulses]


# ---------------------------------------------------------------------------
# Stagger with a missed pulse
# ---------------------------------------------------------------------------

@pytest.fixture
def stagger_missed():
    return make_train(STAGGER, CONTEXT_PULSES, drop=(40,))


def test_stagger_missed_frame_period(stagger_missed):
    context, _, _ = stagger_missed
    toas = toas_from_context(context)
    assert cdif_frame_period(toas)["period"] == pytest.approx(3000.0, abs=TOL)
    assert sdif_frame_period(toas)["period"] == pytest.approx(3000.0, abs=TOL)
    assert sdif_frame_period(toas)["level"] == 3
    assert any(abs(p - 3000.0) < TOL for p in lomb_scargle_periods(toas))


def test_stagger_missed_elements(stagger_missed):
    context, _, _ = stagger_missed
    elements = pri_elements(toas_from_context(context))
    assert np.allclose(sorted(elements), STAGGER, atol=TOL)


def test_stagger_missed_grid(stagger_missed):
    context, _, _ = stagger_missed
    toas = toas_from_context(context)
    model = fit_toa_grid(toas)
    assert model is not None
    assert model.period == pytest.approx(3000.0, abs=TOL)
    assert model.n_positions == 3
    assert np.allclose(sorted(model.intervals), STAGGER, atol=TOL)
    assert model.inlier_fraction == 1.0          # no false pulses
    assert model.coverage < 1.0                  # one empty grid point


@pytest.mark.parametrize("forecast", [cdif_forecast, sdif_forecast, lomb_scargle_forecast, toa_grid_forecast])
def test_stagger_missed_forecast(stagger_missed, forecast):
    context, future, _ = stagger_missed
    assert np.allclose(forecast(context, HORIZON, "PRI"), future, atol=TOL)


def test_stagger_missed_template_gate(stagger_missed):
    context, _, clean = stagger_missed
    filled = template_gap_fill(context)
    # The 1850 us gap becomes its two template intervals, not 925 + 925.
    assert len(filled) == len(clean)
    assert np.allclose(filled, clean, atol=TOL)
    default = clean_pri_context(context)
    assert not np.allclose(default, clean, atol=TOL)


# ---------------------------------------------------------------------------
# Stagger with a false pulse
# ---------------------------------------------------------------------------

@pytest.fixture
def stagger_false():
    # False pulse 400 us after the transmitted pulse at t = 30000 us.
    return make_train(STAGGER, CONTEXT_PULSES, false_at=(30400.0,))


def test_stagger_false_grid(stagger_false):
    context, _, _ = stagger_false
    toas = toas_from_context(context)
    model = fit_toa_grid(toas)
    assert model is not None
    assert model.period == pytest.approx(3000.0, abs=TOL)
    assert model.n_positions == 3
    outliers = np.nonzero(~model.inlier_mask())[0]
    assert len(outliers) == 1
    assert toas[outliers[0]] == pytest.approx(30400.0, abs=TOL)


@pytest.mark.parametrize("forecast", [cdif_forecast, sdif_forecast, lomb_scargle_forecast, toa_grid_forecast])
def test_stagger_false_forecast(stagger_false, forecast):
    context, future, _ = stagger_false
    assert np.allclose(forecast(context, HORIZON, "PRI"), future, atol=TOL)


def test_stagger_false_template_gate(stagger_false):
    context, _, clean = stagger_false
    filled = template_gap_fill(context)
    assert len(filled) == len(clean)
    assert np.allclose(filled, clean, atol=TOL)


def test_false_pulse_as_last_context_pulse():
    # The last received pulse is false: the forecast must still start at the next grid point.
    context, future, _ = make_train(STAGGER, CONTEXT_PULSES)
    t_last = float(np.sum(context))
    context2, _, _ = make_train(STAGGER, CONTEXT_PULSES, false_at=(t_last + 300.0,))
    assert np.allclose(toa_grid_forecast(context2, HORIZON, "PRI"), future, atol=TOL)


def test_missed_pulse_at_end_of_context():
    # The last transmitted context pulse is missed: the grid still knows where "now" is.
    context, future, _ = make_train(STAGGER, CONTEXT_PULSES, drop=(CONTEXT_PULSES - 1,))
    preds = toa_grid_forecast(context, HORIZON, "PRI")
    # The first future grid point is the missed pulse itself, then the true future.
    assert np.allclose(preds[1:], future[:-1], atol=TOL)


# ---------------------------------------------------------------------------
# Dwell and switch
# ---------------------------------------------------------------------------

def test_dwell_clean():
    context, future, _ = make_train(DWELL, CONTEXT_PULSES)
    toas = toas_from_context(context)
    assert sdif_frame_period(toas)["period"] == pytest.approx(16000.0, abs=TOL)
    assert cdif_frame_period(toas)["period"] == pytest.approx(16000.0, abs=TOL)
    model = fit_toa_grid(toas)
    assert model.n_positions == 16
    for forecast in (cdif_forecast, sdif_forecast, lomb_scargle_forecast, toa_grid_forecast):
        assert np.allclose(forecast(context, HORIZON, "PRI"), future, atol=TOL)


def test_dwell_missed_and_false_with_noise():
    context, future, clean = make_train(
        DWELL, CONTEXT_PULSES, drop=(20, 70), false_at=(41234.0,), noise_std=0.5, seed=3
    )
    toas = toas_from_context(context)
    model = fit_toa_grid(toas)
    assert model is not None
    assert model.period == pytest.approx(16000.0, abs=2.0)
    assert model.n_positions == 16
    assert int((~model.inlier_mask()).sum()) == 1
    assert np.allclose(toa_grid_forecast(context, HORIZON, "PRI"), future, atol=3.0)
    filled = template_gap_fill(context)
    assert len(filled) == len(clean)
    assert np.allclose(filled, clean, atol=3.0)


def test_dwell_template_gate_helps_index_domain_methods():
    context, future, _ = make_train(DWELL, CONTEXT_PULSES, drop=(20, 70), false_at=(41234.0,))
    for forecast in (period_estimation_forecast, kalman_forecast):
        preds = forecast(context, HORIZON, "PRI", gate="template")
        assert np.allclose(preds, future, atol=TOL)


# ---------------------------------------------------------------------------
# Other properties
# ---------------------------------------------------------------------------

def test_pri_transform_stable_and_subharmonics():
    context, _, _ = make_train(np.array([1000.0]), CONTEXT_PULSES, drop=(30,))
    toas = toas_from_context(context)
    periods = pri_transform_periods(toas)
    assert periods and periods[0] == pytest.approx(1000.0, abs=TOL)
    # Subharmonic suppression: |D| equals the pair count at the PRI and nearly vanishes
    # at 2 x, 3 x and 4 x PRI, although the pair counts there are just as large.
    spec = pri_transform(toas)
    at = lambda tau: int(np.argmin(np.abs(spec["tau"] - tau)))
    assert spec["D"][at(1000.0)] > 0.95 * spec["C"][at(1000.0)]
    for mult in (2, 3, 4):
        b = at(mult * 1000.0)
        assert spec["C"][b] > 80 and spec["D"][b] < 0.05 * spec["C"][b]


def test_jitter_falls_back_to_rolling_median():
    rng = np.random.default_rng(1)
    context = rng.normal(1000.0, 50.0, 96)
    toas = toas_from_context(context)
    assert fit_toa_grid(toas) is None
    assert fit_grid_from_period(toas, 1000.0) is None
    preds = toa_grid_forecast(context, HORIZON, "PRI")
    assert np.allclose(preds, preds[0])
    assert abs(preds[0] - 1000.0) < 30.0


def test_default_gate_behaviour_unchanged():
    # The new `gate` argument must not change the existing default behaviour.
    context, _, _ = make_train(STAGGER, CONTEXT_PULSES, drop=(40,), false_at=(30400.0,), noise_std=0.3)
    for forecast in (period_estimation_forecast, kalman_forecast):
        assert np.array_equal(forecast(context, HORIZON, "PRI"), forecast(context, HORIZON, "PRI", gate="esm"))
    x = clean_pri_context(context)
    from classic_methods.period_estimation import estimate_period_and_template

    period, template = estimate_period_and_template(x)
    assert period == 3 and len(template) == 3


def test_imm_and_combination_on_clean_stagger():
    from classic_methods.forecast_combination import combination_forecast
    from classic_methods.imm_filter import imm_forecast

    context, future, _ = make_train(STAGGER, CONTEXT_PULSES)
    assert np.allclose(imm_forecast(context, HORIZON, "PRI"), future, atol=TOL)
    assert np.allclose(combination_forecast(context, HORIZON, "PRI"), future, atol=TOL)


def test_dwell_with_commensurate_pris():
    # 4 x 862.5 = 3450 ~ 3 x 1148.6 = 3445.8: a tau that links most pulses but is not the
    # frame period. The histogram methods must move on to the next candidate.
    pattern = np.array([862.5] * 12 + [1148.6] * 12)
    context, future, _ = make_train(pattern, CONTEXT_PULSES)
    toas = toas_from_context(context)
    assert sdif_frame_period(toas)["period"] < 4000.0          # the coincidence is found first
    for forecast in (cdif_forecast, sdif_forecast, toa_grid_forecast):
        assert np.allclose(forecast(context, HORIZON, "PRI"), future, atol=TOL)
    assert fit_toa_grid(toas).n_positions == 24
