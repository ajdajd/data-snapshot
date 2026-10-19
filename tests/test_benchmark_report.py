"""Verify metric formatting, missing-run blanks, and report safety checks."""

import importlib.util
import json
from pathlib import Path

import pytest

from data_snapshot.constants import ROOT


def test_benchmark_markdown(tmp_path: Path) -> None:
    """Render source and pooled values while protecting existing reports."""
    spec = importlib.util.spec_from_file_location(
        "benchmark_report", ROOT / "scripts/summarize_benchmark.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = {
        "documents_mismatch": {"only_gt": [], "only_pred": []},
        "metrics": {
            "0.5": {
                "per_class": {
                    label: {
                        "precision": 0.12345,
                        "recall": 0.87654,
                        "mean_iou": 0.75,
                        "mean_area_precision": 0.9,
                        "mean_area_recall": None,
                    }
                    for label in ("Figure", "Table")
                }
            }
        },
    }
    for relative in ("corpus.json", "sources/unhcr.json"):
        path = tmp_path / "doclayoutyolo/reports" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report))
    module.main(["--output-root", str(tmp_path)])
    output = tmp_path / "report.md"
    text = output.read_text()
    assert text.count("## Figure") == text.count("## Table") == 2
    assert "| Detection | Precision |  | **0.123** |  |  |" in text
    assert "| UNHCR / ReliefWeb | Detection | Recall |  | **0.877** |  |  |" in text
    assert "| PRWP | Detection | Recall |  |  |  |  |" in text
    assert "| Spatial Accuracy | Area Recall |  | N/A |  |  |" in text
    with pytest.raises(FileExistsError):
        module.main(["--output-root", str(tmp_path)])
    module.main(["--output-root", str(tmp_path), "--overwrite"])
    report["documents_mismatch"]["only_gt"] = ["missing.pdf"]
    (tmp_path / "doclayoutyolo/reports/corpus.json").write_text(json.dumps(report))
    with pytest.raises(ValueError, match="Document mismatch"):
        module.main(["--output-root", str(tmp_path), "--overwrite"])
    assert output.read_text() == text


def test_docling_comparison_keeps_native_renderer_note(tmp_path: Path) -> None:
    """Read Docling from a separate root without changing the baseline report.

    Parameters
    ----------
    tmp_path : Path
        Separate baseline and native Docling report roots.
    """
    spec = importlib.util.spec_from_file_location(
        "benchmark_report", ROOT / "scripts/summarize_benchmark.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    metrics = {key: 0.5 for key in module.METRICS.values()}
    report = {
        "documents_mismatch": {"only_gt": [], "only_pred": []},
        "metrics": {"0.5": {"per_class": {"Figure": metrics, "Table": metrics}}},
    }
    path = tmp_path / "native/docling_heron/reports/corpus.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(report))
    egret_path = tmp_path / "egret/docling_egret_medium/reports/corpus.json"
    egret_path.parent.mkdir(parents=True)
    egret_path.write_text(json.dumps(report))
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    module.main(
        [
            "--output-root",
            str(baseline),
            "--docling-root",
            str(tmp_path / "native"),
            "--egret-root",
            str(tmp_path / "egret"),
            "--output",
            str(tmp_path / "comparison.md"),
        ]
    )
    text = (tmp_path / "comparison.md").read_text()
    assert "Docling Heron" in text
    assert "Docling Egret Medium" in text
    assert "| Detection | Precision |  |  |  |  | **0.500** | **0.500** |" in text
    assert "complete pipelines" in text
    assert "crops are not expanded" in text
    assert not (baseline / "report.md").exists()
