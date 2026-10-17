"""Exercise Unlimited-OCR conversion and orchestration without model packages."""

from __future__ import annotations

import json
import sys
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from jsonschema import Draft202012Validator
from PIL import Image

from data_snapshot.constants import ROOT
from data_snapshot.evaluation.benchmark import _load_adapter
from data_snapshot.inference import unlimitedocr as adapter


def test_regions_coordinates_alignment_and_filtering() -> None:
    """Discard captions, retain source alignment, and normalize the 999 grid."""
    detections = [
        {"region_type": " image ", "box": [0, 0, 999, 999]},
        {"region_type": "image", "box": [50, 50, 50, 50]},
        {"region_type": "TABLE", "box": [999, 999, 499.5, 499.5]},
        {"region_type": "image_caption", "box": [0, 0, 999, 999]},
        {"region_type": "table_caption", "box": [0, 0, 999, 999]},
        {"region_type": "text", "box": [0, 0, 999, 999]},
        {"region_type": "image", "box": [0, 0, 1, 1]},
    ]
    objects = adapter._objects_from_detections(
        detections, page_id="sample.pdf::p001", filter_small=True
    )
    assert objects == [
        {
            "id": "sample.pdf::p001:0",
            "label": "Figure",
            "bbox": [0.0, 0.0, 1.0, 1.0],
            "score": 1.0,
        },
        {
            "id": "sample.pdf::p001:1",
            "label": "Table",
            "bbox": [0.5, 0.5, 1.0, 1.0],
            "score": 1.0,
        },
    ]
    unfiltered = adapter._objects_from_detections(
        detections, page_id="sample.pdf::p001", filter_small=False
    )
    assert len(unfiltered) == 3
    assert unfiltered[-1]["bbox"] == pytest.approx([0, 0, 1 / 999, 1 / 999])


def test_out_of_range_coordinates_are_clamped() -> None:
    """Clip the model's grid without treating it as page pixels."""
    objects = adapter._objects_from_detections(
        [{"region_type": "table", "box": [-999, 0, 9990, 999]}],
        page_id="sample.pdf::p000",
        filter_small=True,
    )
    assert objects[0]["bbox"] == [0, 0, 1, 1]


@pytest.mark.parametrize(
    "box",
    [
        None,
        [1, 2],
        [0, 0, "bad", 999],
        [0, 0, float("nan"), 9],
        [0, 0, float("inf"), 9],
    ],
)
def test_invalid_boxes_report_the_page(box: object) -> None:
    """Reject malformed relevant regions with page context.

    Parameters
    ----------
    box : object
        Malformed generated coordinates.
    """
    with pytest.raises(ValueError, match="sample.pdf::p003"):
        adapter._objects_from_detections(
            [{"region_type": "table", "box": box}],
            page_id="sample.pdf::p003",
            filter_small=True,
        )


