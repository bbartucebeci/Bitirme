"""Run the complete single-radar Chronos-2 benchmark in one command.

Stages are ordered so zero-shot reports precede LoRA training, and cross-profile
evaluation uses the checkpoints produced by the training stages.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from foundation_models.chronos2.data import CHANNELS, PROJECT_ROOT
from foundation_models.chronos2.evaluate import RESULTS_ROOT


TASKS = (*CHANNELS, "multivariate")
PROFILES = ("fixed", "varying")
EXPECTED_CONDITIONS = 20  # Five radar types times four error levels.
EXPECTED_TEST_SEQUENCES = 200


@dataclass(frozen=True)
class Stage:
    name: str
    module: str
    arguments: tuple[str, ...]
    metrics: tuple[Path, ...]
    checkpoint: Path | None = None


def _mode(profile: str, task: str) -> Path:
    return Path(f"multivariate_{profile}") if task == "multivariate" else Path(f"univariate_{profile}") / task.lower()


def _build_stages(device: str, no_plots: bool) -> list[Stage]:
    shared = ("--device", device, *(('--no-plots',) if no_plots else ()))
    stages: list[Stage] = []

    for profile in PROFILES:
        for task in TASKS:
            stages.append(Stage(
                f"zero-shot {profile}/{task}",
                "foundation_models.chronos2.evaluate",
                ("--profile-mode", profile, "--target-param", task, *shared),
                (RESULTS_ROOT / "zero_shot" / _mode(profile, task) / "metrics.csv",),
            ))

    for profile in PROFILES:
        for task in TASKS:
            stages.append(Stage(
                f"LoRA {profile}/{task}",
                "foundation_models.chronos2.train",
                ("--profile-mode", profile, "--target-param", task, *shared),
                (RESULTS_ROOT / "lora_sft" / _mode(profile, task) / "metrics.csv",),
                PROJECT_ROOT / "models" / "chronos2_lora" / profile / task.lower() / "best_model",
            ))

    for task in ("PRI", "multivariate"):
        stages.append(Stage(
            f"cross-profile {task}",
            "foundation_models.chronos2.run_cross_evaluation",
            ("--target-param", task, *shared),
            tuple(
                RESULTS_ROOT / "cross_evaluation" / f"{source}_on_{target}" / task.lower() / "metrics.csv"
                for source, target in (("fixed", "varying"), ("varying", "fixed"))
            ),
        ))
    return stages


def _complete_metrics(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        conditions = {(row["radar_type"], row["error_level"]) for row in rows}
        return (
            len(rows) == EXPECTED_CONDITIONS
            and len(conditions) == EXPECTED_CONDITIONS
            and all(
                sum(int(row[key]) for key in ("num_sequences", "skipped_short", "skipped_no_emitter"))
                == EXPECTED_TEST_SEQUENCES
                for row in rows
            )
        )
    except (OSError, KeyError, ValueError):
        return False


def _stage_complete(stage: Stage) -> bool:
    return all(_complete_metrics(path) for path in stage.metrics) and (
        stage.checkpoint is None or (
            (stage.checkpoint / "adapter_config.json").is_file()
            and (stage.checkpoint / "adapter_model.safetensors").is_file()
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print the stage commands without running them")
    parser.add_argument("--resume", action="store_true", help="Skip stages with complete full-size results")
    args = parser.parse_args()

    stages = _build_stages(args.device, args.no_plots)
    for index, stage in enumerate(stages, start=1):
        command = [sys.executable, "-m", stage.module, *stage.arguments]
        if args.resume and _stage_complete(stage):
            print(f"[{index}/{len(stages)}] SKIP {stage.name}: full results exist", flush=True)
            continue
        print(f"[{index}/{len(stages)}] RUN {stage.name}", flush=True)
        if args.dry_run:
            print(subprocess.list2cmdline(command), flush=True)
            continue
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
        if not _stage_complete(stage):
            raise RuntimeError(f"{stage.name} exited without complete metrics or checkpoint")

    if args.dry_run:
        print("Dry run complete; no experiments were executed.", flush=True)
    else:
        print("Chronos-2 single-radar benchmark stages complete.", flush=True)


if __name__ == "__main__":
    main()
