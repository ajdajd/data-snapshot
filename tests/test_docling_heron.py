"""Test native Docling conversion without importing the optional model runtime."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from jsonschema import Draft202012Validator

from data_snapshot.constants import ROOT
from data_snapshot.evaluation.benchmark import _load_adapter
from data_snapshot.inference import docling_heron as adapter


def _cluster(label: str, box: list[float], score: float, index: int) -> SimpleNamespace:
    """Represent a native cluster whose box is already in top-left coordinates."""
    bbox = Mock()
    bbox.to_top_left_origin.return_value.as_tuple.return_value = tuple(box)
    return SimpleNamespace(
        label=SimpleNamespace(value=label), bbox=bbox, confidence=score, id=index
    )


def _page(clusters: list[SimpleNamespace], number: int = 1) -> SimpleNamespace:
    """Represent a native PDF page with point-based dimensions."""
    return SimpleNamespace(
        page_no=number,
        size=SimpleNamespace(width=100, height=200),
        predictions=SimpleNamespace(layout=SimpleNamespace(clusters=clusters)),
    )


def test_normalization_alignment_scores_and_shared_filter() -> None:
    """Retain native labels/confidences after dropping a degenerate source box."""
    page = _page(
        [
            _cluster("picture", [10, 10, 10, 20], 0.4, 10),
            _cluster("caption", [0, 0, 100, 200], 1.0, 11),
            _cluster("table", [20, 40, 80, 180], 1.5, 12),
            _cluster("picture", [-1, 0, 100, 200], -0.5, 13),
            _cluster("picture", [0, 0, 1, 1], 0.8, 14),
        ]
    )
    objects = adapter._objects_from_page(page, page_id="a.pdf::p000", filter_small=True)
    assert [
        (obj["label"], obj["score"], obj["attributes"]["docling_cluster_id"])
        for obj in objects
    ] == [("Table", 1.0, 12), ("Figure", 0.0, 13)]
    assert objects[0]["bbox"] == pytest.approx([0.2, 0.2, 0.8, 0.9])
    assert objects[1]["bbox"] == [0, 0, 1, 1]
    assert objects[1]["id"] == "a.pdf::p000:1"
    assert (
        len(adapter._objects_from_page(page, page_id="a.pdf::p000", filter_small=False))
        == 3
    )
    page.predictions.layout.clusters[2].confidence = float("nan")
    with pytest.raises(ValueError, match="confidence.*a.pdf"):
        adapter._objects_from_page(page, page_id="a.pdf::p000", filter_small=True)


def test_native_document_links_and_empty_pages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Preserve native refs unchanged while emitting only figure/table bounds.

    Parameters
    ----------
    tmp_path : Path
        Temporary PDFs and output files.
    monkeypatch : pytest.MonkeyPatch
        Optional runtime substitutions.
    """
    (tmp_path / "a.pdf").write_bytes(b"fake")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested/b.pdf").write_bytes(b"fake")
    native = {
        "pictures": [
            {
                "self_ref": "#/pictures/0",
                "captions": [{"cref": "#/texts/0"}],
                "footnotes": [{"cref": "#/texts/1"}],
            }
        ],
        "texts": [
            {"self_ref": "#/texts/0", "text": "caption"},
            {"self_ref": "#/texts/1", "text": "note"},
        ],
    }
    document = Mock()
    document.export_to_dict.return_value = native
    result = SimpleNamespace(
        status="success",
        errors=[],
        input=SimpleNamespace(page_count=2),
        document=document,
        pages=[_page([_cluster("picture", [0, 0, 100, 100], 0.7, 3)]), _page([], 2)],
    )
    converter = Mock()
    converter.convert.return_value = result
    monkeypatch.setattr(adapter, "_make_converter", lambda cfg: converter)
    monkeypatch.setattr(adapter, "version", lambda name: "test-version")
    monkeypatch.setitem(
        sys.modules,
        "docling.datamodel.base_models",
        SimpleNamespace(ConversionStatus=SimpleNamespace(SUCCESS="success")),
    )
    output = tmp_path / "results/pred.json"
    cfg = adapter.DoclingHeronConfig(store_doc_path_as="absolute")
    adapter.run_docling_heron_adapter_directory(
        tmp_path, output, run_id="test", config=cfg
    )
    data = json.loads(output.read_text())
    Draft202012Validator(
        json.loads((ROOT / "docs/data-snapshot-eval-v1.3.schema.json").read_text())
    ).validate(data)
    assert [doc["doc_id"] for doc in data["documents"]] == ["a.pdf", "b.pdf"]
    assert [page["page_id"] for page in data["predictions"]] == [
        "a.pdf::p000",
        "b.pdf::p000",
    ]
    assert (
        json.loads(output.with_suffix(".native").joinpath("a.pdf.json").read_text())
        == native
    )
    assert data["predictions"][0]["objects"][0]["bbox"] == [0, 0, 1, 0.5]
    assert _load_adapter("docling_heron") == (
        adapter.DoclingHeronConfig,
        adapter.run_docling_heron_adapter_directory,
    )
    with pytest.raises(FileExistsError):
        adapter.run_docling_heron_adapter_directory(tmp_path, output, config=cfg)
    result.pages = result.pages[:1]
    with pytest.raises(ValueError, match="page coverage"):
        adapter.run_docling_heron_adapter_directory(
            tmp_path, tmp_path / "incomplete.json", config=cfg
        )
    result.status = "partial_success"
    with pytest.raises(RuntimeError, match="partial_success"):
        adapter.run_docling_heron_adapter_directory(
            tmp_path, tmp_path / "failed.json", config=cfg
        )


def test_missing_pdfs_and_duplicate_names(tmp_path: Path) -> None:
    """Reject ambiguous inputs before loading any optional model dependencies.

    Parameters
    ----------
    tmp_path : Path
        Empty directory populated with duplicate PDF basenames.
    """
    with pytest.raises(FileNotFoundError, match="No PDFs"):
        adapter.run_docling_heron_adapter_directory(tmp_path, tmp_path / "out.json")
    (tmp_path / "nested").mkdir()
    (tmp_path / "a.pdf").write_bytes(b"fake")
    (tmp_path / "nested/a.pdf").write_bytes(b"fake")
    with pytest.raises(ValueError, match="unique"):
        adapter.run_docling_heron_adapter_directory(tmp_path, tmp_path / "out.json")


def test_missing_layout_and_invalid_dimensions() -> None:
    """Fail with page context rather than silently dropping native failures."""
    page = _page([])
    page.size.width = 0
    with pytest.raises(ValueError, match="dimensions"):
        adapter._objects_from_page(page, page_id="a.pdf::p000", filter_small=True)
    page.predictions.layout = None
    with pytest.raises(ValueError, match="Missing.*a.pdf"):
        adapter._objects_from_page(page, page_id="a.pdf::p000", filter_small=True)
