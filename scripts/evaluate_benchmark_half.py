"""Evaluate the fixed half-size benchmark by source and as a combined corpus."""

from __future__ import annotations

from collections.abc import Sequence

from evaluate_benchmark_sample import main as run_sample

from data_snapshot.constants import ROOT


def main(argv: Sequence[str] | None = None) -> None:
    """Run the sample evaluator with the fixed half-size manifest.

    Parameters
    ----------
    argv : Sequence[str] | None
        Optional arguments for testing. Uses process arguments when ``None``.
    """
    run_sample(
        argv,
        default_manifest=ROOT
        / "src/data_snapshot/evaluation/configs/paper_benchmark_half.json",
    )


if __name__ == "__main__":
    main()
