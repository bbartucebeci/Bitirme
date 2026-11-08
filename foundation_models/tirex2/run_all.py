"""Run all comparable TiRex-2 zero-shot single-radar experiments."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

from foundation_models.chronos2.data import CHANNELS
from foundation_models.tirex2.evaluate import RESULTS_ROOT


TASKS = (*CHANNELS, "multivariate")
PROFILES = ("fixed", "varying")
EXPECTED_CONDITIONS = 20
EXPECTED_TEST_SEQUENCES = 200


def _metrics_path(profile: str, task: str) -> Path:
    mode = (
        Path(f"multivariate_{profile}")
        if task == "multivariate"
        else Path(f"univariate_{profile}") / task.lower()
    )
    return RESULTS_ROOT / mode / "metrics.csv"


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Print stage commands without running them")
    parser.add_argument("--resume", action="store_true", help="Skip stages with complete full-size results")
    args = parser.parse_args()
    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")

    stages = [(profile, task) for profile in PROFILES for task in TASKS]
    for index, (profile, task) in enumerate(stages, start=1):
        metrics_path = _metrics_path(profile, task)
        if args.resume and _complete_metrics(metrics_path):
            print(f"[{index}/{len(stages)}] SKIP {profile}/{task}: full results exist", flush=True)
            continue
        command = [
            sys.executable,
            "-m", "foundation_models.tirex2.evaluate",
            "--profile-mode", profile,
            "--target-param", task,
            "--device", args.device,
            "--batch-size", str(args.batch_size),
            *(("--no-plots",) if args.no_plots else ()),
        ]
        print(f"[{index}/{len(stages)}] RUN {profile}/{task}", flush=True)
        if args.dry_run:
            print(subprocess.list2cmdline(command), flush=True)
            continue
        subprocess.run(command, cwd=RESULTS_ROOT.parents[2], check=True)
        if not _complete_metrics(metrics_path):
            raise RuntimeError(f"{profile}/{task} exited without complete full-size metrics")

    print(
        "Dry run complete; no experiments were executed."
        if args.dry_run else "TiRex-2 zero-shot benchmark stages complete.",
        flush=True,
    )


if __name__ == "__main__":
    main()
