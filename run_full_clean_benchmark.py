"""PULSAR: Master End-to-End Benchmark Orchestrator.

Orchestrates clean retraining, evaluation, and visualization across all 5 foundation models
and 6 classical baselines on the single-radar benchmark (Varying & Fixed profiles).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable


def run_cmd(cmd: list[str], desc: str, dry_run: bool = False) -> bool:
    print(f"\n{'='*75}")
    print(f"[*] {desc}")
    print(f"[*] Command: {' '.join(cmd)}")
    print(f"{'='*75}")
    if dry_run:
        print("[DRY-RUN] Skipped.")
        return True

    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
        elapsed = time.time() - t0
        print(f"[SUCCESS] {desc} (Completed in {elapsed:.1f}s)")
        return True
    except subprocess.CalledProcessError as exc:
        elapsed = time.time() - t0
        print(f"[ERROR] {desc} failed with exit code {exc.returncode} after {elapsed:.1f}s")
        return False
    except Exception as exc:
        print(f"[FATAL] {desc} encountered unexpected exception: {exc}")
        return False


def main():
    parser = argparse.ArgumentParser(description="PULSAR Master Benchmark Runner")
    parser.add_argument("--profile-mode", choices=("varying", "fixed", "both"), default="varying",
                        help="Benchmark profile (default: varying)")
    parser.add_argument("--stage", choices=("all", "classic", "zero_shot", "lora", "plots", "neural", "sequential_neural", "remaining"), default="all",
                        help="Benchmark stage to execute ('neural' = zero_shot + lora + plots; 'remaining' = finishes interrupted lora + plots)")
    parser.add_argument("--device", default="auto", choices=("auto", "cuda", "cpu"))
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs for LoRA fine-tuning (default: 3)")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing")
    args = parser.parse_args()

    profiles = ("varying", "fixed") if args.profile_mode == "both" else (args.profile_mode,)
    device = args.device

    print(f"\n{'#'*75}")
    print(f"# PULSAR MASTER BENCHMARK RUNNER")
    print(f"# Profiles: {', '.join(profiles)} | Stage: {args.stage} | Device: {device}")
    print(f"{'#'*75}")

    # =========================================================================
    # STAGE 1: Classical Signal Processing Baselines
    # =========================================================================
    if args.stage in ("all", "classic"):
        for prof in profiles:
            run_cmd(
                [PYTHON, "-m", "classic_methods.compare_methods", "--profile-mode", prof],
                f"Classic Baselines Comparison ({prof})",
                args.dry_run,
            )

    # =========================================================================
    # STAGE 2: Pre-Trained Foundation Models (Zero-Shot)
    # =========================================================================
    if args.stage in ("all", "zero_shot", "neural", "sequential_neural"):
        for prof in profiles:
            # Chronos-2 Zero-Shot (Univariate PRI & Multivariate)
            run_cmd(
                [PYTHON, "-m", "foundation_models.chronos2.evaluate", "--profile-mode", prof, "--target-param", "PRI", "--device", device],
                f"Chronos-2 Zero-Shot Univariate PRI ({prof})",
                args.dry_run,
            )
            run_cmd(
                [PYTHON, "-m", "foundation_models.chronos2.evaluate", "--profile-mode", prof, "--target-param", "multivariate", "--device", device],
                f"Chronos-2 Zero-Shot Multivariate ({prof})",
                args.dry_run,
            )

            # TimesFM 3.0 Zero-Shot (Univariate PRI & Multivariate)
            run_cmd(
                [PYTHON, "-m", "foundation_models.timesfm.evaluate", "--profile-mode", prof, "--modality", "univariate", "--target-param", "PRI"],
                f"TimesFM 3.0 Zero-Shot Univariate PRI ({prof})",
                args.dry_run,
            )
            run_cmd(
                [PYTHON, "-m", "foundation_models.timesfm.evaluate_multivariate", "--profile-mode", prof],
                f"TimesFM 3.0 Zero-Shot Multivariate ({prof})",
                args.dry_run,
            )

            # TiRex-2 Zero-Shot (Pure PyTorch CPU backend on Windows)
            run_cmd(
                [PYTHON, "-m", "foundation_models.tirex2.evaluate", "--profile-mode", prof, "--target-param", "PRI", "--device", "cpu"],
                f"TiRex-2 Zero-Shot Univariate PRI ({prof})",
                args.dry_run,
            )

            # Toto 2.0 Zero-Shot
            run_cmd(
                [PYTHON, "-m", "foundation_models.toto2.evaluate", "--profile-mode", prof, "--target-param", "PRI"],
                f"Toto 2.0 Zero-Shot Univariate PRI ({prof})",
                args.dry_run,
            )

            # t0-gamma Zero-Shot
            run_cmd(
                [PYTHON, "-m", "foundation_models.t0_gamma.evaluate", "--profile-mode", prof, "--target-param", "PRI"],
                f"t0-gamma Zero-Shot Univariate PRI ({prof})",
                args.dry_run,
            )

    # =========================================================================
    # STAGE 3: Supervised LoRA Fine-Tuning & Evaluation
    # =========================================================================
    if args.stage in ("all", "lora", "neural", "sequential_neural", "remaining"):
        for prof in profiles:
            if args.stage != "remaining":
                # Chronos-2 LoRA SFT Univariate PRI
                run_cmd(
                    [PYTHON, "-m", "foundation_models.chronos2.train", "--profile-mode", prof, "--target-param", "PRI", "--epochs", str(args.epochs), "--device", device],
                    f"Chronos-2 LoRA SFT Univariate PRI ({prof})",
                    args.dry_run,
                )

            # Chronos-2 LoRA SFT Multivariate
            run_cmd(
                [PYTHON, "-m", "foundation_models.chronos2.train", "--profile-mode", prof, "--target-param", "multivariate", "--epochs", str(args.epochs), "--device", device],
                f"Chronos-2 LoRA SFT Multivariate ({prof})",
                args.dry_run,
            )

            # TimesFM 3.0 LoRA SFT (Univariate PRI & Multivariate)
            run_cmd(
                [PYTHON, "-m", "foundation_models.timesfm.train", "--profile-mode", prof, "--target-param", "PRI", "--epochs", str(args.epochs)],
                f"TimesFM 3.0 LoRA SFT Univariate PRI ({prof})",
                args.dry_run,
            )
            run_cmd(
                [PYTHON, "-m", "foundation_models.timesfm.train_multivariate", "--profile-mode", prof, "--epochs", str(args.epochs)],
                f"TimesFM 3.0 LoRA SFT Multivariate ({prof})",
                args.dry_run,
            )

    # =========================================================================
    # STAGE 4: Master Visualization Suite & Report Regeneration
    # =========================================================================
    if args.stage in ("all", "plots", "neural", "sequential_neural", "remaining"):
        run_cmd(
            [PYTHON, "results/comparison/generate_master_plots.py"],
            "Regenerate Master Visualizations & Benchmark Plots",
            args.dry_run,
        )

    print(f"\n{'#'*75}")
    print(f"# PULSAR BENCHMARK PIPELINE COMPLETE")
    print(f"{'#'*75}")


if __name__ == "__main__":
    main()
