"""PULSAR: Automated End-to-End Varying Profile Training & Benchmarking Pipeline.

Sequentially executes:
1. Univariate LoRA SFT for PRI (3 epochs) + full 4,000 sequence test eval
2. Univariate LoRA SFT for Frequency (3 epochs) + full 4,000 sequence test eval
3. Univariate LoRA SFT for PW (3 epochs) + full 4,000 sequence test eval
4. Univariate LoRA SFT for AOA (3 epochs) + full 4,000 sequence test eval
5. Univariate LoRA SFT for Amplitude (3 epochs) + full 4,000 sequence test eval
6. Joint 5-Channel Multivariate LoRA SFT (3 epochs) + full 4,000 sequence test eval
7. Master Summary Report Generation (univariate_varying_summary.md & univariate_vs_multivariate_varying_summary.md)
"""

from __future__ import annotations
import subprocess
import sys
import time
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent


def run_step(step_name: str, cmd: list[str]):
    print("\n" + "=" * 80)
    print(f"PIPELINE STEP: {step_name}")
    print(f"COMMAND: {' '.join(cmd)}")
    print("=" * 80)
    t0 = time.time()
    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    elapsed = time.time() - t0
    if res.returncode != 0:
        print(f"[ERROR] Step '{step_name}' failed with exit code {res.returncode} after {elapsed:.1f}s!")
        sys.exit(res.returncode)
    print(f"[SUCCESS] Step '{step_name}' completed in {elapsed:.1f}s ({elapsed/60:.1f} min)")


def main():
    t_start = time.time()
    py_exec = sys.executable

    # 1-5. Univariate LoRA SFT runs
    univariate_params = ["PRI", "Frequency", "PW", "AOA", "Amplitude"]
    for param in univariate_params:
        cmd = [
            py_exec,
            "-m",
            "foundation_models.timesfm.train",
            "--profile-mode",
            "varying",
            "--target-param",
            param,
            "--epochs",
            "3",
            "--batch-size",
            "64",
            "--lr",
            "1e-4",
        ]
        run_step(f"Univariate LoRA SFT [{param} Varying]", cmd)

    # 6. Joint Multivariate LoRA SFT
    cmd_mv = [
        py_exec,
        "-m",
        "foundation_models.timesfm.train_multivariate",
        "--profile-mode",
        "varying",
        "--epochs",
        "3",
        "--batch-size",
        "64",
        "--lr",
        "1e-4",
    ]
    run_step("Joint 5-Channel Multivariate LoRA SFT [Varying]", cmd_mv)

    # 7. Master Summaries Compilation
    cmd_sum = [
        py_exec,
        "-m",
        "foundation_models.common.summary",
        "--profile-mode",
        "varying",
    ]
    run_step("Compile Master Summaries [Varying]", cmd_sum)

    total_time = time.time() - t_start
    print("\n" + "=" * 80)
    print(f"PULSAR: Full Varying Profile Pipeline Complete in {total_time:.1f}s ({total_time/60:.1f} min)!")
    print("=" * 80)


if __name__ == "__main__":
    main()

