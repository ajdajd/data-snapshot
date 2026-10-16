"""Evaluate an integrated model on the fixed paper benchmark sample."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from data_snapshot.constants import ROOT

DEFAULT_MANIFEST = (
    ROOT / "src/data_snapshot/evaluation/configs/paper_benchmark_sample.json"
)
BENCHMARK_SCRIPT = ROOT / "scripts/evaluate_benchmark.py"


def _load_json_object(path: Path, *, kind: str) -> dict[str, Any]:
    """Load a JSON object from disk.

    Parameters
    ----------
    path : Path
        JSON file to read.
    kind : str
        Human-readable file type used in validation errors.

    Returns
    -------
    dict[str, Any]
        Parsed JSON object.

    Raises
    ------
    ValueError
        If the file does not contain a JSON object.
    """
    with path.open("r", encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, dict):
        raise ValueError(f"{kind} must be a JSON object: {path}")
    return value


def _stage_sample(
    dataset_root: Path, manifest: dict[str, Any], sample_root: Path
) -> int:
    """Link manifest documents into one temporary sample source.

    Parameters
    ----------
    dataset_root : Path
        Dataset root containing source-specific documents and annotations.
    manifest : dict[str, Any]
        Sample manifest with source, PDF, and annotation filenames.
    sample_root : Path
        Temporary dataset root to populate.

    Returns
    -------
    int
        Number of staged documents.

    Raises
    ------
    FileNotFoundError
        If a selected PDF or annotation does not exist.
    ValueError
        If the manifest structure or selected filenames are invalid.
    """
    documents = manifest.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError("Sample manifest 'documents' must be a non-empty list.")

    pdf_dir = sample_root / "documents/sample"
    annotation_dir = sample_root / "annotations/sample"
    pdf_dir.mkdir(parents=True)
    annotation_dir.mkdir(parents=True)

    seen_pdfs: set[str] = set()
    seen_annotations: set[str] = set()
    for entry in documents:
        if not isinstance(entry, dict):
            raise ValueError("Each sample document must be a JSON object.")
        values = {field: entry.get(field) for field in ("source", "pdf", "annotation")}
        if not all(
            isinstance(value, str) and value and Path(value).name == value
            for value in values.values()
        ):
            raise ValueError(
                "Sample source, PDF, and annotation values must be filenames."
            )

        source = values["source"]
        pdf_name = values["pdf"]
        annotation_name = values["annotation"]
        if pdf_name in seen_pdfs or annotation_name in seen_annotations:
            raise ValueError("Sample PDF and annotation filenames must be unique.")
        seen_pdfs.add(pdf_name)
        seen_annotations.add(annotation_name)

        pdf_path = dataset_root / "documents" / source / pdf_name
        annotation_path = dataset_root / "annotations" / source / annotation_name
        for selected_path in (pdf_path, annotation_path):
            if not selected_path.is_file():
                raise FileNotFoundError(f"Sample input not found: {selected_path}")

        (pdf_dir / pdf_name).symlink_to(pdf_path.resolve())
        (annotation_dir / annotation_name).symlink_to(annotation_path.resolve())

    return len(documents)


def _build_parser() -> argparse.ArgumentParser:
    """Build the sample benchmark command-line parser.

    Returns
    -------
    argparse.ArgumentParser
        Configured parser.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a model benchmark JSON configuration.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Path to the sample manifest.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing sample ground truth, predictions, and report.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Stage and evaluate the fixed benchmark sample.

    Parameters
    ----------
    argv : Sequence[str] | None
        Optional arguments for testing. Uses process arguments when ``None``.
    """
    args = _build_parser().parse_args(argv)
    try:
        config = _load_json_object(args.config, kind="Benchmark configuration")
        manifest = _load_json_object(args.manifest, kind="Sample manifest")
        dataset_root_value = config.get("dataset_root")
        if not isinstance(dataset_root_value, str) or not dataset_root_value:
            raise ValueError("Configuration 'dataset_root' must be a string.")
        dataset_root = Path(dataset_root_value)
        if not dataset_root.is_absolute():
            dataset_root = ROOT / dataset_root

        with tempfile.TemporaryDirectory(prefix="data-snapshot-sample-") as directory:
            sample_root = Path(directory)
            document_count = _stage_sample(dataset_root, manifest, sample_root)
            sample_config = {
                **config,
                "dataset_root": str(sample_root),
                "sources": ["sample"],
            }
            sample_config_path = sample_root / "benchmark.json"
            sample_config_path.write_text(
                json.dumps(sample_config, indent=2), encoding="utf-8"
            )
            print(f"Running sample benchmark on {document_count} document(s).")
            command = [
                sys.executable,
                str(BENCHMARK_SCRIPT),
                "--config",
                str(sample_config_path),
                "--source",
                "sample",
            ]
            if args.overwrite:
                command.append("--overwrite")
            subprocess.run(command, check=True)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
