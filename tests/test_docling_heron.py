"""Test native Docling conversion without importing the optional model runtime."""

from __future__ import annotations

import json
import hashlib
import sys
from collections.abc import Iterator
from contextlib import contextmanager
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


@pytest.mark.parametrize("document_concurrency", [1, 2])
@pytest.mark.parametrize(
    "config_type", [adapter.DoclingHeronConfig, adapter.DoclingEgretMediumConfig]
)
def test_native_document_links_and_empty_pages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    document_concurrency: int,
    config_type: type[adapter.DoclingHeronConfig],
) -> None:
    """Preserve native refs unchanged while emitting only figure/table bounds.

    Parameters
    ----------
    tmp_path : Path
        Temporary PDFs and output files.
    monkeypatch : pytest.MonkeyPatch
        Optional runtime substitutions.
    document_concurrency : int
        Requested native document concurrency.
    config_type : type[adapter.DoclingHeronConfig]
        Checkpoint configuration sharing the native conversion runner.
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
    original_perf = Mock()
    original_perf.model_copy.side_effect = lambda update: SimpleNamespace(**update)
    settings = SimpleNamespace(perf=original_perf)

    @contextmanager
    def scope(*, perf: SimpleNamespace) -> Iterator[None]:
        """Emulate native scoped settings and restore them even on failure."""
        before = settings.perf
        settings.perf = perf
        try:
            yield
        finally:
            settings.perf = before

    def results(pdfs: list[Path]) -> list[SimpleNamespace]:
        """Verify native concurrency is active when ordered conversion starts."""
        assert settings.perf.doc_batch_size == document_concurrency
        assert settings.perf.doc_batch_concurrency == document_concurrency
        assert [pdf.name for pdf in pdfs] == ["a.pdf", "b.pdf"]
        return [result, result]

    converter.convert_all.side_effect = results
    monkeypatch.setattr(adapter, "_make_converter", lambda cfg: converter)
    monkeypatch.setattr(adapter, "version", lambda name: "test-version")
    monkeypatch.setitem(
        sys.modules,
        "docling.datamodel.base_models",
        SimpleNamespace(
            ConversionStatus=SimpleNamespace(SUCCESS="success"),
            InputFormat=SimpleNamespace(PDF="pdf"),
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "docling.datamodel.settings",
        SimpleNamespace(
            settings=settings,
            scoped=scope,
        ),
    )
    output = tmp_path / "results/pred.json"
    cfg = config_type(
        store_doc_path_as="absolute", document_concurrency=document_concurrency
    )
    adapter.run_docling_heron_adapter_directory(
        tmp_path, output, run_id="test", config=cfg
    )
    data = json.loads(output.read_text())
    assert data["info"]["model"]["name"] == cfg.model_name
    assert data["info"]["model"]["version"] == cfg.model_revision
    assert data["info"]["model"]["weights_sha256"] == cfg.weights_sha256
    assert data["info"]["model"]["layout_preset"] == cfg.layout_preset
    converter.initialize_pipeline.assert_called_once_with("pdf")
    converter.convert.assert_not_called()
    assert settings.perf is original_perf
    assert (
        f"document_concurrency={document_concurrency}" in data["info"]["model"]["notes"]
    )
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
    assert _load_adapter("docling_egret_medium") == (
        adapter.DoclingEgretMediumConfig,
        adapter.run_docling_heron_adapter_directory,
    )
    with pytest.raises(FileExistsError):
        adapter.run_docling_heron_adapter_directory(tmp_path, output, config=cfg)
    valid_pages = result.pages
    result.pages = result.pages[:1]
    with pytest.raises(ValueError, match="page coverage"):
        adapter.run_docling_heron_adapter_directory(
            tmp_path, tmp_path / "incomplete.json", config=cfg
        )
    assert settings.perf is original_perf
    result.status = "partial_success"
    with pytest.raises(RuntimeError, match="partial_success"):
        adapter.run_docling_heron_adapter_directory(
            tmp_path, tmp_path / "failed.json", config=cfg
        )
    assert settings.perf is original_perf
    result.status, result.pages = "success", valid_pages
    converter.convert_all.side_effect = lambda pdfs: [result]
    with pytest.raises(ValueError, match="zip"):
        adapter.run_docling_heron_adapter_directory(
            tmp_path, tmp_path / "missing-document.json", config=cfg
        )
    assert settings.perf is original_perf


@pytest.mark.parametrize(
    "config_type", [adapter.DoclingHeronConfig, adapter.DoclingEgretMediumConfig]
)
def test_converter_checkpoint_and_pipeline_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    config_type: type[adapter.DoclingHeronConfig],
) -> None:
    """Select each pinned checkpoint without changing the shared pipeline.

    Parameters
    ----------
    tmp_path : Path
        Local fake weights.
    monkeypatch : pytest.MonkeyPatch
        Substitute optional model dependencies without importing them.
    config_type : type[adapter.DoclingHeronConfig]
        Heron or Egret configuration to exercise.
    """
    cfg = config_type(artifacts_path=tmp_path, device="cuda:0")
    weights = tmp_path / cfg.model_name.replace("/", "--") / "model.safetensors"
    weights.parent.mkdir()
    weights.write_bytes(b"weights")
    cfg.weights_sha256 = hashlib.sha256(b"weights").hexdigest()
    cuda = Mock()
    cuda.is_available.return_value = True
    spec = Mock()
    layout = SimpleNamespace(model_spec=spec)
    preset = Mock(return_value=layout)
    modules = {
        "torch": SimpleNamespace(cuda=cuda),
        "docling.datamodel.accelerator_options": SimpleNamespace(
            AcceleratorOptions=SimpleNamespace
        ),
        "docling.datamodel.base_models": SimpleNamespace(
            InputFormat=SimpleNamespace(PDF="pdf")
        ),
        "docling.datamodel.object_detection_engine_options": SimpleNamespace(
            TransformersObjectDetectionEngineOptions=SimpleNamespace
        ),
        "docling.datamodel.pipeline_options": SimpleNamespace(
            LayoutObjectDetectionOptions=SimpleNamespace(from_preset=preset),
            PdfPipelineOptions=SimpleNamespace,
            RapidOcrOptions=SimpleNamespace,
        ),
        "docling.document_converter": SimpleNamespace(
            DocumentConverter=SimpleNamespace, PdfFormatOption=SimpleNamespace
        ),
    }
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    converter = adapter._make_converter(cfg)
    options = converter.format_options["pdf"].pipeline_options
    preset.assert_called_once_with(cfg.layout_preset)
    spec.model_copy.assert_called_once_with(update={"revision": cfg.model_revision})
    assert options.layout_options.engine_options.torch_dtype == "float32"
    assert options.layout_options.engine_options.compile_model is False
    assert options.accelerator_options.device == "cuda:0"
    assert (
        options.layout_batch_size
        == options.ocr_batch_size
        == options.table_batch_size
        == 1
    )
    assert options.do_ocr and not options.do_table_structure
    assert options.ocr_options.lang == ["en"]
    assert not any(options.ocr_options.rapidocr_params.values())
    cuda.is_available.return_value = False
    with pytest.raises(RuntimeError, match="CUDA requested"):
        adapter._make_converter(cfg)
    weights.write_bytes(b"wrong checkpoint")
    with pytest.raises(ValueError, match="pinned revision"):
        adapter._make_converter(cfg)


@pytest.mark.parametrize("value", [0, 3, -1, True, 1.5])
def test_invalid_document_concurrency(value: object) -> None:
    """Reject unsupported native worker counts before loading the runtime.

    Parameters
    ----------
    value : object
        Invalid worker count.
    """
    with pytest.raises(ValueError, match="document_concurrency"):
        adapter.DoclingHeronConfig(document_concurrency=value)


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
