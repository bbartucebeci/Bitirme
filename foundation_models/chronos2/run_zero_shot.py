"""Zero-shot PRI/RF experiment on the complex single-radar benchmark; no training stages."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
import yaml

from dataset_generator.catalog import RADAR_TYPES, ERROR_LEVELS, PROJECT_ROOT, NEW_COMPLEX_PRI, OLD_COMPLEX_PRI, family_for_schema
from dataset_generator.sequence_io import SCHEMA_V2, read_sequence_frame, is_boundary_dataset, boundary_start
from foundation_models.chronos2.adapter import MODEL_ID, load_pipeline, predict_median
from foundation_models.common.dataset import CHANNELS, load_split
from foundation_models.common.metrics import aggregate, score_single, score_window
from foundation_models.common.plotting import save_forecast_plot, save_multivariate_forecast_plot
from foundation_models.common.windowing import WINDOW_SEED, draw_random_start, file_sha256, window_key

TASKS = ("PRI", "Frequency", "multivariate")
CONTEXT_LENS = (96, 256, 512, 992)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def code_fingerprint() -> str:
    names = ("chronos2/run_zero_shot.py", "chronos2/adapter.py", "common/dataset.py",
             "common/windowing.py", "common/metrics.py", "common/plotting.py")
    digest = hashlib.sha256()
    for name in names:
        digest.update(name.encode())
        digest.update((PROJECT_ROOT / "foundation_models" / name).read_bytes())
    digest.update((PROJECT_ROOT/"dataset_generator"/"sequence_io.py").read_bytes())
    digest.update((PROJECT_ROOT/"dataset_generator"/"catalog.py").read_bytes())
    return digest.hexdigest()


def prepare_inputs(root: Path, size: str, profiles, radar_types, levels, lengths,
                   horizon: int, mode: str, seed: int, limit: int | None,
                   plot_id: str | None) -> tuple[pd.DataFrame, dict]:
    """Inspect only test CSVs, record hashes and exact windows, never generate data."""
    collection_path=root.parent/"collection.json"
    if collection_path.is_file():
        collection=json.loads(collection_path.read_text(encoding="utf-8"))
        if collection.get("status")!="complete":
            raise ValueError("Dataset collection is incomplete; wait for generation to finish")
    sequence_count, intervals = map(int, size.split("x"))
    if any(length + horizon > intervals for length in lengths):
        raise ValueError(f"Context + horizon exceeds {intervals} generated intervals")
    rows, hashes, windows, sequence_lengths, examples = [], {}, {}, {}, {}
    metadata_hashes = {}
    schemas = set()
    for profile in profiles:
        for radar in radar_types:
            for level in levels:
                folder = root / profile / radar / f"{size}_{level}"
                metadata_path = folder / "metadata.yaml"
                metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
                schemas.add(metadata.get("schema_version","complex_pri_v1"))
                if (metadata["profile_mode"], metadata["radar_type"], metadata["error_level"]) != (profile, radar, level):
                    raise ValueError(f"{folder}: metadata condition mismatch")
                if metadata["sequence_count"] != sequence_count or metadata["expected_pulses_per_sequence"] != intervals:
                    raise ValueError(f"{folder}: metadata size mismatch")
                files = sorted((folder / "test").glob("seq_*.csv"))
                expected = int(metadata["split"]["test"]["sequence_count"])
                if len(files) != expected:
                    raise ValueError(f"{folder}: expected {expected} test CSVs, found {len(files)}")
                files = files[:limit] if limit is not None else files
                if not files:
                    raise ValueError(f"{folder}: empty selected test split")
                example = plot_id or files[0].stem
                if example not in {file.stem for file in files}:
                    raise ValueError(f"{folder}: plot sequence {example} is outside selected test CSVs")
                condition = f"{profile}/{radar}/{level}"
                metadata_hashes[condition] = file_sha256(metadata_path)
                examples[condition] = example
                for csv_file in files:
                    frame = read_sequence_frame(csv_file)
                    if len(frame) > 1 and float(frame.Measured_Delta_TOA.iloc[0]) == 0:
                        frame = frame.iloc[1:]
                    if len(frame) != intervals:
                        raise ValueError(f"{csv_file}: expected {intervals} intervals after anchor")
                    key = f"{condition}/{csv_file.stem}"
                    hashes[key] = file_sha256(csv_file)
                    sequence_lengths[key] = len(frame)
                    for length in lengths:
                        start = (boundary_start(metadata, length, horizon, mode) if is_boundary_dataset(metadata) or mode == "boundary" else
                                 intervals-length-horizon if mode == "tail" else
                                 draw_random_start(intervals, length, horizon, seed,
                                                   window_key(profile, radar, level, csv_file.stem, length))
                                 if mode == "random" else 0)
                        if not frame.Radar_ID.iloc[start+length:start+length+horizon].eq("R_SINGLE").any():
                            raise ValueError(f"{csv_file}: target window has no emitter pulses")
                        windows[window_key(profile, radar, level, csv_file.stem, length)] = start
                rows.append({"profile": profile, "radar_type": radar, "error_level": level,
                             "test_sequences": len(files), "intervals": intervals, "plot_sequence_id": example})
                print(f"[PREFLIGHT] {condition}: {len(files)} test sequences", flush=True)
    if len(schemas)!=1:
        raise ValueError("A run cannot mix dataset protocols")
    manifest = {
        "meta": {"dataset_size": size, "split": "test", "context_lens": list(lengths),
                 "horizon_len": horizon, "seed": seed, "window_mode": mode,"schema_version":next(iter(schemas)),
                 "dataset_family":family_for_schema(next(iter(schemas)))},
        "windows": windows, "sequence_lengths": sequence_lengths, "sequence_sha256": hashes,
        "metadata_sha256": metadata_hashes, "plot_sequences": examples,
    }
    return pd.DataFrame(rows), manifest


def score_prediction(task: str, prediction, window) -> dict | None:
    if task != "multivariate":
        return score_single(prediction[0], window.target[0], window.emitter_mask, task, unrounded=True)
    # Chronos receives all five context channels and predicts them jointly.
    # The requested experiment reports only PRI and RF errors.
    result = score_window(prediction, window.target, window.emitter_mask)
    if result is None:
        return None
    wanted = {"valid_pulses_evaluated", "mae_pri", "rmse_pri", "hit_rate_pri",
              "mae_frequency", "rmse_frequency", "hit_rate_frequency"}
    return {key: value for key, value in result.items() if key in wanted}


def plot_forecast(path: Path, example: dict, task: str, title: str) -> None:
    context, target, prediction = (np.asarray(example[key]) for key in ("context", "target", "prediction"))
    if task == "multivariate":
        indices = [CHANNELS.index("PRI"), CHANNELS.index("Frequency")]
        save_multivariate_forecast_plot(path, title, context[indices], target[indices], prediction[indices],
                                       tolerances=[10., 2.], param_names=["PRI", "Frequency"], units=["µs", "MHz"])
    else:
        save_forecast_plot(path, title, context[0], target[0], prediction[0],
                           tolerance=10. if task == "PRI" else 2., param_label=task,
                           unit="µs" if task == "PRI" else "MHz")


def evaluate_one(pipeline, folder: Path, profile: str, radar: str, level: str,
                 task: str, length: int, horizon: int, batch_size: int,
                 limit: int | None, mode: str, seed: int, manifest: dict,
                 output: Path, plots: bool = True) -> dict:
    condition = f"{profile}/{radar}/{level}"
    if file_sha256(folder / "metadata.yaml") != manifest["metadata_sha256"][condition]:
        raise ValueError(f"{folder}: metadata changed after preflight")
    loaded = load_split(folder, "test", task, length, horizon, limit,
                        window_mode=mode, window_seed=seed, window_manifest=manifest)
    if loaded.skipped_short or not loaded.windows:
        raise ValueError(f"{folder}: incomplete forecast windows")
    # Verify fingerprints in tail/first mode too (the common loader enforces them for random).
    if mode != "random":
        for window in loaded.windows:
            key = f"{condition}/{window.sequence_id}"
            if file_sha256(folder / "test" / f"{window.sequence_id}.csv") != manifest["sequence_sha256"][key]:
                raise ValueError(f"{key}: CSV changed after preflight")
    scores, sequence_rows, example = [], [], None
    inference_seconds = 0.
    example_id = manifest["plot_sequences"][condition]
    for begin in range(0, len(loaded.windows), batch_size):
        batch = loaded.windows[begin:begin+batch_size]
        started = time.perf_counter()
        predictions = predict_median(pipeline, [window.context for window in batch], horizon, batch_size)
        elapsed = time.perf_counter()-started
        inference_seconds += elapsed
        for window, prediction in zip(batch, predictions, strict=True):
            score = score_prediction(task, prediction, window)
            if score is not None:
                scores.append(score)
                sequence_rows.append({"sequence_id": window.sequence_id, "start": window.start,
                                      "batch_amortized_inference_ms": elapsed*1000/len(batch), **score})
            if window.sequence_id == example_id:
                example = {"sequence_id": window.sequence_id, "start": window.start,
                           "context": window.context.tolist(), "target": window.target.tolist(),
                           "prediction": prediction.tolist(), "emitter_mask": window.emitter_mask.tolist()}
        print(f"[BATCH] {task}/L{length}/{condition}: {min(begin+batch_size,len(loaded.windows))}/{len(loaded.windows)}", flush=True)
    if example is None:
        raise ValueError(f"{folder}: missing requested example")
    row = {"task": task, "context_len": length, "horizon": horizon, "profile": profile,
           "radar_type": radar, "error_level": level, "num_sequences": len(scores),
           "skipped_short": loaded.skipped_short, "skipped_no_emitter": len(loaded.windows)-len(scores),
           "inference_seconds": inference_seconds, **aggregate(scores)}
    name = f"{radar}_{level}"
    output.mkdir(parents=True, exist_ok=True)
    per_sequence = output / "per_sequence" / f"{name}.csv"
    per_sequence.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(sequence_rows).to_csv(per_sequence, index=False)
    write_json(output / "examples" / f"{name}.json", example)
    if plots:
        family=manifest.get("meta",{}).get("dataset_family",family_for_schema(manifest.get("meta",{}).get("schema_version","complex_pri_v1")))
        title = f"Chronos-2 zero-shot [{family}] | {task} | {profile}/{radar}/{level} | L={length}, H={horizon} | {example_id}"
        plot_forecast(output / "plots" / f"{family}_{name}.png", example, task, title)
    # Completion marker is written last so interrupted jobs are not silently resumed.
    write_json(output / "completed" / f"{name}.json", row)
    return row


def export_reports(rows: list[dict], output: Path, config: dict) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    frame.to_csv(output / "metrics.csv", index=False)
    links = []
    for (task, length, profile), group in frame.groupby(["task", "context_len", "profile"], sort=False):
        folder = output / task / f"L{length}" / profile
        folder.mkdir(parents=True, exist_ok=True)
        columns = ["radar_type", "error_level", "num_sequences", "skipped_short", "skipped_no_emitter"]
        columns += (["mae_pri", "rmse_pri", "hit_rate_pri", "mae_frequency", "rmse_frequency", "hit_rate_frequency"]
                    if task == "multivariate" else ["mae", "rmse", "hit_rate_pct"])
        columns += ["valid_pulses_evaluated"]
        table = group[columns]
        table.to_csv(folder / "metrics.csv", index=False)
        text = [f"# Chronos-2 zero-shot: {task}, {profile}, L={length}, H={config['horizon']}", "",
                "MAE/RMSE/hit rate are means of per-sequence emitter-only scores, matching the existing evaluator.",
                "PRI gate: ±10 µs. Frequency gate: ±2 MHz. Multivariate input: all five PDW channels.", "",
                table.round(6).to_markdown(index=False), ""]
        (folder / "report.md").write_text("\n".join(text), encoding="utf-8")
        links.append(f"- [{task}, L={length}, {profile}]({task}/L{length}/{profile}/report.md)")
    for (task, radar), group in frame.groupby(["task", "radar_type"], sort=False):
        folder = output / "by_radar" / task / radar
        folder.mkdir(parents=True, exist_ok=True)
        group.to_csv(folder / "metrics.csv", index=False)
        (folder / "report.md").write_text(f"# {radar}: {task}\n\n"+group.round(6).to_markdown(index=False)+"\n",encoding="utf-8")
    protocol = ["# Chronos-2 complex PRI zero-shot experiment", "",
                f"Dataset: {config.get('dataset_family', NEW_COMPLEX_PRI if config['window_mode']=='boundary' else OLD_COMPLEX_PRI)}. Completed conditions: {len(frame)}. Mode: {config['window_mode']}. Horizon: {config['horizon']}.",
                "No fitting or training data are used. Only test CSVs are scored; input files are never modified.",
                "Tail mode shares the final targets; boundary mode shares the first H consecutive source pulses after the stored context boundary.",
                "PRI input is observed Delta-TOA; PRI target is source PRI, following the repository definition.",
                "Frequency input/target retain the repository's measured Frequency definition.",
                "Multivariate inference receives five channels; only PRI and Frequency are scored and plotted.",
                "No cross-radar/error-level averages are used for comparison. No context cleaning is applied.",
                "Timing is wall time for prediction plus CPU conversion; per-sequence timing is batch-amortized.", "",
                "## Condition reports", "", *links, ""]
    (output / "report.md").write_text("\n".join(protocol),encoding="utf-8")
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets-root", type=Path, required=True, help="Directory containing fixed/ and varying/")
    parser.add_argument("--dataset-size", default="1000x1024")
    parser.add_argument("--profiles", nargs="+", choices=("fixed", "varying"), default=("fixed", "varying"))
    parser.add_argument("--radar-types", nargs="+", choices=RADAR_TYPES, default=RADAR_TYPES)
    parser.add_argument("--error-levels", nargs="+", choices=ERROR_LEVELS, default=ERROR_LEVELS)
    parser.add_argument("--tasks", nargs="+", choices=TASKS, default=TASKS)
    parser.add_argument("--context-lens", nargs="+", type=int, default=CONTEXT_LENS)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--window-mode", choices=("tail", "random", "first", "boundary"), default="tail")
    parser.add_argument("--window-seed", type=int, default=WINDOW_SEED)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-test-seqs", type=int)
    parser.add_argument("--plot-sequence-id", help="Default: first selected test sequence (seq_0800 in full datasets)")
    parser.add_argument("--model-id", default=MODEL_ID, help="Base model ID or local base-model snapshot; no LoRA checkpoint")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--coverage-only", action="store_true", help="Preflight and save manifests without loading any model")
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    if min(*args.context_lens,args.horizon,args.batch_size) <= 0 or (args.max_test_seqs is not None and args.max_test_seqs <= 0):
        parser.error("Lengths, batch size and optional test limit must be positive")
    for name in ("profiles", "radar_types", "error_levels", "tasks", "context_lens"):
        if len(getattr(args,name)) != len(set(getattr(args,name))):
            parser.error(f"--{name.replace('_','-')} contains duplicate entries")
    root = args.datasets_root.resolve()
    if (Path(args.model_id)/"adapter_config.json").is_file():
        parser.error("Zero-shot requires a base model, not a fine-tuned adapter")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")
    protocol_tag=NEW_COMPLEX_PRI if args.window_mode=="boundary" else OLD_COMPLEX_PRI
    output = (args.output_dir or PROJECT_ROOT/"results"/"chronos2"/"zero_shot"/protocol_tag/f"{root.parent.name}_{stamp}").resolve()
    if output == root or root in output.parents or output in root.parents:
        parser.error("Output must be outside the single_radar input tree")
    config = {"protocol_version":1, "regime":"zero_shot", "datasets_root":str(root),"dataset_family":protocol_tag,
              "dataset_size":args.dataset_size,"profiles":list(args.profiles),"radar_types":list(args.radar_types),
              "error_levels":list(args.error_levels),"tasks":list(args.tasks),"context_lens":list(args.context_lens),
              "horizon":args.horizon,"window_mode":args.window_mode,"window_seed":args.window_seed,
              "max_test_seqs":args.max_test_seqs,"plot_sequence_id":args.plot_sequence_id,
              "model_id":args.model_id,"plots":not args.no_plots,"code_sha256":code_fingerprint()}
    config_path = output/"run_config.json"
    if output.exists() and any(output.iterdir()):
        if not args.resume or not config_path.is_file():
            parser.error("Output is not empty. Use a fresh directory, or --resume with an identical run configuration")
        if json.loads(config_path.read_text()) != config:
            parser.error("Resume configuration/code differs from saved run; use a fresh output directory")
    elif args.resume:
        parser.error("--resume requires an existing run")
    coverage, manifest = prepare_inputs(root,args.dataset_size,args.profiles,args.radar_types,args.error_levels,
                                       args.context_lens,args.horizon,args.window_mode,args.window_seed,
                                       args.max_test_seqs,args.plot_sequence_id)
    if args.resume and json.loads((output/"test_windows.json").read_text()) != manifest:
        parser.error("Dataset/metadata changed since this run; resume rejected")
    output.mkdir(parents=True,exist_ok=True)
    write_json(config_path,config)
    write_json(output/"test_windows.json",manifest)
    coverage.to_csv(output/"coverage.csv",index=False)
    print(f"[COVERAGE] {len(coverage)} datasets; {int(coverage.test_sequences.sum())} selected sequences; output {output}",flush=True)
    if args.coverage_only:
        return
    import torch
    np.random.seed(args.window_seed); torch.manual_seed(args.window_seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(args.window_seed)
    runtime = {"started_utc":datetime.now(timezone.utc).isoformat(),"device_requested":args.device,
               "batch_size":args.batch_size,"torch":torch.__version__,"cuda_available":torch.cuda.is_available(),
               "chronos_forecasting":importlib.metadata.version("chronos-forecasting")}
    write_json(output/"runtime.json",runtime)
    pipeline = load_pipeline(args.model_id,args.device)
    git_revision = subprocess.run(["git","rev-parse","HEAD"],cwd=PROJECT_ROOT,
                                  capture_output=True,text=True,check=False)
    runtime.update({"git_revision":git_revision.stdout.strip(),
                    "device_actual":str(pipeline.model.device),
                    "model_commit":getattr(pipeline.model.config,"_commit_hash",None),
                    "gpu_name":torch.cuda.get_device_name() if pipeline.model.device.type == "cuda" else None})
    write_json(output/"runtime.json",runtime)
    rows = []
    jobs = len(args.tasks)*len(args.context_lens)*len(coverage)
    for task in args.tasks:
        for length in args.context_lens:
            for condition in coverage.itertuples(index=False):
                profile,radar,level = condition.profile,condition.radar_type,condition.error_level
                scope = output/task/f"L{length}"/profile
                marker = scope/"completed"/f"{radar}_{level}.json"
                if args.resume and marker.is_file():
                    row = json.loads(marker.read_text())
                    required = [scope/"per_sequence"/f"{radar}_{level}.csv",scope/"examples"/f"{radar}_{level}.json"]
                    if not args.no_plots:required.append(scope/"plots"/f"{protocol_tag}_{radar}_{level}.png")
                    if not all(path.is_file() for path in required):
                        raise ValueError(f"{marker}: incomplete saved condition")
                    print(f"[RESUME] {task}/L{length}/{profile}/{radar}/{level}",flush=True)
                else:
                    row = evaluate_one(pipeline,root/profile/radar/f"{args.dataset_size}_{level}",profile,radar,level,
                                       task,length,args.horizon,args.batch_size,args.max_test_seqs,args.window_mode,
                                       args.window_seed,manifest,scope,not args.no_plots)
                rows.append(row)
                pd.DataFrame(rows).to_csv(output/"metrics.csv",index=False)
                if len(rows) % len(coverage) == 0:
                    export_reports(rows,output,config)
                print(f"[PROGRESS] {len(rows)}/{jobs} conditions complete",flush=True)
    print(f"[DONE] {len(rows)} conditions. Reports: {output/'report.md'}",flush=True)


if __name__ == "__main__":main()
