import json
from pathlib import Path
from typing import Any

import pytest

import data_snapshot.evaluation.benchmark as benchmark
import data_snapshot.evaluation.evaluate_model as evaluate_model_module
from data_snapshot.utils import load_json


def _evaluation_file(doc_id: str, *, model: str) -> dict[str, Any]:
    """Build a minimal evaluation file for one document and page."""
    return {
        "label_map": {"1": "Figure", "2": "Table"},
        "info": {
            "schema_version": "1.3",
            "type": "ground_truth" if model == "human annotation" else "prediction",
            "model": {"name": model},
            "coordinate_system": {
                "type": "normalized_xyxy",
                "range": [0.0, 1.0],
                "origin": "top_left",
            },
        },
        "documents": [{"doc_id": doc_id, "doc_name": doc_id, "doc_path": doc_id}],
        "predictions": [
            {
                "page_id": f"{doc_id}::p000",
                "doc_id": doc_id,
                "page_index": 0,
                "objects": [
                    {
                        "id": "figure-1",
                        "label": "Figure",
                        "bbox": [0.1, 0.1, 0.9, 0.9],
                        "score": None if model == "human annotation" else 0.9,
                    }
                ],
            }
        ],
    }


def _write_source(dataset_root: Path, source: str) -> None:
    """Write one PDF placeholder and its matching annotation."""
    pdf_dir = dataset_root / "documents" / source
    annotation_dir = dataset_root / "annotations" / source
    pdf_dir.mkdir(parents=True)
    annotation_dir.mkdir(parents=True)
    doc_id = f"{source}.pdf"
    (pdf_dir / doc_id).write_bytes(b"%PDF-placeholder")
    (annotation_dir / f"{source}.json").write_text(
        json.dumps(_evaluation_file(doc_id, model="human annotation")),
        encoding="utf-8",
    )


def test_source_and_corpus_workflow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset_root = tmp_path / "dataset"
    output_root = tmp_path / "runs"
    for source in ("first", "second"):
        _write_source(dataset_root, source)

    configs: list[dict[str, Any]] = []

    class FakeConfig:
        """Capture the configuration passed to the fake adapter."""

        def __init__(self, **kwargs: Any) -> None:
            configs.append(kwargs)

    def fake_runner(
        input_pdf_dir: str | Path,
        output_json_path: str | Path,
        *,
        config: FakeConfig,
    ) -> Path:
        """Write deterministic predictions without loading a model."""
        del config
        pdf_paths = sorted(Path(input_pdf_dir).glob("*.pdf"))
        output_json_path = Path(output_json_path)
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(_evaluation_file(pdf_paths[0].name, model="fake model")),
            encoding="utf-8",
        )
        return output_json_path

    monkeypatch.setattr(
        benchmark, "_load_adapter", lambda model: (FakeConfig, fake_runner)
    )
    monkeypatch.setattr(evaluate_model_module, "ROOT", tmp_path)

    for source in ("first", "second"):
        report = benchmark.evaluate_source(
            model="doclayoutyolo",
            source=source,
            dataset_root=dataset_root,
            output_root=output_root,
            device="cuda:0",
        )
        assert report["metrics"]["0.5"]["per_class"]["Figure"]["precision"] == 1

    assert configs == [
        {
            "device": "cuda:0",
            "store_doc_path_as": "absolute",
            "filter_small": True,
        },
        {
            "device": "cuda:0",
            "store_doc_path_as": "absolute",
            "filter_small": True,
        },
    ]

    report = benchmark.evaluate_corpus(
        model="doclayoutyolo",
        sources=("first", "second"),
        output_root=output_root,
    )
    assert report["documents_mismatch"] == {"only_gt": [], "only_pred": []}
    corpus = load_json(output_root / "doclayoutyolo/predictions/corpus.json")
    assert {document["doc_id"] for document in corpus["documents"]} == {
        "first.pdf",
        "second.pdf",
    }

    with pytest.raises(FileExistsError):
        benchmark.evaluate_source(
            model="doclayoutyolo",
            source="first",
            dataset_root=dataset_root,
            output_root=output_root,
        )

    model_root = output_root / "doclayoutyolo"
    for kind in ("ground_truth", "predictions"):
        first_path = model_root / kind / "sources/first.json"
        second_path = model_root / kind / "sources/second.json"
        second_path.write_text(first_path.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="repeated across sources"):
        benchmark.evaluate_corpus(
            model="doclayoutyolo",
            sources=("first", "second"),
            output_root=output_root,
            overwrite=True,
        )
