#!/usr/bin/env python3
"""Runs and compares the robust-periodicity methods against the existing classic baselines.

Why the baselines are re-run here
---------------------------------
`dataset_generator/generate_datasets.py --seed` seeds only the profile sampling; the
channel / receiver noise uses NumPy's global generator, so every generation of the
datasets gives different sequences. The committed results/classic_methods/<method>/
metrics.csv files therefore belong to an older realisation of the data. For a
like-for-like table all methods are evaluated on the SAME test sequences: the six
existing baselines are re-run (unchanged code, default arguments) into

    results/classic_methods/robust_periodicity/baselines_rerun/<method>/<profile>_pri/

and the committed files are left untouched. New methods write to the standard location
results/classic_methods/<new_method>/<profile>_pri/.

Usage:
    python classic_methods/compare_robust_methods.py run --method sdif --profile-mode fixed
    python classic_methods/compare_robust_methods.py run --method period_estimation --profile-mode varying
    python classic_methods/compare_robust_methods.py report
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Callable, Dict, List, Tuple

import numpy as np
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classic_methods.common import (
    DEFAULT_DATASETS_ROOT,
    ERROR_LEVELS,
    RADAR_TYPES,
    compute_metrics,
    evaluate_method_across_benchmarks,
    load_dataset_sequences,
)

RESULTS_ROOT = PROJECT_ROOT / "results" / "classic_methods"
RERUN_ROOT = RESULTS_ROOT / "robust_periodicity" / "baselines_rerun"
REPORT_PATH = RESULTS_ROOT / "comparison_robust_periodicity.md"
PROFILES = ["fixed", "varying"]
NOISY = ["error_lv1", "error_lv2", "error_lv3"]

# slug -> (benchmark name, short table label)
BASELINES: Dict[str, Tuple[str, str]] = {
    "rolling_median": ("Rolling Median (W=32)", "Rolling median"),
    "period_estimation": ("Period Estimation (P_max=24)", "Period estimation"),
    "hidden_markov_model": ("Hidden Markov Model (Baum-Welch + Viterbi)", "HMM"),
    "kalman_filter": ("Kalman Filter Bank", "Kalman bank"),
    "exponential_smoothing": ("Exponential Smoothing (AICc-selected ETS)", "Exp. smoothing"),
    "arima": ("ARIMA (Box-Jenkins, AIC-selected)", "ARIMA"),
}
NEW_METHODS: Dict[str, Tuple[str, str]] = {
    "cdif": ("CDIF Histogram + TOA Grid", "CDIF"),
    "sdif": ("SDIF Histogram + TOA Grid", "SDIF"),
    "pri_transform": ("PRI Transform + TOA Grid", "PRI transform"),
    "lomb_scargle": ("Lomb-Scargle + TOA Grid", "Lomb-Scargle"),
    "toa_grid_fit": ("TOA Grid Fit (RANSAC)", "TOA grid fit"),
    "period_estimation_template_gate": ("Period Estimation (P_max=24) (template gate)", "Period est. + template gate"),
    "kalman_filter_template_gate": ("Kalman Filter Bank (template gate)", "Kalman + template gate"),
    "imm_filter": ("IMM Filter (level/trend/periodic)", "IMM filter"),
    "forecast_combination": ("Forecast Combination (weighted median)", "Forecast combination"),
}
REFERENCE = "period_estimation"  # current best baseline


def get_predict_fn(slug: str) -> Callable:
    if slug == "rolling_median":
        from classic_methods.rolling_median import rolling_median_forecast as fn
    elif slug == "hidden_markov_model":
        from classic_methods.hidden_markov_model import hmm_forecast as fn
    elif slug == "exponential_smoothing":
        from classic_methods.exponential_smoothing import exponential_smoothing_forecast as fn
    elif slug == "arima":
        from classic_methods.arima import arima_forecast as fn
    else:
        from classic_methods.tune_robust_methods import get_predict_fn as robust_fn

        fn = robust_fn(slug)
    return fn


def metrics_path(slug: str, profile: str) -> Path:
    root = RERUN_ROOT if slug in BASELINES else RESULTS_ROOT
    return root / slug / f"{profile}_pri" / "metrics.csv"


def run_method(slug: str, profile: str, max_test_seqs: int = 200, radar_types=None) -> None:
    """Benchmarks one method on one profile.

    The work is done one radar type at a time into <results_dir>/parts/<radar_type>/ and
    then merged, so an interrupted run of a slow method (ARIMA, forecast combination)
    continues where it stopped instead of starting again.
    """
    name = (BASELINES.get(slug) or NEW_METHODS[slug])[0]
    fn = get_predict_fn(slug)
    out_dir = metrics_path(slug, profile).parent
    for rtype in (radar_types or RADAR_TYPES):
        part_csv = out_dir / "parts" / rtype / "metrics.csv"
        if part_csv.exists() and len(pd.read_csv(part_csv)) == len(ERROR_LEVELS):
            print(f"[SKIP] {slug}/{profile}/{rtype}: already done")
            continue
        evaluate_method_across_benchmarks(
            method_name=name,
            method_slug=slug,
            predict_fn=lambda ctx, h, p: fn(ctx, h, p),
            profile_mode=profile,
            target_param="PRI",
            radar_types=[rtype],
            max_test_seqs=max_test_seqs,
            results_dir=part_csv.parent,
        )
    if radar_types is None:  # partial runs (parallel workers) leave the merge to a final full call
        merge_parts(slug, profile)


def merge_parts(slug: str, profile: str) -> None:
    """Joins the per-radar-type parts into the standard metrics.csv / report.md / plots."""
    import shutil

    out_dir = metrics_path(slug, profile).parent
    parts = [out_dir / "parts" / r for r in RADAR_TYPES]
    if not all((d / "metrics.csv").exists() for d in parts):
        return
    df = pd.concat([pd.read_csv(d / "metrics.csv") for d in parts], ignore_index=True)
    df.to_csv(out_dir / "metrics.csv", index=False)

    texts = [(d / "report.md").read_text(encoding="utf-8").splitlines() for d in parts]
    header = [ln for ln in texts[0] if not ln.startswith("| `")]
    rows = [ln for t in texts for ln in t if ln.startswith("| `")]
    (out_dir / "report.md").write_text("\n".join(header + rows) + "\n", encoding="utf-8")

    (out_dir / "plots").mkdir(exist_ok=True)
    for d in parts:
        for png in (d / "plots").glob("*.png"):
            shutil.copy2(png, out_dir / "plots" / png.name)
    shutil.rmtree(out_dir / "parts")
    print(f"[MERGED] {out_dir / 'metrics.csv'}")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _load(slug: str, profile: str) -> pd.DataFrame:
    path = metrics_path(slug, profile)
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run: compare_robust_methods.py run --method {slug} --profile-mode {profile}")
    return pd.read_csv(path).set_index(["radar_type", "error_level"])


def _fmt(values: List[float], fmt: str, best: str) -> List[str]:
    target = min(values) if best == "min" else max(values)
    return [f"**{format(v, fmt)}**" if np.isclose(v, target, atol=5e-3) else format(v, fmt) for v in values]


def horizon_event_breakdown(slugs: List[str], max_test_seqs: int = 200) -> pd.DataFrame:
    """MAE split by whether the 32-pulse horizon itself contains a missed or false pulse.

    Ground truth is used here for the ANALYSIS of the errors only (never for forecasting):
    a horizon is "undisturbed" when all 32 rows are emitter pulses and every measured
    Delta-TOA equals its source PRI within 20 us.
    """
    rows = []
    fns = {s: get_predict_fn(s) for s in slugs}
    for profile in PROFILES:
        for rtype in ["stagger", "dwell_and_switch", "sliding"]:
            for level in NOISY:
                seqs = load_dataset_sequences(
                    DEFAULT_DATASETS_ROOT / profile / rtype / f"1000x128_{level}", split="test", max_seqs=max_test_seqs
                )
                acc = {s: {True: [], False: []} for s in slugs}
                for _, obs, tgt, mask in seqs:
                    total = len(obs)
                    if total <= 40:
                        continue
                    c = 96 if total >= 128 else total - 32
                    ctx, gt, m, obs_h = obs[:c], tgt[c:c + 32], mask[c:c + 32], obs[c:c + 32]
                    undisturbed = bool(m.all() and np.all(np.abs(obs_h - gt) < 20.0))
                    for s in slugs:
                        r = compute_metrics(fns[s](ctx, 32, "PRI"), gt, tolerance=10.0, mask=m)
                        if r["valid_pulses"] > 0:
                            acc[s][undisturbed].append(r["mae"])
                n_clean = len(acc[slugs[0]][True])
                n_all = n_clean + len(acc[slugs[0]][False])
                row = {"profile": profile, "radar_type": rtype, "error_level": level,
                       "undisturbed_pct": 100.0 * n_clean / max(n_all, 1)}
                for s in slugs:
                    row[f"{s}_undisturbed"] = float(np.mean(acc[s][True])) if acc[s][True] else float("nan")
                    row[f"{s}_disturbed"] = float(np.mean(acc[s][False])) if acc[s][False] else float("nan")
                rows.append(row)
    return pd.DataFrame(rows)


def build_report(with_breakdown: bool = True) -> None:
    slugs = list(BASELINES) + list(NEW_METHODS)
    labels = {s: (BASELINES.get(s) or NEW_METHODS[s])[1] for s in slugs}
    data = {(s, p): _load(s, p) for s in slugs for p in PROFILES}

    def mean_over(slug, profile, col, levels, rtypes=RADAR_TYPES):
        df = data[(slug, profile)]
        return float(np.mean([df.loc[(r, e), col] for r in rtypes for e in levels]))

    lines = [
        "# Robust-periodicity classic methods vs. existing classic baselines (PRI)",
        "",
        "Protocol: 96-pulse context, 32-pulse horizon, errors on emitter pulses only (false pulses",
        "masked with the ground-truth labels), target = source PRI, gate = +/-10 us. Test split,",
        "200 sequences per dataset. Forecasts use the context only; hyperparameters were chosen on",
        "the validation split (`results/classic_methods/robust_tuning_val/`).",
        "",
        "All methods, old and new, were run on the same test sequences. The existing baselines were",
        "re-run for this table (`robust_periodicity/baselines_rerun/`) because the dataset generator",
        "does not seed the noise, so the committed `metrics.csv` files come from a different",
        "realisation of the data. Best value per column in **bold**. New methods are below the line.",
        "",
        "## 1. Summary: mean over error levels 1-3 and all five radar types",
        "",
        "| Method | MAE fixed (us) | MAE varying (us) | Hit rate fixed (%) | Hit rate varying (%) | RMSE fixed (us) | RMSE varying (us) | Runtime (ms / sequence) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    cols = []
    for s in slugs:
        lat = np.mean([data[(s, p)]["latency_us_per_seq"].mean() for p in PROFILES]) / 1e3
        cols.append([
            mean_over(s, "fixed", "mae_us", NOISY), mean_over(s, "varying", "mae_us", NOISY),
            mean_over(s, "fixed", "gate_hit_rate_pct", NOISY), mean_over(s, "varying", "gate_hit_rate_pct", NOISY),
            mean_over(s, "fixed", "rmse_us", NOISY), mean_over(s, "varying", "rmse_us", NOISY), lat,
        ])
    arr = np.array(cols)
    fmts = [(".2f", "min"), (".2f", "min"), (".1f", "max"), (".1f", "max"), (".2f", "min"), (".2f", "min"), (".1f", "min")]
    cells = [_fmt(list(arr[:, j]), f, b) for j, (f, b) in enumerate(fmts)]
    for i, s in enumerate(slugs):
        if s == next(iter(NEW_METHODS)):
            lines.append("| *new methods* | | | | | | | |")
        lines.append(f"| {labels[s]} | " + " | ".join(cells[j][i] for j in range(len(fmts))) + " |")

    for metric, title, fmt, best in [
        ("mae_us", "MAE (us)", ".2f", "min"),
        ("gate_hit_rate_pct", "Gate hit rate (%)", ".1f", "max"),
    ]:
        for profile in PROFILES:
            lines += [
                "",
                f"## {'2' if metric == 'mae_us' else '3'}. {title} per radar type, mean over error levels 1-3 [{profile}]",
                "",
                "| Method | " + " | ".join(f"`{r}`" for r in RADAR_TYPES) + " |",
                "|---|" + "---:|" * len(RADAR_TYPES),
            ]
            arr = np.array([[mean_over(s, profile, metric, NOISY, [r]) for r in RADAR_TYPES] for s in slugs])
            cells = [_fmt(list(arr[:, j]), fmt, best) for j in range(len(RADAR_TYPES))]
            for i, s in enumerate(slugs):
                lines.append(f"| {labels[s]} | " + " | ".join(cells[j][i] for j in range(len(RADAR_TYPES))) + " |")

    hard = [(r, e) for r in ["stagger", "dwell_and_switch"] for e in ["error_lv2", "error_lv3"]]
    for profile in PROFILES:
        lines += [
            "",
            f"## 4. Stagger and dwell-and-switch at error levels 2-3: MAE in us (hit rate in %) [{profile}]",
            "",
            "| Method | " + " | ".join(f"`{r}` {e[-3:]}" for r, e in hard) + " |",
            "|---|" + "---:|" * len(hard),
        ]
        mae = np.array([[data[(s, profile)].loc[k, "mae_us"] for k in hard] for s in slugs])
        hit = np.array([[data[(s, profile)].loc[k, "gate_hit_rate_pct"] for k in hard] for s in slugs])
        best = mae.min(axis=0)
        for i, s in enumerate(slugs):
            row = []
            for j in range(len(hard)):
                txt = f"{mae[i, j]:.1f} ({hit[i, j]:.0f})"
                row.append(f"**{txt}**" if np.isclose(mae[i, j], best[j], atol=5e-2) else txt)
            lines.append(f"| {labels[s]} | " + " | ".join(row) + " |")

    lines += [
        "",
        "## 5. Clean datasets (no receiver errors): mean MAE in us over the five radar types",
        "",
        "| Method | fixed | varying |",
        "|---|---:|---:|",
    ]
    for s in slugs:
        lines.append(f"| {labels[s]} | {mean_over(s, 'fixed', 'mae_us', ['clean']):.2f} | "
                     f"{mean_over(s, 'varying', 'mae_us', ['clean']):.2f} |")

    if with_breakdown:
        probe = [REFERENCE, "toa_grid_fit"]
        bd = horizon_event_breakdown(probe)
        bd.to_csv(RESULTS_ROOT / "robust_periodicity" / "horizon_event_breakdown.csv", index=False)
        lines += [
            "",
            "## 6. Where the remaining error comes from",
            "",
            "The benchmark scores horizon row h against the PRI of the h-th *received* pulse. When a",
            "pulse is missed (or a false pulse is received) inside the 32-pulse horizon, every later row",
            "moves one step along the pattern. That event lies in the future, so no forecast that uses",
            "only the context can follow it. The table splits the test sequences by whether the horizon",
            "itself is undisturbed (all 32 rows are emitter pulses whose measured interval equals the",
            "source PRI). Ground truth is used for this split only, not for forecasting.",
            "",
            "| Profile | Radar type | Level | Undisturbed horizons (%) | "
            + " | ".join(f"{labels[s]}: MAE undisturbed / disturbed (us)" for s in probe) + " |",
            "|---|---|---|---:|" + "---:|" * len(probe),
        ]
        for _, r in bd.iterrows():
            lines.append(
                f"| {r['profile']} | `{r['radar_type']}` | `{r['error_level']}` | {r['undisturbed_pct']:.0f} | "
                + " | ".join(f"{r[f'{s}_undisturbed']:.2f} / {r[f'{s}_disturbed']:.1f}" for s in probe) + " |"
            )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[SAVED] {REPORT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run / compare the robust-periodicity classic methods")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run", help="Benchmark one method on the test split")
    p_run.add_argument("--method", required=True, choices=list(BASELINES) + list(NEW_METHODS))
    p_run.add_argument("--profile-mode", choices=PROFILES + ["both"], default="both")
    p_run.add_argument("--max-test-seqs", type=int, default=200)
    p_run.add_argument("--radar-types", nargs="*", choices=RADAR_TYPES, default=None,
                       help="Only run these parts (no merge); used to spread a slow method over processes")
    p_rep = sub.add_parser("report", help="Write the Markdown comparison")
    p_rep.add_argument("--no-breakdown", action="store_true")
    args = parser.parse_args()

    if args.cmd == "run":
        for profile in (PROFILES if args.profile_mode == "both" else [args.profile_mode]):
            run_method(args.method, profile, args.max_test_seqs, args.radar_types)
    else:
        (RESULTS_ROOT / "robust_periodicity").mkdir(parents=True, exist_ok=True)
        build_report(with_breakdown=not args.no_breakdown)


if __name__ == "__main__":
    main()
