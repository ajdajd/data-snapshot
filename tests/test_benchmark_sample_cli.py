import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from data_snapshot.constants import ROOT

_SCRIPT_PATH = ROOT / "scripts/evaluate_benchmark_sample.py"
_MANIFEST_PATH = (
    ROOT / "src/data_snapshot/evaluation/configs/paper_benchmark_sample.json"
)


def _load_cli_module() -> ModuleType:
    """Load the sample benchmark script for focused testing."""
    spec = importlib.util.spec_from_file_location(
        "evaluate_benchmark_sample_cli", _SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load sample benchmark CLI: {_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checked_in_sample_has_three_documents_per_source() -> None:
    """Require three unique sample documents from each paper corpus."""
    manifest = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    sources = [document["source"] for document in manifest["documents"]]
    pdfs = [document["pdf"] for document in manifest["documents"]]

    assert {source: sources.count(source) for source in set(sources)} == {
        "unhcr": 3,
        "prwp": 3,
        "refugee": 3,
    }
    assert len(pdfs) == len(set(pdfs)) == 9


def test_sample_cli_stages_inputs_and_runs_benchmark(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stage selected files and invoke the existing benchmark CLI."""
    module = _load_cli_module()
    dataset_root = tmp_path / "dataset"
    pdf_path = dataset_root / "documents/unhcr/example.pdf"
    annotation_path = dataset_root / "annotations/unhcr/example.json"
    pdf_path.parent.mkdir(parents=True)
    annotation_path.parent.mkdir(parents=True)
    pdf_path.write_bytes(b"%PDF-placeholder")
    annotation_path.write_text("{}", encoding="utf-8")

    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "model": "doclayoutyolo",
                "dataset_root": str(dataset_root),
                "output_root": "data/evaluation_runs",
                "sources": ["unhcr", "prwp", "refugee"],
                "device": "cuda:0",
                "adapter_config": {"pdf_backend": "pdf2image"},
            }
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "source": "unhcr",
                        "pdf": "example.pdf",
                        "annotation": "example.json",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    invocation: dict[str, Any] = {}

    def fake_run(command: list[str], *, check: bool) -> None:
        """Capture the staged configuration before its temporary directory closes."""
        invocation["command"] = command
        invocation["check"] = check
        sample_config = json.loads(Path(command[3]).read_text(encoding="utf-8"))
        sample_root = Path(sample_config["dataset_root"])
        invocation["sources"] = sample_config["sources"]
        invocation["pdf_target"] = (
            sample_root / "documents/sample/example.pdf"
        ).resolve()
        invocation["annotation_target"] = (
            sample_root / "annotations/sample/example.json"
        ).resolve()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module.main(
        [
            "--config",
            str(config_path),
            "--manifest",
            str(manifest_path),
            "--overwrite",
        ]
    )

    assert invocation == {
        "command": [
            module.sys.executable,
            str(module.BENCHMARK_SCRIPT),
            "--config",
            invocation["command"][3],
            "--source",
            "sample",
            "--overwrite",
        ],
        "check": True,
        "sources": ["sample"],
        "pdf_target": pdf_path,
        "annotation_target": annotation_path,
    }
