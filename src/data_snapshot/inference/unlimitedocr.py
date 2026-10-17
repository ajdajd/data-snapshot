"""Convert native Transformers Unlimited-OCR detections to evaluation v1.3.

Only image and table regions are retained. Captions are not associated with
objects. The native processor supplies no region confidence, so scores are 1.0.
"""

from __future__ import annotations

import argparse
import json
import math
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from tqdm.auto import tqdm

from data_snapshot.constants import INPUT_PDF_DIR, LABEL_MAP, MIN_PREDICTION_AREA, ROOT
from data_snapshot.utils import (
    convert_pdf_to_images,
    filter_small_predictions,
    normalize_bboxes_xyxy_with_indices,
    utc_now_iso,
)

MODEL_ID_DEFAULT = "baidu/Unlimited-OCR"
MODEL_REVISION_DEFAULT = "8249d20b2822a7d8a4c22c8d8c9069b5ac36bda3"
OUTPUT_JSON_PATH = ROOT / "data/evaluation_input/unlimitedocr.json"
_LABEL_NORMALIZATION = {"image": LABEL_MAP["1"], "table": LABEL_MAP["2"]}


@dataclass
class UnlimitedOCRConfig:
    """Configure page-by-page Unlimited-OCR prediction.

    Parameters
    ----------
    model_id : str
        Hugging Face model identifier or local checkpoint directory.
    revision : str
        Checkpoint revision; select a matching revision when changing model_id.
    device : str
        CUDA device, such as ``cuda:0``. BF16 support is required.
    dpi : int
        PDF rendering resolution.
    store_doc_path_as : {"relative", "absolute"}
        Store document paths relative to the repository root or as absolute paths.
    filter_small : bool
        Apply the shared minimum normalized area of 0.008.
    pdf_backend : {"pymupdf", "pdf2image"}
        PDF rendering backend.
    max_length : int
        Maximum total sequence length, including image and prompt tokens.
    """

    model_id: str = MODEL_ID_DEFAULT
    revision: str = MODEL_REVISION_DEFAULT
    device: str = "cuda:0"
    dpi: int = 300
    store_doc_path_as: Literal["relative", "absolute"] = "relative"
    filter_small: bool = True
    pdf_backend: Literal["pymupdf", "pdf2image"] = "pymupdf"
    max_length: int = 32768


def _objects_from_detections(
    detections: list[dict[str, Any]], *, page_id: str, filter_small: bool
) -> list[dict[str, Any]]:
    """Map native regions and their 0–999 boxes to canonical prediction objects."""
    labels: list[str] = []
    boxes: list[list[float]] = []
    for detection in detections:
        label = _LABEL_NORMALIZATION.get(
            str(detection.get("region_type", "")).strip().lower()
        )
        if label is None:
            continue
        box = detection.get("box")
        try:
            if not isinstance(box, (list, tuple)) or len(box) != 4:
                raise ValueError("Expected four coordinates")
            coordinates = [float(value) / 999.0 for value in box]
            if not all(math.isfinite(value) for value in coordinates):
                raise ValueError("Coordinates must be finite")
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                f"Invalid Unlimited-OCR box on {page_id}: {box!r}"
            ) from exc
        labels.append(label)
        boxes.append(coordinates)

    objects = [
        {
            "id": f"{page_id}:{object_index}",
            "label": labels[source_index],
            "bbox": bbox,
            "score": 1.0,
        }
        for object_index, (source_index, bbox) in enumerate(
            normalize_bboxes_xyxy_with_indices(boxes, width=1, height=1)
        )
    ]
    return filter_small_predictions(objects) if filter_small else objects