@pytest.fixture
def native_runtime(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Provide a fake CUDA model and processor without importing optional extras.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Temporary module and renderer substitutions.

    Returns
    -------
    SimpleNamespace
        Runtime mocks whose inference calls can be inspected.
    """
    torch = SimpleNamespace(
        bfloat16="bf16",
        cuda=SimpleNamespace(
            is_available=lambda: True,
            is_bf16_supported=lambda: True,
            device=lambda device: nullcontext(),
        ),
        inference_mode=nullcontext,
        autocast=lambda *args, **kwargs: nullcontext(),
    )
    inputs = MagicMock()
    inputs.keys.return_value = ["input_ids"]
    inputs.__getitem__.return_value = SimpleNamespace(shape=(1, 3))
    inputs.to.return_value = inputs
    processor = MagicMock()
    processor.apply_chat_template.return_value = inputs
    processor.tokenizer.eos_token_id = 1
    model = MagicMock(device="cuda:0", dtype="bf16")
    model.config = SimpleNamespace(_commit_hash="resolved-checkpoint")
    model.eval.return_value = model
    output = MagicMock(shape=(1, 10))
    output.__getitem__.return_value.item.return_value = 2
    model.generate.return_value = output
    model_loader = MagicMock(return_value=model)
    processor_loader = MagicMock(return_value=processor)
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(
            __version__="5.20.1",
            AutoProcessor=SimpleNamespace(from_pretrained=processor_loader),
            UnlimitedOcrForConditionalGeneration=SimpleNamespace(
                from_pretrained=model_loader
            ),
        ),
    )
    renderer = MagicMock(return_value=[Image.new("RGB", (100, 200))])
    monkeypatch.setattr(adapter, "convert_pdf_to_images", renderer)
    return SimpleNamespace(
        model=model,
        processor=processor,
        model_loader=model_loader,
        processor_loader=processor_loader,
        output=output,
        renderer=renderer,
        torch=torch,
    )


def test_directory_output_and_native_inference(
    tmp_path: Path, native_runtime: SimpleNamespace
) -> None:
    """Produce schema-valid output for sorted PDFs and omit empty pages.

    Parameters
    ----------
    tmp_path : Path
        Temporary input and output directory.
    native_runtime : SimpleNamespace
        Fake model and processor.
    """
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "b.pdf").write_bytes(b"placeholder")
    (tmp_path / "a.pdf").write_bytes(b"placeholder")
    native_runtime.renderer.return_value = [Image.new("RGB", (100, 200))] * 2
    native_runtime.processor.decode.side_effect = [
        ("", [{"region_type": "text", "box": [0, 0, 999, 999]}]),
        ("", [{"region_type": "table", "box": [0, 0, 999, 999]}]),
        ("", []),
        ("", []),
    ]
    output_path = tmp_path / "output/predictions.json"
    result = adapter.run_unlimitedocr_adapter_directory(
        tmp_path,
        output_path,
        run_id="offline-test",
        config=adapter.UnlimitedOCRConfig(store_doc_path_as="absolute"),
    )
    assert result == output_path
    data = json.loads(result.read_text())
    schema = json.loads((ROOT / "docs/data-snapshot-eval-v1.3.schema.json").read_text())
    Draft202012Validator(schema).validate(data)
    assert [doc["doc_id"] for doc in data["documents"]] == ["a.pdf", "b.pdf"]
    assert data["documents"][1]["doc_path"] == str(nested / "b.pdf")
    assert data["predictions"] == [
        {
            "page_id": "a.pdf::p001",
            "doc_id": "a.pdf",
            "page_index": 1,
            "objects": [
                {
                    "id": "a.pdf::p001:0",
                    "label": "Table",
                    "bbox": [0, 0, 1, 1],
                    "score": 1.0,
                }
            ],
        }
    ]
    assert data["info"]["run_id"] == "offline-test"
    assert data["info"]["model"]["version"] == "resolved-checkpoint"
    assert "no region confidence" in data["info"]["model"]["notes"]
    native_runtime.model_loader.assert_called_once_with(
        adapter.MODEL_ID_DEFAULT,
        revision=adapter.MODEL_REVISION_DEFAULT,
        trust_remote_code=False,
        use_safetensors=True,
        dtype="bf16",
        device_map="cuda:0",
    )
    native_runtime.processor_loader.assert_called_once_with(
        adapter.MODEL_ID_DEFAULT,
        revision=adapter.MODEL_REVISION_DEFAULT,
        trust_remote_code=False,
    )
    assert native_runtime.model.generate.call_count == 4
    kwargs = native_runtime.model.generate.call_args.kwargs
    assert kwargs["do_sample"] is False
    assert kwargs["max_length"] == 32768
    assert kwargs["no_repeat_ngram_size"] == 35
    assert kwargs["no_repeat_ngram_window_size"] == 128
    native_runtime.output.__getitem__.assert_any_call((0, slice(3, None)))
    native_runtime.processor.decode.assert_called_with(
        native_runtime.output.__getitem__.return_value,
        skip_special_tokens=False,
        return_detections=True,
    )


def test_truncated_generation_does_not_write_predictions(
    tmp_path: Path, native_runtime: SimpleNamespace
) -> None:
    """Reject a length-limited sequence instead of writing incomplete evidence.

    Parameters
    ----------
    tmp_path : Path
        Temporary input and output directory.
    native_runtime : SimpleNamespace
        Fake model returning a sequence without an end token.
    """
    (tmp_path / "sample.pdf").write_bytes(b"placeholder")
    native_runtime.output.shape = (1, 32768)
    output_path = tmp_path / "predictions.json"
    with pytest.raises(ValueError, match="max_length=32768 on sample.pdf::p000"):
        adapter.run_unlimitedocr_adapter_directory(
            tmp_path,
            output_path,
            config=adapter.UnlimitedOCRConfig(store_doc_path_as="absolute"),
        )
    assert not output_path.exists()


def test_empty_directory_does_not_load_model(tmp_path: Path) -> None:
    """Discover missing inputs before loading any optional model runtime.

    Parameters
    ----------
    tmp_path : Path
        Empty input directory.
    """
    with pytest.raises(FileNotFoundError, match="No PDFs"):
        adapter.run_unlimitedocr_adapter_directory(tmp_path, tmp_path / "output.json")


@pytest.mark.parametrize(
    "settings",
    [
        {"device": "cpu"},
        {"dpi": 0},
        {"max_length": 0},
        {"pdf_backend": "unknown"},
        {"store_doc_path_as": "unknown"},
    ],
)
def test_invalid_config_fails_before_loading(
    tmp_path: Path, settings: dict[str, object]
) -> None:
    """Reject unsupported settings before importing model packages.

    Parameters
    ----------
    tmp_path : Path
        Temporary input and output directory.
    settings : dict[str, object]
        Invalid configuration override.
    """
    with pytest.raises(ValueError):
        adapter.run_unlimitedocr_adapter_directory(
            tmp_path,
            tmp_path / "output.json",
            config=adapter.UnlimitedOCRConfig(**settings),
        )


def test_duplicate_filenames_fail_before_loading(tmp_path: Path) -> None:
    """Prevent recursive inputs from producing duplicate document identifiers.

    Parameters
    ----------
    tmp_path : Path
        Temporary input tree.
    """
    (tmp_path / "sample.pdf").write_bytes(b"placeholder")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested/sample.pdf").write_bytes(b"placeholder")
    with pytest.raises(ValueError, match="filenames must be unique"):
        adapter.run_unlimitedocr_adapter_directory(tmp_path, tmp_path / "output.json")


@pytest.mark.parametrize(
    "cuda_available,bf16_supported", [(False, True), (True, False)]
)
def test_unsupported_gpu_fails_before_checkpoint_loading(
    tmp_path: Path,
    native_runtime: SimpleNamespace,
    cuda_available: bool,
    bf16_supported: bool,
) -> None:
    """Check the GPU before any checkpoint download can start.

    Parameters
    ----------
    tmp_path : Path
        Temporary input directory.
    native_runtime : SimpleNamespace
        Fake model runtime.
    cuda_available : bool
        Whether a CUDA device is available.
    bf16_supported : bool
        Whether the device supports BF16.
    """
    (tmp_path / "sample.pdf").write_bytes(b"placeholder")
    native_runtime.torch.cuda.is_available = lambda: cuda_available
    native_runtime.torch.cuda.is_bf16_supported = lambda: bf16_supported
    with pytest.raises(RuntimeError, match="CUDA GPU"):
        adapter.run_unlimitedocr_adapter_directory(tmp_path, tmp_path / "output.json")
    native_runtime.model_loader.assert_not_called()
    native_runtime.processor_loader.assert_not_called()


def test_missing_native_model_reports_sync_command(
    tmp_path: Path, native_runtime: SimpleNamespace
) -> None:
    """Explain how to switch from an older Transformers environment.

    Parameters
    ----------
    tmp_path : Path
        Temporary input directory.
    native_runtime : SimpleNamespace
        Runtime whose native model symbol is removed for this test.
    """
    del native_runtime
    (tmp_path / "sample.pdf").write_bytes(b"placeholder")
    del sys.modules["transformers"].UnlimitedOcrForConditionalGeneration
    with pytest.raises(ImportError, match="uv sync --locked --extra unlimitedocr"):
        adapter.run_unlimitedocr_adapter_directory(tmp_path, tmp_path / "output.json")


@pytest.mark.parametrize("local_checkpoint", [False, True])
def test_end_token_at_limit_and_relative_paths(
    tmp_path: Path,
    native_runtime: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    local_checkpoint: bool,
) -> None:
    """Accept a complete sequence at the limit and retain an empty document.

    Parameters
    ----------
    tmp_path : Path
        Temporary repository root.
    native_runtime : SimpleNamespace
        Fake runtime returning a terminal token and no objects.
    monkeypatch : pytest.MonkeyPatch
        Temporary repository-root substitution.
    local_checkpoint : bool
        Load a local checkpoint identifier instead of the default remote revision.
    """
    (tmp_path / "sample.pdf").write_bytes(b"placeholder")
    monkeypatch.setattr(adapter, "ROOT", tmp_path)
    native_runtime.output.shape = (1, 32768)
    native_runtime.output.__getitem__.return_value.item.return_value = 1
    native_runtime.processor.decode.return_value = ("", [])
    native_runtime.model.config._commit_hash = None
    config = adapter.UnlimitedOCRConfig()
    if local_checkpoint:
        checkpoint = tmp_path / "checkpoint"
        checkpoint.mkdir()
        config.model_id = str(checkpoint)
    result = adapter.run_unlimitedocr_adapter_directory(
        tmp_path, tmp_path / "predictions.json", config=config
    )
    data = json.loads(result.read_text())
    assert data["documents"] == [
        {"doc_id": "sample.pdf", "doc_name": "sample.pdf", "doc_path": "sample.pdf"}
    ]
    assert data["predictions"] == []
    assert data["info"]["run_id"].startswith("unlimitedocr-")
    assert data["info"]["created_at"].endswith("Z")
    assert data["info"]["model"]["version"] == (
        config.model_id if local_checkpoint else adapter.MODEL_REVISION_DEFAULT
    )


def test_benchmark_can_load_unlimitedocr() -> None:
    """Resolve the new benchmark adapter without importing its model packages."""
    config_type, runner = _load_adapter("unlimitedocr")
    assert config_type is adapter.UnlimitedOCRConfig
    assert runner is adapter.run_unlimitedocr_adapter_directory
