#!/usr/bin/env python3
"""Method 12: Interacting Multiple Model (IMM) Filter.

EE / Signal Processing Rationale:
---------------------------------
The Kalman filter bank (kalman_filter.py) is a STATIC multiple-model filter: it runs the
level, trend and periodic models independently and picks one for the whole context. The
IMM filter (Blom & Bar-Shalom, 1988) is the standard DYNAMIC multiple-model estimator:
the active model is a Markov chain with transition matrix PI, the model probabilities
are updated pulse by pulse from the innovation likelihoods, and before every step the
model states are mixed according to those probabilities.

    mu_j[n]  ~  Lambda_j[n] * sum_i PI[i, j] * mu_i[n-1]        (model probability)

The three models are the ones of the existing bank. IMM mixing needs one common state
vector, so they are written on the state of the periodic model plus a slope:

    s = [c_0 .. c_{P-1}, b],   observation  y[n] = c_{n mod P} + v[n]

    periodic:  c stays (each slot is a random walk), b = 0
    level:     all slots are replaced by their mean L (flat PRI), b = 0
    trend:     all slots are replaced by L + b, slope b is kept

P and the process-noise ratios q are taken from the bank's own prequential scoring
(best periodic period; best q per model; the bank's best model gets the initial
probability), so the IMM adds only the switching layer.
The measurement-noise scale and the Huber clipping of the state update are the same as
in the bank. The model likelihood uses a Student-t density (3 degrees of freedom) of the
unclipped innovation: a Gaussian likelihood would let one missed-pulse outlier decide the
model, while a likelihood of the clipped innovation cannot tell a wrong model from an
outlier at all.

Forecast: each model's state is propagated over the horizon and the forecasts are
combined with the final model probabilities.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict

import numpy as np

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.common import clean_pri_context
from classic_methods.kalman_filter import (
    HUBER_C,
    Q_RATIO_GRID,
    _innovation_sigma,
    _prequential_l1,
    _run,
)
from classic_methods.toa_utils import is_pri_target, run_cli, tuned

# Tuned on the validation split (see tune_robust_methods.py).
P_STAY = tuned("imm_filter.P_STAY", 0.9999)  # probability of keeping the current model from one pulse to the next
PROPAGATE_MODES = tuned("imm_filter.PROPAGATE_MODES", False)  # True: model probabilities follow PI over the horizon; False: frozen
T_DOF = 3.0                # degrees of freedom of the Student-t innovation likelihood
SIGMA_FLOOR = 1e-3         # lower bound of the innovation scale (normalised units)

MODELS = ("level", "trend", "periodic")


def bank_settings(z: np.ndarray, max_period: int = 24) -> Dict[str, Dict]:
    """Best (period, q, sigma) per model kind, scored exactly like kalman_filter.select_model."""
    n = len(z)
    max_p = int(min(max_period, max(2, n // 3)))
    eval_start = max_p + 1
    candidates = [("level", 1), ("trend", 1)] + [("periodic", p) for p in range(2, max_p + 1)]
    best: Dict[str, Dict] = {k: {"score": np.inf} for k in MODELS}
    for q in Q_RATIO_GRID:
        for kind, period in candidates:
            _, nu, f = _run(kind, z, period, q, None)
            sigma = _innovation_sigma(nu, f, eval_start)
            _, nu, f = _run(kind, z, period, q, sigma)
            score = _prequential_l1(nu, eval_start)
            if score < best[kind]["score"] - 1e-12:
                best[kind] = {"period": period, "q": q, "sigma": sigma, "score": score}
    return best


def _model_matrices(period: int, qs: Dict[str, float]):
    p = period
    d = p + 1
    avg = np.full((p, p), 1.0 / p)
    ones = np.ones((p, p))

    f_level = np.zeros((d, d))
    f_level[:p, :p] = avg
    q_level = np.zeros((d, d))
    q_level[:p, :p] = qs["level"] * ones

    f_trend = np.zeros((d, d))
    f_trend[:p, :p] = avg
    f_trend[:p, p] = 1.0
    f_trend[p, p] = 1.0
    q_trend = np.zeros((d, d))
    q_trend[:p, :p] = qs["trend"] * ones
    q_trend[p, p] = 0.1 * qs["trend"]

    f_per = np.zeros((d, d))
    f_per[:p, :p] = np.eye(p)

    return [f_level, f_trend, f_per], [q_level, q_trend, None]


def imm_filter(
    z: np.ndarray,
    period: int,
    qs: Dict[str, float],
    sigma: float,
    p_stay: float = P_STAY,
    prior_model: int = 2,
) -> Dict:
    """Runs the IMM over the normalised sequence z. Returns final states and probabilities.

    prior_model: index in MODELS that starts with probability p_stay (the bank's static
    choice). A uniform start would mix the flat level state into the periodic template
    during the first pulses, before the likelihoods have separated the models.
    """
    n = len(z)
    p = period
    d = p + 1
    n_models = 3
    fs, q_mats = _model_matrices(p, qs)
    trans = np.full((n_models, n_models), (1.0 - p_stay) / (n_models - 1))
    np.fill_diagonal(trans, p_stay)

    # Initial state: the first P samples fill the P slots; measurement variance R = 1.
    x0 = np.zeros(d)
    x0[:p] = z[:p]
    c0 = np.eye(d)
    xs = [x0.copy() for _ in range(n_models)]
    cs = [c0.copy() for _ in range(n_models)]
    mu = np.full(n_models, (1.0 - p_stay) / (n_models - 1))
    mu[prior_model] = p_stay
    var_scale = max(sigma, SIGMA_FLOOR) ** 2

    for k in range(p, n):
        ph = k % p
        # --- interaction (mixing) ---
        cbar = trans.T @ mu
        w = (trans * mu[:, None]) / np.maximum(cbar[None, :], 1e-300)
        xm, cm = [], []
        for j in range(n_models):
            xj = sum(w[i, j] * xs[i] for i in range(n_models))
            cj = np.zeros((d, d))
            for i in range(n_models):
                dx = xs[i] - xj
                cj += w[i, j] * (cs[i] + np.outer(dx, dx))
            xm.append(xj)
            cm.append(cj)

        # --- model-matched filtering ---
        loglik = np.zeros(n_models)
        for j in range(n_models):
            f = fs[j]
            x_pred = f @ xm[j]
            c_pred = f @ cm[j] @ f.T
            if q_mats[j] is None:
                c_pred[ph, ph] += qs["periodic"]
            else:
                c_pred = c_pred + q_mats[j]
            s = c_pred[ph, ph] + 1.0
            nu = z[k] - x_pred[ph]
            lim = HUBER_C * np.sqrt(s * var_scale)
            nu_c = min(max(nu, -lim), lim)
            gain = c_pred[:, ph] / s
            xs[j] = x_pred + gain * nu_c
            cs[j] = c_pred - np.outer(gain, c_pred[ph, :])
            loglik[j] = (-0.5 * (T_DOF + 1.0) * np.log1p(nu ** 2 / (T_DOF * s * var_scale))
                         - 0.5 * np.log(s * var_scale))

        # --- model probability update ---
        post = np.log(np.maximum(cbar, 1e-300)) + loglik
        post = np.exp(post - post.max())
        mu = post / post.sum()

    return {"states": xs, "mu": mu, "trans": trans, "matrices": fs, "n": n}


def imm_forecast(
    context: np.ndarray,
    horizon_len: int = 32,
    target_param: str = "PRI",
    max_period: int = 24,
    use_gate: bool = True,
    gate: str = "esm",
    p_stay: float = P_STAY,
    propagate_modes: bool = PROPAGATE_MODES,
) -> np.ndarray:
    """Forecasts future PDW values with the IMM filter over the level / trend / periodic models."""
    raw = np.asarray(context, dtype=np.float64)
    if len(raw) == 0:
        return np.zeros(horizon_len, dtype=np.float64)

    if use_gate and is_pri_target(target_param):
        if gate == "esm":
            x = clean_pri_context(raw)
        else:
            from classic_methods.template_gate import apply_gate

            x = apply_gate(raw, gate)
    else:
        x = raw.copy()

    scale = float(np.std(x))
    if len(x) < 8 or scale < 1e-9:
        return np.full(horizon_len, float(np.median(x)), dtype=np.float64)

    mean = float(np.mean(x))
    z = (x - mean) / scale

    best = bank_settings(z, max_period=max_period)
    period = int(best["periodic"]["period"])
    qs = {k: best[k]["q"] for k in MODELS}
    sigma = min(best[k]["sigma"] for k in MODELS)
    if len(z) <= period + 2:
        return np.full(horizon_len, float(np.median(x)), dtype=np.float64)

    prior = int(np.argmin([best[k]["score"] for k in MODELS]))
    res = imm_filter(z, period, qs, sigma, p_stay=p_stay, prior_model=prior)
    mu = res["mu"].copy()
    states = [s.copy() for s in res["states"]]
    fz = np.zeros(horizon_len)
    for h in range(horizon_len):
        ph = (res["n"] + h) % period
        if propagate_modes:
            mu = res["trans"].T @ mu
        for j in range(3):
            states[j] = res["matrices"][j] @ states[j]
            fz[h] += mu[j] * states[j][ph]

    return fz * scale + mean


if __name__ == "__main__":
    run_cli("PULSAR Classic Baseline 12: IMM filter (level / trend / periodic Kalman models)",
            "IMM Filter (level/trend/periodic)", "imm_filter", imm_forecast)