def run_unlimitedocr_adapter_directory(
    input_pdf_dir: str | Path,
    output_json_path: str | Path,
    *,
    run_id: str | None = None,
    config: UnlimitedOCRConfig | None = None,
) -> Path:
    """Run Unlimited-OCR on recursively discovered PDFs and write v1.3 JSON.

    Parameters
    ----------
    input_pdf_dir : str | Path
        Directory containing PDF inputs.
    output_json_path : str | Path
        Destination for one combined prediction file.
    run_id : str | None
        Run identifier; generated when omitted.
    config : UnlimitedOCRConfig | None
        Inference settings; defaults to a pinned checkpoint on CUDA device 0.

    Returns
    -------
    Path
        Written prediction file.

    Raises
    ------
    FileNotFoundError
        If no PDFs are found.
    ImportError
        If the native model runtime is unavailable.
    ValueError
        If configuration, document identifiers, or relevant boxes are invalid,
        or generation reaches its length limit without an end token.
    RuntimeError
        If the selected device cannot execute CUDA BF16 inference.
    """
    cfg = config or UnlimitedOCRConfig()
    if cfg.device.split(":")[0] != "cuda":
        raise ValueError("Unlimited-OCR requires a CUDA device, such as cuda:0.")
    if cfg.store_doc_path_as not in {"relative", "absolute"}:
        raise ValueError("store_doc_path_as must be 'relative' or 'absolute'.")
    if cfg.pdf_backend not in {"pymupdf", "pdf2image"}:
        raise ValueError("pdf_backend must be 'pymupdf' or 'pdf2image'.")
    if cfg.dpi <= 0 or cfg.max_length <= 0:
        raise ValueError("dpi and max_length must be positive.")

    pdf_files = sorted(Path(input_pdf_dir).rglob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDFs found under: {input_pdf_dir}")
    if len({path.name for path in pdf_files}) != len(pdf_files):
        raise ValueError("PDF filenames must be unique to produce unique doc_ids.")

    try:
        import torch
        import transformers
        from transformers import AutoProcessor, UnlimitedOcrForConditionalGeneration
    except ImportError as exc:
        raise ImportError(
            "Unlimited-OCR requires its native Transformers runtime. Run: "
            "uv sync --locked --extra unlimitedocr"
        ) from exc

    if not torch.cuda.is_available():
        raise RuntimeError("Unlimited-OCR requires an available CUDA GPU.")

    with torch.cuda.device(cfg.device):
        if not torch.cuda.is_bf16_supported():
            raise RuntimeError("Unlimited-OCR requires a CUDA GPU with BF16 support.")

    processor = AutoProcessor.from_pretrained(
        cfg.model_id, revision=cfg.revision, trust_remote_code=False
    )
    model = UnlimitedOcrForConditionalGeneration.from_pretrained(
        cfg.model_id,
        revision=cfg.revision,
        trust_remote_code=False,
        use_safetensors=True,
        dtype=torch.bfloat16,
        device_map=cfg.device,
    ).eval()
    documents: list[dict[str, str]] = []
    predictions: list[dict[str, Any]] = []

    for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
        doc_id = pdf_path.name
        doc_path = pdf_path.resolve()
        documents.append(
            {
                "doc_id": doc_id,
                "doc_name": doc_id,
                "doc_path": str(
                    doc_path.relative_to(ROOT)
                    if cfg.store_doc_path_as == "relative"
                    else doc_path
                ),
            }
        )
        images = convert_pdf_to_images(pdf_path, dpi=cfg.dpi, backend=cfg.pdf_backend)
        for page_index, image in enumerate(images):
            page_id = f"{doc_id}::p{page_index:03d}"
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image.convert("RGB")},
                        {"type": "text", "text": "document parsing."},
                    ],
                }
            ]
            inputs = processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
                processor_kwargs={"crop_to_patches": True},
            ).to(model.device, model.dtype)
            with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
                output = model.generate(
                    **inputs,
                    do_sample=False,
                    max_length=cfg.max_length,
                    max_new_tokens=None,
                    no_repeat_ngram_size=35,
                    no_repeat_ngram_window_size=128,
                    use_cache=True,
                )
            if (
                output.shape[1] >= cfg.max_length
                and output[0, -1].item() != processor.tokenizer.eos_token_id
            ):
                raise ValueError(
                    f"Unlimited-OCR reached max_length={cfg.max_length} on {page_id}; "
                    "increase the limit before evaluating these predictions."
                )
            _, detections = processor.decode(
                output[0, inputs["input_ids"].shape[1] :],
                skip_special_tokens=False,
                return_detections=True,
            )
            objects = _objects_from_detections(
                detections, page_id=page_id, filter_small=cfg.filter_small
            )
            if objects:
                predictions.append(
                    {
                        "page_id": page_id,
                        "doc_id": doc_id,
                        "page_index": page_index,
                        "objects": objects,
                    }
                )

    out = {
        "label_map": LABEL_MAP,
        "info": {
            "schema_version": "1.3",
            "type": "prediction",
            "created_at": utc_now_iso(),
            "run_id": run_id or f"unlimitedocr-{uuid.uuid4().hex[:10]}",
            "model": {
                "name": cfg.model_id,
                "version": getattr(model.config, "_commit_hash", None)
                or (
                    str(Path(cfg.model_id).resolve())
                    if Path(cfg.model_id).is_dir()
                    else cfg.revision
                ),
                "notes": (
                    f"adapter=unlimitedocr; transformers={transformers.__version__}; "
                    f"device={cfg.device}; dpi={cfg.dpi}; pdf_backend={cfg.pdf_backend}; "
                    f"max_length={cfg.max_length}; mode=gundam; temperature=0; "
                    "no_repeat_ngram_size=35; no_repeat_ngram_window_size=128; "
                    f"filter_small={cfg.filter_small}; min_area={MIN_PREDICTION_AREA}; "
                    "score=1.0 (no region confidence)"
                ),
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
    output_json_path = Path(output_json_path)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=4, allow_nan=False), encoding="utf-8"
    )
    return output_json_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Unlimited-OCR over PDFs and write v1.3 predictions."
    )
    parser.add_argument("--input_pdf_dir", default=str(INPUT_PDF_DIR))
    parser.add_argument("--output_json_path", default=str(OUTPUT_JSON_PATH))
    parser.add_argument("--run_id", default=None)
    parser.add_argument("--model_id", default=MODEL_ID_DEFAULT)
    parser.add_argument("--revision", default=MODEL_REVISION_DEFAULT)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--dpi", type=int, default=300)
    parser.add_argument("--max_length", type=int, default=32768)
    parser.add_argument(
        "--store_doc_path_as", choices=["relative", "absolute"], default="relative"
    )
    parser.add_argument(
        "--pdf_backend", choices=["pymupdf", "pdf2image"], default="pymupdf"
    )
    parser.add_argument(
        "--filter_small_predictions",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    args = parser.parse_args()
    output_path = run_unlimitedocr_adapter_directory(
        args.input_pdf_dir,
        args.output_json_path,
        run_id=args.run_id,
        config=UnlimitedOCRConfig(
            model_id=args.model_id,
            revision=args.revision,
            device=args.device,
            dpi=args.dpi,
            max_length=args.max_length,
            store_doc_path_as=args.store_doc_path_as,
            filter_small=args.filter_small_predictions,
            pdf_backend=args.pdf_backend,
        ),
    )
    print(f"Wrote: {output_path}")
