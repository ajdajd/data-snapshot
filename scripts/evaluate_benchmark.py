"""Evaluate every configured source and the combined corpus, or one chosen step."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from data_snapshot.constants import ROOT
from data_snapshot.evaluation.benchmark import evaluate_corpus, evaluate_source

_CONFIG_FIELDS = {
    "model",
    "dataset_root",
    "output_root",
    "sources",
    "device",
    "adapter_config",
}
_REQUIRED_CONFIG_FIELDS = _CONFIG_FIELDS - {"adapter_config"}


def _build_parser() -> argparse.ArgumentParser:
    """Build the benchmark command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to the benchmark JSON configuration.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--source", help="Run one configured dataset source.")
    mode.add_argument(
        "--corpus",
        action="store_true",
        help="Combine and evaluate all configured sources.",
    )
    parser.add_argument(
        "--reuse-predictions",
        action="store_true",
        help="Skip source inference and reuse its existing prediction file.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace generated ground truth and report outputs.",
    )
    return parser


def _resolve_repo_path(value: str) -> Path:
    """Resolve a configuration path relative to the repository root."""
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _load_config(path: Path) -> dict[str, Any]:
    """Load and validate a benchmark JSON configuration.

    Parameters
    ----------
    path : Path
        Configuration file to load.

    Returns
    -------
    dict[str, Any]
        Validated configuration values with resolved paths.

    Raises
    ------
    FileNotFoundError
        If the configuration file does not exist.
    ValueError
        If the JSON object is missing fields or contains invalid values.
    """
    with path.open("r", encoding="utf-8") as file:
        config = json.load(file)
    if not isinstance(config, dict):
        raise ValueError("Benchmark configuration must be a JSON object.")

    unknown = sorted(set(config) - _CONFIG_FIELDS)
    missing = sorted(_REQUIRED_CONFIG_FIELDS - set(config))
    if unknown:
        raise ValueError(f"Unknown benchmark configuration fields: {unknown}")
    if missing:
        raise ValueError(f"Missing benchmark configuration fields: {missing}")

    for field in ("model", "dataset_root", "output_root", "device"):
        if not isinstance(config[field], str) or not config[field]:
            raise ValueError(f"Configuration field {field!r} must be a string.")

    sources = config["sources"]
    if (
        not isinstance(sources, list)
        or not sources
        or not all(isinstance(source, str) and source for source in sources)
    ):
        raise ValueError("Configuration field 'sources' must be a list of names.")
    if len(sources) != len(set(sources)):
        raise ValueError("Configuration source names must be unique.")

    adapter_config = config.get("adapter_config", {})
    if not isinstance(adapter_config, dict):
        raise ValueError("Configuration field 'adapter_config' must be an object.")

    return {
        **config,
        "dataset_root": _resolve_repo_path(config["dataset_root"]),
        "output_root": _resolve_repo_path(config["output_root"]),
        "adapter_config": adapter_config,
    }


def main(argv: Sequence[str] | None = None) -> None:
    """Load configuration and run the selected benchmark operation.

    Parameters
    ----------
    argv : Sequence[str] | None
        Optional arguments for testing. Uses process arguments when ``None``.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        config = _load_config(args.config)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    if args.corpus:
        if args.reuse_predictions:
            parser.error("--reuse-predictions applies only to --source runs.")
        evaluate_corpus(
            model=config["model"],
            sources=config["sources"],
            output_root=config["output_root"],
            overwrite=args.overwrite,
        )
        return

    if args.source is not None and args.source not in config["sources"]:
        parser.error(
            f"Source {args.source!r} is not listed in the configuration sources."
        )
    sources = [args.source] if args.source is not None else config["sources"]
    for source in sources:
        evaluate_source(
            model=config["model"],
            source=source,
            dataset_root=config["dataset_root"],
            output_root=config["output_root"],
            device=config["device"],
            adapter_config=config["adapter_config"],
            run_inference=not args.reuse_predictions,
            overwrite=args.overwrite,
        )
    if args.source is None:
        evaluate_corpus(
            model=config["model"],
            sources=sources,
            output_root=config["output_root"],
            overwrite=args.overwrite,
        )


if __name__ == "__main__":
    main()
