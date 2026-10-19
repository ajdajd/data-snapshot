"""Evaluate native Docling Heron bounds and preserve its document links separately.

PDFs pass through Docling's own backend, OCR, layout postprocessing, and reading
order. Only picture/table layout clusters enter the evaluation JSON. Native
document JSON retains captions and footnotes without custom association rules.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import time
import uuid
from importlib.metadata import version
from pathlib import Path
from typing import Any

from data_snapshot.constants import LABEL_MAP, MIN_PREDICTION_AREA, MODELS_DIR, ROOT
from data_snapshot.utils import (
    filter_small_predictions,
    normalize_bboxes_xyxy_with_indices,
    utc_now_iso,
)

MODEL_NAME = "docling-project/docling-layout-heron"
MODEL_REVISION = "8f39ad3c0b4c58e9c2d2c84a38465abf757272d8"
_WEIGHTS_SHA256 = "00333a43451945aaf89db8ca9c0a17e75d1537c17db60fdb91aa95f4c7929e0c"
_LABELS = {"picture": LABEL_MAP["1"], "table": LABEL_MAP["2"]}


class DoclingHeronConfig:
    """Configure native Docling Heron evaluation using prefetched local assets.

    Parameters
    ----------
    artifacts_path : str | Path
        Docling artifact root with Heron and English RapidOCR models. Relative
        paths resolve from the repository root. No assets are downloaded here.
    device : str
        PyTorch layout device, such as ``cpu`` or ``cuda:0``. OCR uses CPU.
    store_doc_path_as : {"relative", "absolute"}
        How input PDF paths are recorded in the prediction JSON.
    filter_small : bool
        Apply the existing benchmark area threshold of 0.008.

    Raises
    ------
    ValueError
        If the document path mode is unsupported.
    """

    def __init__(
        self,
        artifacts_path: str | Path = MODELS_DIR / "docling",
        device: str = "cpu",
        store_doc_path_as: str = "relative",
        filter_small: bool = True,
    ) -> None:
        if store_doc_path_as not in {"relative", "absolute"}:
            raise ValueError("store_doc_path_as must be relative or absolute")
        path = Path(artifacts_path)
        self.artifacts_path = path if path.is_absolute() else ROOT / path
        self.device = device
        self.store_doc_path_as = store_doc_path_as
        self.filter_small = filter_small


def _make_converter(config: DoclingHeronConfig) -> Any:
    """Create the smoke-tested native pipeline without downloading assets."""
    import torch
    from docling.datamodel.accelerator_options import AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.object_detection_engine_options import (
        TransformersObjectDetectionEngineOptions,
    )
    from docling.datamodel.pipeline_options import (
        LayoutObjectDetectionOptions,
        PdfPipelineOptions,
        RapidOcrOptions,
    )
    from docling.document_converter import DocumentConverter, PdfFormatOption

    if not config.artifacts_path.is_dir():
        raise FileNotFoundError(f"Prefetch Docling assets into {config.artifacts_path}")
    weights = (
        config.artifacts_path / MODEL_NAME.replace("/", "--") / "model.safetensors"
    )
    digest = hashlib.sha256()
    with weights.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != _WEIGHTS_SHA256:
        raise ValueError(f"Heron weights do not match pinned revision: {weights}")
    if config.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable; refusing CPU fallback")
    layout = LayoutObjectDetectionOptions.from_preset("layout_heron_default")
    layout.model_spec = layout.model_spec.model_copy(
        update={"revision": MODEL_REVISION}
    )
    layout.engine_options = TransformersObjectDetectionEngineOptions(
        torch_dtype="float32", compile_model=False
    )
    options = PdfPipelineOptions(
        artifacts_path=config.artifacts_path,
        accelerator_options=AcceleratorOptions(device=config.device, num_threads=4),
        layout_options=layout,
        do_ocr=True,
        ocr_options=RapidOcrOptions(
            backend="onnxruntime",
            lang=["en"],
            rapidocr_params={
                "EngineConfig.onnxruntime.use_cuda": False,
                "Det.use_cuda": False,
                "Cls.use_cuda": False,
                "Rec.use_cuda": False,
            },
        ),
        do_table_structure=False,
        layout_batch_size=1,
        ocr_batch_size=1,
        table_batch_size=1,
    )
    return DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)},
    )


def _objects_from_page(
    page: Any, *, page_id: str, filter_small: bool
) -> list[dict[str, Any]]:
    """Convert native point coordinates and confidences without box expansion."""
    if page.size is None or page.predictions.layout is None:
        raise ValueError(f"Missing page dimensions or layout: {page_id}")
    width, height = page.size.width, page.size.height
    if not all(math.isfinite(value) and value > 0 for value in (width, height)):
        raise ValueError(f"Invalid page dimensions: {page_id}")
    clusters = page.predictions.layout.clusters
    boxes = []
    for cluster in clusters:
        box = cluster.bbox.to_top_left_origin(page_height=height).as_tuple()
        if not all(math.isfinite(value) for value in box):
            raise ValueError(f"Nonfinite native bounding box: {page_id}")
        # Divide PDF points explicitly; the shared helper also accepts normalized boxes.
        boxes.append([box[0] / width, box[1] / height, box[2] / width, box[3] / height])
    objects = []
    for source_index, bbox in normalize_bboxes_xyxy_with_indices(boxes, 1, 1):
        cluster = clusters[source_index]
        label = _LABELS.get(cluster.label.value)
        if label is None:
            continue
        score = float(cluster.confidence)
        if not math.isfinite(score):
            raise ValueError(f"Nonfinite native confidence: {page_id}")
        objects.append(
            {
                "id": f"{page_id}:{len(objects)}",
                "label": label,
                "bbox": bbox,
                "score": max(0.0, min(1.0, score)),
                "attributes": {"docling_cluster_id": cluster.id},
            }
        )
    return filter_small_predictions(objects) if filter_small else objects


def run_docling_heron_adapter_directory(
    input_pdf_dir: str | Path,
    output_json_path: str | Path,
    *,
    run_id: str | None = None,
    config: DoclingHeronConfig | None = None,
) -> Path:
    """Evaluate native picture/table clusters for every PDF and save native JSON.

    Parameters
    ----------
    input_pdf_dir : str | Path
        Directory searched recursively for PDFs in sorted order.
    output_json_path : str | Path
        Destination for schema v1.3 predictions. Native document JSON is stored
        alongside it in ``<prediction stem>.native/<PDF filename>.json``.
    run_id : str | None
        Run identifier; generated when omitted.
    config : DoclingHeronConfig | None
        Local assets, device, path recording, and shared filtering settings.

    Returns
    -------
    Path
        Written evaluation prediction file.

    Raises
    ------
    FileNotFoundError
        If no PDFs or required local model assets are found.
    FileExistsError
        If predictions or their native evidence directory already exist.
    ValueError
        If filenames repeat, page coverage is incomplete, or detections are invalid.
    RuntimeError
        If CUDA is unavailable or Docling reports a conversion failure.
    """
    cfg = config or DoclingHeronConfig()
    pdfs = sorted(Path(input_pdf_dir).rglob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No PDFs found under: {input_pdf_dir}")
    if len({pdf.name for pdf in pdfs}) != len(pdfs):
        raise ValueError("Input PDF filenames must be unique")
    output = Path(output_json_path)
    native_dir = output.with_suffix(".native")
    for path in (output, native_dir):
        if path.exists():
            raise FileExistsError(f"Output already exists: {path}")
    converter = _make_converter(cfg)
    from docling.datamodel.base_models import ConversionStatus

    output.parent.mkdir(parents=True, exist_ok=True)
    native_dir.mkdir()
    documents, predictions = [], []
    logger = logging.getLogger("data_snapshot.rendering")
    for index, pdf in enumerate(pdfs, 1):
        started = time.perf_counter()
        print(f"Docling [{index}/{len(pdfs)}] {pdf.name}", flush=True)
        result = converter.convert(pdf)
        if result.status != ConversionStatus.SUCCESS or result.errors:
            raise RuntimeError(
                f"Docling failed for {pdf.name}: {result.status}; {result.errors}"
            )
        expected = result.input.page_count
        if [page.page_no for page in result.pages] != list(range(1, expected + 1)):
            raise ValueError(f"Docling page coverage mismatch: {pdf.name}")
        documents.append(
            {
                "doc_id": pdf.name,
                "doc_name": pdf.name,
                "doc_path": (
                    str(pdf.resolve())
                    if cfg.store_doc_path_as == "absolute"
                    else str(pdf.resolve().relative_to(ROOT))
                ),
            }
        )
        for page in result.pages:
            page_index = page.page_no - 1
            page_id = f"{pdf.name}::p{page_index:03d}"
            objects = _objects_from_page(
                page, page_id=page_id, filter_small=cfg.filter_small
            )
            if objects:
                predictions.append(
                    {
                        "page_id": page_id,
                        "doc_id": pdf.name,
                        "page_index": page_index,
                        "objects": objects,
                    }
                )
        with (native_dir / f"{pdf.name}.json").open("x", encoding="utf-8") as stream:
            json.dump(result.document.export_to_dict(), stream, allow_nan=False)
        logger.info(
            json.dumps(
                {
                    "timestamp": utc_now_iso(),
                    "event": "document_finished",
                    "doc_id": pdf.name,
                    "backend": "docling-parse",
                    "expected_pages": expected,
                    "processed_pages": len(result.pages),
                    "elapsed_seconds": time.perf_counter() - started,
                }
            )
        )
    data = {
        "label_map": LABEL_MAP,
        "info": {
            "schema_version": "1.3",
            "type": "prediction",
            "created_at": utc_now_iso(),
            "run_id": run_id or f"docling-heron-{uuid.uuid4().hex[:10]}",
            "model": {
                "name": MODEL_NAME,
                "version": MODEL_REVISION,
                "weights_sha256": _WEIGHTS_SHA256,
                "notes": f"native Docling PDF pipeline; device={cfg.device}; float32; "
                "layout batch=1; native layout postprocessing and associations; "
                "RapidOCR English ONNX CPU; table structure/enrichment disabled; "
                f"filter_small={cfg.filter_small}; min_area={MIN_PREDICTION_AREA}; "
                "native document JSON stored separately; crops do not expand to linked text",
                "packages": {
                    name: version(name)
                    for name in (
                        "docling",
                        "docling-core",
                        "docling-parse",
                        "torch",
                        "transformers",
                        "rapidocr",
                        "onnxruntime",
                    )
                },
            },
            "coordinate_system": {
                "type": "normalized_xyxy",
                "range": [0.0, 1.0],
                "origin": "top_left",
            },
        },
        "documents": documents,
        "predictions": predictions,
    }
    with output.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
    return output


def main() -> None:
    """Run the native Docling adapter from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input_pdf_dir", type=Path, required=True)
    parser.add_argument("--output_json_path", type=Path, required=True)
    parser.add_argument("--artifacts_path", type=Path, default=MODELS_DIR / "docling")
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--store_doc_path_as", choices=["relative", "absolute"], default="relative"
    )
    parser.add_argument("--run_id")
    parser.add_argument(
        "--filter_small_predictions",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    args = parser.parse_args()
    path = run_docling_heron_adapter_directory(
        args.input_pdf_dir,
        args.output_json_path,
        run_id=args.run_id,
        config=DoclingHeronConfig(
            artifacts_path=args.artifacts_path,
            device=args.device,
            store_doc_path_as=args.store_doc_path_as,
            filter_small=args.filter_small_predictions,
        ),
    )
    print(path)


if __name__ == "__main__":
    main()
