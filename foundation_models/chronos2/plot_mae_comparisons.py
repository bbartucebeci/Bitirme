"""Plot new_complex_pri MAE comparisons separately for each context length."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np

from dataset_generator.catalog import PROJECT_ROOT, NEW_COMPLEX_PRI, RADAR_TYPES, ERROR_LEVELS, SCHEMA_V2

CONTEXTS = (96, 256, 512, 992)
KINDS = ("fixed_vs_varying", "univariate_vs_multivariate")
TITLES = {"fixed_vs_varying":"Fixed vs varying", "univariate_vs_multivariate":"Univariate vs multivariate"}
RADAR_LABELS = {"stable":"Stable", "jitter":"Gaussian jitter", "stagger":"Stagger",
                "dwell_and_switch":"Dwell and switch", "sliding":"Sliding", "sinusoidal":"Sinusoidal",
                "triangular_sliding":"Triangular sliding", "markov_agile":"Markov agile"}


def index_metrics(rows: list[dict], config: dict) -> dict:
    lookup = {}
    for row in rows:
        key = (row["task"], int(row["context_len"]), row["profile"], row["radar_type"], row["error_level"])
        if key in lookup:
            raise ValueError(f"Duplicate metric condition: {key}")
        if (int(row["horizon"]) != config["horizon"] or int(row["num_sequences"]) != 200
                or int(row["valid_pulses_evaluated"]) != 6400
                or int(row["skipped_short"]) != 0 or int(row["skipped_no_emitter"]) != 0):
            raise ValueError(f"Incomplete or incompatible metric condition: {key}")
        names = ("mae_pri", "mae_frequency") if row["task"] == "multivariate" else ("mae",)
        if any(not math.isfinite(float(row[name])) or float(row[name]) < 0 for name in names):
            raise ValueError(f"Invalid MAE: {key}")
        lookup[key] = row
    expected = set(itertools.product(config["tasks"], config["context_lens"], config["profiles"],
                                     config["radar_types"], config["error_levels"]))
    if set(lookup) != expected:
        raise ValueError(f"Condition matrix differs from configuration: {len(expected-set(lookup))} missing, {len(set(lookup)-expected)} unexpected")
    return lookup


def pair_condition(lookup: dict, kind: str, target: str, held: str, length: int,
                   radar: str, level: str) -> dict:
    if target not in ("PRI", "Frequency"):
        raise ValueError("Comparisons are limited to PRI and Frequency")
    if kind == "fixed_vs_varying" and held in ("univariate", "multivariate"):
        task = target if held == "univariate" else "multivariate"
        left = lookup[(task, length, "fixed", radar, level)]
        right = lookup[(task, length, "varying", radar, level)]
        labels = ("Fixed", "Varying")
    elif kind == "univariate_vs_multivariate" and held in ("fixed", "varying"):
        left = lookup[(target, length, held, radar, level)]
        right = lookup[("multivariate", length, held, radar, level)]
        labels = ("Univariate", "Multivariate (5 inputs)")
    else:
        raise ValueError("Comparison type and held setting do not match")
    def mae(row):
        return float(row[f"mae_{target.lower()}"] if row["task"] == "multivariate" else row["mae"])
    a, b = mae(left), mae(right)
    return {"dataset_family":NEW_COMPLEX_PRI, "comparison":kind, "target":target,
            "context_len":length, "horizon":32, "held_setting":held, "radar_type":radar,
            "error_level":level, "left_label":labels[0], "right_label":labels[1],
            "mae_left":a, "mae_right":b, "delta_right_minus_left":b-a,
            "unit":"us" if target == "PRI" else "MHz", "test_sequences_each":200}


def verify_sequence_scores(run: Path, lookup: dict) -> int:
    verified = 0
    expected_ids = {f"seq_{i:04d}" for i in range(800, 1000)}
    for (task, length, profile, radar, level), row in lookup.items():
        path = run/task/f"L{length}"/profile/"per_sequence"/f"{radar}_{level}.csv"
        with path.open(newline="", encoding="utf-8-sig") as stream:
            records = list(csv.DictReader(stream))
        if len(records) != 200 or {r["sequence_id"] for r in records} != expected_ids:
            raise ValueError(f"{path}: incomplete/duplicate test sequence IDs")
        if any(int(r["start"]) != 1024-length for r in records):
            raise ValueError(f"{path}: wrong forecast boundary")
        names = ("mae_pri", "mae_frequency") if task == "multivariate" else ("mae",)
        for name in names:
            average = math.fsum(float(r[name]) for r in records)/200
            if not math.isclose(average, float(row[name]), rel_tol=1e-12, abs_tol=1e-10):
                raise ValueError(f"{path}: aggregate {name} differs from per-sequence average")
            verified += 1
    return verified


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def plot_comparison(path: Path, rows: list[dict]) -> None:
    first = rows[0]
    fig, axes = plt.subplots(2, 4, figsize=(19.2, 9.2), sharex=True)
    x = np.arange(len(ERROR_LEVELS))
    for axis, radar in zip(axes.flat, RADAR_TYPES, strict=True):
        panel = {r["error_level"]:r for r in rows if r["radar_type"] == radar}
        a = [panel[level]["mae_left"] for level in ERROR_LEVELS]
        b = [panel[level]["mae_right"] for level in ERROR_LEVELS]
        axis.plot(x, a, "o-", color="#2563eb", linewidth=1.7, markersize=4.5, label=first["left_label"])
        axis.plot(x, b, "s--", color="#d97706", linewidth=1.7, markersize=4.5, label=first["right_label"])
        maximum = max(*a, *b)
        axis.set_ylim(0, maximum*1.13 if maximum > 0 else 1.)
        axis.set_xticks(x, ["Clean", *[f"Lv{i}" for i in range(1,8)]])
        axis.tick_params(axis="both", labelsize=9)
        axis.tick_params(axis="x", labelbottom=True)
        axis.yaxis.set_major_locator(MaxNLocator(nbins=5))
        axis.ticklabel_format(axis="y", style="plain", useOffset=False)
        axis.set_title(RADAR_LABELS[radar], fontsize=12, fontweight="bold")
        axis.set_ylabel(f"MAE ({'µs' if first['target']=='PRI' else 'MHz'})", fontsize=10)
        axis.set_xlabel("Error level", fontsize=10)
        axis.grid(axis="both", linestyle=":", alpha=.3)
    fig.suptitle(f"{NEW_COMPLEX_PRI}: Chronos-2 zero-shot {first['target']} MAE\n"
                 f"{TITLES[first['comparison']]} · {first['held_setting']} · L={first['context_len']}, H=32",
                 fontsize=17, fontweight="bold", y=.985)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5,.912), ncol=2, frameon=False, fontsize=12)
    fig.text(.5,.86,"200 test sequences per condition. Lower MAE is better. Each radar panel has its own linear y-axis scale.",
             ha="center", fontsize=10)
    fig.subplots_adjust(left=.055, right=.985, bottom=.075, top=.815, wspace=.3, hspace=.43)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Completed new_complex_pri zero-shot run")
    parser.add_argument("--output-dir", type=Path, help="Default: outputs/new_complex_pri/comparisons/<run>")
    args = parser.parse_args()
    run = args.source.resolve()
    config = json.loads((run/"run_config.json").read_text(encoding="utf-8"))
    manifest = json.loads((run/"test_windows.json").read_text(encoding="utf-8"))
    if (config["window_mode"] != "boundary" or config.get("dataset_family") != NEW_COMPLEX_PRI
            or config["dataset_size"] != "1000x1056" or config["horizon"] != 32
            or config["regime"] != "zero_shot" or config["max_test_seqs"] is not None
            or manifest["meta"]["schema_version"] != SCHEMA_V2):
        parser.error("This comparison is scoped to the full new_complex_pri boundary zero-shot experiment")
    for name, expected in (("context_lens",CONTEXTS),("profiles",("fixed","varying")),
                           ("tasks",("PRI","Frequency","multivariate")),
                           ("radar_types",RADAR_TYPES),("error_levels",ERROR_LEVELS)):
        if len(config[name]) != len(expected) or set(config[name]) != set(expected):
            parser.error(f"Unexpected {name}: {config[name]}")
    output = (args.output_dir or PROJECT_ROOT/"outputs"/NEW_COMPLEX_PRI/"comparisons"/run.name).resolve()
    if output == run or output in run.parents:
        parser.error("Output cannot replace the source run or its parent directories")
    if output.exists() and any(output.iterdir()):
        parser.error(f"Output already contains files: {output}")
    source_csv = run/"metrics.csv"
    original_hash = hashlib.sha256(source_csv.read_bytes()).hexdigest()
    with source_csv.open(newline="", encoding="utf-8-sig") as stream:
        lookup = index_metrics(list(csv.DictReader(stream)), config)
    verified = verify_sequence_scores(run, lookup)
    print(f"[VERIFIED] {len(lookup)} conditions; {verified} MAE values reconciled with per-sequence scores", flush=True)
    output.mkdir(parents=True, exist_ok=True)
    all_rows, plots = [], []
    readme = [f"# {NEW_COMPLEX_PRI}: fixed/varying and univariate/multivariate MAE", "",
              "Chronos-2 zero-shot, H=32, 200 test sequences per condition. Source run: `"+run.name+"`.",
              "Each figure belongs to one L and one target. Its eight panels show individual radar types; x-axis categories are clean and error_lv1–error_lv7.",
              "Fixed/varying comparisons hold input mode constant. Univariate/multivariate comparisons hold profile constant.",
              "Multivariate means five input channels, scored here for PRI or Frequency. PRI uses µs; Frequency uses MHz.",
              "Raw MAE definitions and existing per-sequence rounding are retained. Radar types/error levels are not averaged together.",
              "Panel y-axes start at zero and have independent linear scales. Error levels are configured categories, not a monotone missing-rate axis.",
              "The fixed and varying populations have different profile definitions; these are absolute MAE comparisons, not normalized errors or matched per-sequence parameter draws.", ""]
    for kind in KINDS:
        readme += [f"## {TITLES[kind]}", "", "| Target | Held setting | L=96 | L=256 | L=512 | L=992 |", "|---|---|---|---|---|---|"]
        settings = ("univariate","multivariate") if kind == "fixed_vs_varying" else ("fixed","varying")
        for target in ("PRI","Frequency"):
            for held in settings:
                links = []
                for length in CONTEXTS:
                    rows = [pair_condition(lookup,kind,target,held,length,radar,level) for radar in RADAR_TYPES for level in ERROR_LEVELS]
                    name = f"{NEW_COMPLEX_PRI}_{kind}_{target.lower()}_{held}_L{length}"
                    png = output/kind/f"L{length}"/f"{name}.png"
                    plot_comparison(png, rows)
                    write_csv(png.with_suffix(".csv"), rows)
                    all_rows.extend(rows); plots.append(png.relative_to(output).as_posix())
                    links.append(f"[PNG]({png.relative_to(output).as_posix()})")
                    print(f"[PLOT] {len(plots)}/32: {png.name}", flush=True)
                readme.append("| "+" | ".join([target,held,*links])+" |")
        readme.append("")
    write_csv(output/"comparisons.csv", all_rows)
    source_link=Path(os.path.relpath(run/"report.md",output)).as_posix()
    readme += [f"[Source experiment]({source_link}) · [All numeric comparisons](comparisons.csv)", "",
               "CSV delta_right_minus_left is Varying−Fixed or Multivariate−Univariate. Negative means the right-hand series has lower MAE; it is not a percentage.", ""]
    (output/"README.md").write_text("\n".join(readme),encoding="utf-8")
    if hashlib.sha256(source_csv.read_bytes()).hexdigest() != original_hash:
        raise ValueError("Source metrics changed during plotting")
    audit={"dataset_family":NEW_COMPLEX_PRI,"source_run":run.name,"source_metrics_sha256":original_hash,
           "metric_conditions":len(lookup),"unique_mae_values_verified":verified,"comparison_rows":len(all_rows),
           "png_count":len(plots),"context_lens":list(CONTEXTS),"horizon":32,"test_sequences_each":200,
           "plots":plots,"source_unchanged":True}
    (output/"validation.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
    print(f"[DONE] {len(plots)} PNGs; {len(all_rows)} comparisons. {output/'README.md'}",flush=True)


if __name__=="__main__":main()
