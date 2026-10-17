"""
Shared utility functions for the data-snapshot package.

Provides common helpers used across adapter modules and evaluation tools.
"""

from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Sequence

from PIL import Image

from data_snapshot.constants import MIN_PREDICTION_AREA


def _log_render_event(
    pdf_path: str | Path,
    event: str,
    *,
    dpi: int,
    page_index: int | None = None,
    warnings: str = "",
    **details: Any,
) -> None:
    """Record one PDF operation with stable document and page identifiers."""
    record = {
        "timestamp": utc_now_iso(),
        "event": event,
        "status": (
            "error" if event == "render_failed" else "warning" if warnings else "ok"
        ),
        "doc_id": Path(pdf_path).name,
        "pdf_path": str(Path(pdf_path).resolve()),
        "backend": "pymupdf",
        "dpi": dpi,
        "page_index": page_index,
        "page_number": None if page_index is None else page_index + 1,
        "warnings": warnings,
        **details,
    }
    logging.getLogger("data_snapshot.rendering").info(json.dumps(record))


def convert_pdf_to_images(
    pdf_path: str | Path,
    dpi: int = 300,
    backend: Literal["pymupdf", "pdf2image"] = "pymupdf",
) -> list[Image.Image]:
    """Convert PDF pages to PIL images and log PyMuPDF rendering diagnostics.

    Parameters
    ----------
    pdf_path : str | Path
        Path to the PDF file.
    dpi : int
        Resolution for rendering, in dots per inch.
    backend : {"pymupdf", "pdf2image"}
        Library to use for PDF rendering.  ``"pymupdf"`` (default) is
        faster and requires no system dependencies.  ``"pdf2image"``
        delegates to poppler via the ``pdf2image`` package.

    Returns
    -------
    list[Image.Image]
        One PIL RGB image per page, in document order.

    Raises
    ------
    ValueError
        If *backend* is not one of the supported values.
    ImportError
        If the requested backend package is not installed.

    Notes
    -----
    PyMuPDF events use the ``data_snapshot.rendering`` logger. Page indices are
    zero-based and page numbers are one-based. Warnings do not imply defective
    images; rendering exceptions are logged and re-raised without skipping pages.
    """
    if backend == "pymupdf":
        try:
            import pymupdf  # noqa: F811
        except ImportError as exc:
            raise ImportError(
                "pymupdf is required for the 'pymupdf' backend. "
                "Install the locked core environment with: uv sync --locked"
            ) from exc

        images: list[Image.Image] = []
        page_index = None
        page_count = None
        phase = "open"
        # shortcut: MuPDF's message buffer is global; use processes for parallel rendering.
        pymupdf.TOOLS.reset_mupdf_warnings()
        try:
            with pymupdf.open(str(pdf_path)) as doc:
                page_count = doc.page_count
                _log_render_event(
                    pdf_path,
                    "document_opened",
                    dpi=dpi,
                    warnings=pymupdf.TOOLS.mupdf_warnings(),
                    page_count=page_count,
                    pymupdf_version=pymupdf.VersionBind,
                    mupdf_version=pymupdf.VersionFitz,
                )
                for page_index in range(page_count):
                    phase = "page"
                    page = doc.load_page(page_index)
                    pix = page.get_pixmap(dpi=dpi)
                    image = pix.pil_image()
                    images.append(image)
                    _log_render_event(
                        pdf_path,
                        "page_rendered",
                        dpi=dpi,
                        page_index=page_index,
                        warnings=pymupdf.TOOLS.mupdf_warnings(),
                        width=image.width,
                        height=image.height,
                    )
                page_index = None
                phase = "close"
            _log_render_event(
                pdf_path,
                "document_finished",
                dpi=dpi,
                warnings=pymupdf.TOOLS.mupdf_warnings(),
                page_count=page_count,
                rendered_pages=len(images),
            )
        except BaseException as exc:
            _log_render_event(
                pdf_path,
                "render_failed",
                dpi=dpi,
                page_index=page_index,
                warnings=pymupdf.TOOLS.mupdf_warnings(),
                phase=phase,
                page_count=page_count,
                rendered_pages=len(images),
                exception=f"{type(exc).__name__}: {exc}",
                traceback=traceback.format_exc(),
                pymupdf_version=pymupdf.VersionBind,
                mupdf_version=pymupdf.VersionFitz,
            )
            raise
        return images

    if backend == "pdf2image":
        try:
            from pdf2image import convert_from_path
        except ImportError as exc:
            raise ImportError(
                "pdf2image is required for the 'pdf2image' backend. "
                "Install it with: uv sync --locked --extra pdf2image"
            ) from exc

        return convert_from_path(str(pdf_path), dpi=dpi)

    raise ValueError(
        f"Unknown PDF backend: {backend!r}. "
        f"Supported values: 'pymupdf', 'pdf2image'."
    )


