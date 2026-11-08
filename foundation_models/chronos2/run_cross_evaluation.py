"""Evaluate fixed-trained and varying-trained Chronos-2 checkpoints across profiles."""

from __future__ import annotations

import argparse

from foundation_models.chronos2.adapter import checkpoint_path, load_pipeline
from foundation_models.chronos2.evaluate import RESULTS_ROOT, audit_coverage, run_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description="Chronos-2 cross-profile transfer benchmark")
    parser.add_argument("--target-param", choices=("PRI", "multivariate"), default="PRI")
    parser.add_argument("--dataset-size", default="1000x128")
    parser.add_argument("--context-len", type=int, default=96)
    parser.add_argument("--horizon", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--max-test-seqs", type=int)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    for source, target in (("fixed", "varying"), ("varying", "fixed")):
        coverage = audit_coverage(
            target, args.target_param, args.dataset_size, args.context_len,
            args.horizon, args.max_test_seqs,
        )
        print(coverage.to_string(index=False))
        if (coverage.eligible_windows == 0).any():
            raise ValueError(f"{target} test profile contains a condition without a complete forecast window")
        checkpoint = checkpoint_path(source, args.target_param)
        if not checkpoint.is_dir():
            raise FileNotFoundError(f"Missing trained checkpoint: {checkpoint}")
        pipeline = load_pipeline(str(checkpoint), args.device)
        run_evaluation(
            pipeline, target, args.target_param, args.dataset_size,
            args.context_len, args.horizon, args.batch_size, args.max_test_seqs,
            RESULTS_ROOT / "cross_evaluation" / f"{source}_on_{target}" / args.target_param.lower(),
            plots=not args.no_plots,
        )


if __name__ == "__main__":
    main()
