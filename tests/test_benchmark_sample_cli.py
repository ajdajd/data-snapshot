"""Test manifest staging and source-to-corpus sample orchestration."""

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


def test_half_runner_uses_fixed_half_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the half runner separate from the nine-document smoke selection."""
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    import evaluate_benchmark_half as half

    captured: dict[str, Any] = {}

    def capture(argv: list[str], *, default_manifest: Path) -> None:
        """Capture delegation without staging inputs or running inference."""
        captured.update(argv=argv, manifest=default_manifest)

    monkeypatch.setattr(half, "run_sample", capture)
    half.main(["--config", "model.json"])
    assert captured["argv"] == ["--config", "model.json"]
    manifest = json.loads(captured["manifest"].read_text())
    counts: dict[str, int] = {}
    for entry in manifest["documents"]:
        counts[entry["source"]] = counts.get(entry["source"], 0) + 1
    assert counts == {"unhcr": 169, "prwp": 50, "refugee": 19}
    assert len({entry["pdf"] for entry in manifest["documents"]}) == 238
    module = _load_cli_module()
    assert (
        module._build_parser(captured["manifest"])
        .parse_args(["--config", "model.json"])
        .manifest
        == captured["manifest"]
    )


@pytest.mark.parametrize("overwrite", [False, True])
def test_sample_cli_stages_inputs_and_runs_benchmark(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, overwrite: bool
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
    second_pdf = dataset_root / "documents/prwp/other.pdf"
    second_annotation = dataset_root / "annotations/prwp/other.json"
    second_pdf.parent.mkdir(parents=True)
    second_annotation.parent.mkdir(parents=True)
    second_pdf.write_bytes(b"%PDF-placeholder")
    second_annotation.write_text("{}", encoding="utf-8")

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
                    },
                    {
                        "source": "prwp",
                        "pdf": "other.pdf",
                        "annotation": "other.json",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    invocations: list[list[str]] = []

    def fake_run(command: list[str], *, check: bool) -> None:
        """Capture the staged configuration before its temporary directory closes."""
        invocations.append(command)
        assert check is True
        sample_config = json.loads(Path(command[3]).read_text(encoding="utf-8"))
        sample_root = Path(sample_config["dataset_root"])
        assert sample_config["sources"] == ["unhcr", "prwp"]
        assert sample_config["output_root"] == str(
            ROOT / "data/evaluation_runs/manifest"
        )
        for original in (pdf_path, annotation_path, second_pdf, second_annotation):
            staged = sample_root / original.relative_to(dataset_root)
            assert staged.is_symlink()
            assert staged.resolve() == original
        assert not (sample_root / "documents/refugee").exists()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module.main(
        [
            "--config",
            str(config_path),
            "--manifest",
            str(manifest_path),
            *(["--overwrite"] if overwrite else []),
        ]
    )

    base_command = [
        module.sys.executable,
        str(module.BENCHMARK_SCRIPT),
        "--config",
        invocations[0][3],
        *(["--overwrite"] if overwrite else []),
    ]
    assert invocations == [
        [*base_command, "--source", "unhcr"],
        [*base_command, "--source", "prwp"],
        [*base_command, "--corpus"],
    ]


@pytest.mark.parametrize("source", [".", "..", "../unhcr"])
def test_sample_rejects_invalid_source(tmp_path: Path, source: str) -> None:
    """Reject source paths that could escape the staged directory layout."""
    module = _load_cli_module()
    manifest: dict[str, Any] = {
        "documents": [
            {"source": source, "pdf": "example.pdf", "annotation": "example.json"}
        ]
    }
    with pytest.raises(ValueError, match="must be filenames"):
        module._stage_sample(tmp_path / "dataset", manifest, tmp_path / "sample")