def load_json(path: str | Path) -> dict:
    """Load and return a JSON file as a dictionary.

    Parameters
    ----------
    path : str | Path
        Path to the JSON file.

    Returns
    -------
    dict
        Parsed JSON contents.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clamp01(x: float) -> float:
    """Clamp a numeric value to the ``[0, 1]`` range.

    Parameters
    ----------
    x : float
        Value to clamp.

    Returns
    -------
    float
        Clamped value.
    """
    if x < 0.0:
        return 0.0
    elif x > 1.0:
        return 1.0
    else:
        return x


def sanitize_bbox(b: list[float]) -> tuple[float, float, float, float]:
    """Validate and clamp a bounding box to ``[0, 1]``.

    Parameters
    ----------
    b : list[float]
        A four-element list ``[x1, y1, x2, y2]``.

    Returns
    -------
    tuple[float, float, float, float]
        Clamped ``(x1, y1, x2, y2)``.

    Raises
    ------
    ValueError
        If *b* is not a four-element list.
    """
    if not (isinstance(b, list) and len(b) == 4):
        raise ValueError(f"Invalid bbox: {b}")
    x1, y1, x2, y2 = map(float, b)
    return (clamp01(x1), clamp01(y1), clamp01(x2), clamp01(y2))


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string with ``Z`` suffix.

    Returns
    -------
    str
        Timestamp in the form ``"2026-03-26T07:00:00Z"``.
    """
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def normalize_bboxes_xyxy(
    bboxes: Sequence[Sequence[float]], width: int, height: int
) -> list[list[float]]:
    """Convert bounding boxes to normalized ``[0, 1]`` xyxy format.

    Absolute-pixel coordinates (detected via a ``> 1.5`` heuristic) are
    divided by the image dimensions.  All coordinates are clamped to
    ``[0, 1]`` and reordered so that ``x1 < x2`` and ``y1 < y2``.
    Degenerate boxes (zero area after clamping) are silently dropped.

    Parameters
    ----------
    bboxes : Sequence[Sequence[float]]
        Raw bounding boxes, each as ``[x1, y1, x2, y2]``.
    width : int
        Image width in pixels.
    height : int
        Image height in pixels.

    Returns
    -------
    list[list[float]]
        Normalized bounding boxes that passed validation.
    """
    return [
        bbox for _, bbox in normalize_bboxes_xyxy_with_indices(bboxes, width, height)
    ]


def normalize_bboxes_xyxy_with_indices(
    bboxes: Sequence[Sequence[float]], width: int, height: int
) -> list[tuple[int, list[float]]]:
    """Normalize bounding boxes while retaining their source indices.

    Parameters
    ----------
    bboxes : Sequence[Sequence[float]]
        Raw bounding boxes, each as ``[x1, y1, x2, y2]``.
    width : int
        Image width in pixels.
    height : int
        Image height in pixels.

    Returns
    -------
    list[tuple[int, list[float]]]
        Source index and normalized bounding box for each valid input box.
    """
    out: list[tuple[int, list[float]]] = []
    for index, bb in enumerate(bboxes):
        if len(bb) != 4:
            continue
        x1, y1, x2, y2 = (float(v) for v in bb)

        # Heuristic: if any coord > 1.5, assume absolute pixels.
        if max(abs(x1), abs(y1), abs(x2), abs(y2)) > 1.5:
            x1, x2 = x1 / float(width), x2 / float(width)
            y1, y2 = y1 / float(height), y2 / float(height)

        nx1, nx2 = sorted([clamp01(x1), clamp01(x2)])
        ny1, ny2 = sorted([clamp01(y1), clamp01(y2)])

        if nx2 <= nx1 or ny2 <= ny1:
            continue  # degenerate

        out.append((index, [nx1, ny1, nx2, ny2]))
    return out


def filter_small_predictions(
    objects: list[dict[str, Any]],
    min_area: float = MIN_PREDICTION_AREA,
) -> list[dict[str, Any]]:
    """Remove predictions whose normalized bounding-box area is below a threshold.

    This filters out spurious, near-zero-area detections that are unlikely to
    represent meaningful page elements.

    Parameters
    ----------
    objects : list[dict[str, Any]]
        Prediction objects, each containing a ``"bbox"`` key with normalised
        ``[x1, y1, x2, y2]`` coordinates in the ``[0, 1]`` range.
    min_area : float
        Minimum normalised area (width × height) a prediction must have to be
        kept.

    Returns
    -------
    list[dict[str, Any]]
        Filtered list retaining only predictions whose area ≥ *min_area*.
    """
    kept: list[dict[str, Any]] = []
    for obj in objects:
        x1, y1, x2, y2 = obj["bbox"]
        area = abs(x2 - x1) * abs(y2 - y1)
        if area >= min_area:
            kept.append(obj)
    return kept
