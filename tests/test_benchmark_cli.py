import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from data_snapshot.constants import ROOT

_SCRIPT_PATH = ROOT / "scripts/evaluate_benchmark.py"


def _load_cli_module() -> ModuleType:
    """Load the benchmark script as a module for focused CLI testing."""
    spec = importlib.util.spec_from_file_location(
        "evaluate_benchmark_cli", _SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load benchmark CLI: {_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_and_corpus_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_cli_module()
    config_path = tmp_path / "benchmark.json"
    config_path.write_text(
        json.dumps(
            {
                "model": "yolo26",
                "dataset_root": str(tmp_path / "dataset"),
                "output_root": "data/evaluation_runs",
                "sources": ["unhcr", "prwp"],
                "device": "cuda:0",
                "adapter_config": {"pdf_backend": "pdf2image"},
            }
        ),
        encoding="utf-8",
    )
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_evaluate_source(**kwargs: Any) -> dict[str, Any]:
        """Record a source invocation."""
        calls.append(("source", kwargs))
        return {}

    def fake_evaluate_corpus(**kwargs: Any) -> dict[str, Any]:
        """Record a corpus invocation."""
        calls.append(("corpus", kwargs))
        return {}

    monkeypatch.setattr(module, "evaluate_source", fake_evaluate_source)
    monkeypatch.setattr(module, "evaluate_corpus", fake_evaluate_corpus)

    module.main(
        [
            "--config",
            str(config_path),
            "--source",
            "unhcr",
            "--reuse-predictions",
            "--overwrite",
        ]
    )
    module.main(["--config", str(config_path), "--corpus"])

    assert calls == [
        (
            "source",
            {
                "model": "yolo26",
                "source": "unhcr",
                "dataset_root": tmp_path / "dataset",
                "output_root": ROOT / "data/evaluation_runs",
                "device": "cuda:0",
                "adapter_config": {"pdf_backend": "pdf2image"},
                "run_inference": False,
                "overwrite": True,
            },
        ),
        (
            "corpus",
            {
                "model": "yolo26",
                "sources": ["unhcr", "prwp"],
                "output_root": ROOT / "data/evaluation_runs",
                "overwrite": False,
            },
        ),
    ]


def test_cli_rejects_unconfigured_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_cli_module()
    config_path = tmp_path / "benchmark.json"
    config_path.write_text(
        json.dumps(
            {
                "model": "yolo26",
                "dataset_root": str(tmp_path / "dataset"),
                "output_root": "data/evaluation_runs",
                "sources": ["unhcr"],
                "device": "cpu",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "evaluate_source", lambda **kwargs: {})

    with pytest.raises(SystemExit, match="2"):
        module.main(["--config", str(config_path), "--source", "prwp"])
