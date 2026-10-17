"""Run reproducible source and corpus evaluations for integrated models."""

from __future__ import annotations

import importlib
import json
import logging
import traceback
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from data_snapshot.constants import ROOT
from data_snapshot.evaluation.evaluate_model import evaluate, print_summary_metrics
from data_snapshot.evaluation.merge_batch_preds import combine_evaluation_files
from data_snapshot.utils import load_json, utc_now_iso

DEFAULT_OUTPUT_ROOT = ROOT / "data/evaluation_runs"

_ADAPTERS = {
    "unlimitedocr": (
        "data_snapshot.inference.unlimitedocr",
        "UnlimitedOCRConfig",
        "run_unlimitedocr_adapter_directory",
    ),
    "doclayoutyolo": (
        "data_snapshot.inference.doclayoutyolo",
        "DocLayoutYOLOConfig",
        "run_doclayout_yolo_adapter_directory",
    ),
    "tfid": (
        "data_snapshot.inference.tfid",
        "TFIDConfig",
        "run_tfid_adapter_directory",
    ),
    "yolo11": (
        "data_snapshot.inference.yolo11",
        "YOLO11Config",
        "run_yolo11_adapter_directory",
    ),
    "yolo26": (
        "data_snapshot.inference.yolo26",
        "YOLO26Config",
        "run_yolo26_adapter_directory",
    ),
}


def _validate_name(value: str, *, kind: str) -> None:
    """Validate a model or source name before using it in an output path."""
    if not value or Path(value).name != value or value in {".", ".."}:
        raise ValueError(f"Invalid {kind} name: {value!r}")


def _load_adapter(model: str) -> tuple[type[Any], Callable[..., Path]]:
    """Load only the selected model adapter and its optional dependencies."""
    try:
        module_name, config_name, runner_name = _ADAPTERS[model]
    except KeyError as exc:
        choices = ", ".join(sorted(_ADAPTERS))
        raise ValueError(
            f"Unsupported model {model!r}. Choose from: {choices}"
        ) from exc

    module = importlib.import_module(module_name)
    return getattr(module, config_name), getattr(module, runner_name)


def _document_ids(path: str | Path) -> list[str]:
    """Read document identifiers from an evaluation JSON file."""
    data = load_json(Path(path))
    return [document["doc_id"] for document in data.get("documents", [])]


def _validate_source_inputs(pdf_dir: Path, annotation_dir: Path) -> list[Path]:
    """Validate source directories and return their annotation files."""
    pdf_paths = sorted(pdf_dir.rglob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"No PDFs found under: {pdf_dir}")

    annotation_paths = sorted(annotation_dir.glob("*.json"))
    if not annotation_paths:
        raise FileNotFoundError(
            f"No annotation JSON files found under: {annotation_dir}"
        )

    pdf_ids = [path.name for path in pdf_paths]
    if len(pdf_ids) != len(set(pdf_ids)):
        raise ValueError(f"Duplicate PDF filenames found under: {pdf_dir}")

    annotation_ids = [
        doc_id for path in annotation_paths for doc_id in _document_ids(path)
    ]
    if len(annotation_ids) != len(set(annotation_ids)):
        raise ValueError(f"Duplicate annotation doc_ids found under: {annotation_dir}")

    only_annotations = sorted(set(annotation_ids) - set(pdf_ids))
    only_pdfs = sorted(set(pdf_ids) - set(annotation_ids))
    if only_annotations or only_pdfs:
        raise ValueError(
            "PDF and annotation document IDs do not match: "
            f"only_annotations={only_annotations}, only_pdfs={only_pdfs}"
        )

    return annotation_paths


def _ensure_outputs_available(paths: Sequence[Path], *, overwrite: bool) -> None:
    """Refuse to replace generated files unless overwrite is explicit."""
    existing = [path for path in paths if path.exists()]
    if existing and not overwrite:
        joined = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"Output already exists: {joined}")


def _validate_matching_documents(gt_path: Path, pred_path: Path) -> None:
    """Require ground truth and predictions to cover the same documents."""
    gt_ids = set(_document_ids(gt_path))
    pred_ids = set(_document_ids(pred_path))
    if gt_ids != pred_ids:
        raise ValueError(
            "Ground truth and prediction document IDs do not match: "
            f"only_gt={sorted(gt_ids - pred_ids)}, "
            f"only_predictions={sorted(pred_ids - gt_ids)}"
        )


def _validate_disjoint_sources(paths: Sequence[Path]) -> None:
    """Reject document IDs repeated across source files."""
    seen: set[str] = set()
    for path in paths:
        current = set(_document_ids(path))
        repeated = sorted(seen & current)
        if repeated:
            raise ValueError(f"Document IDs repeated across sources: {repeated}")
        seen.update(current)


@contextmanager
def _render_diagnostics_log(
    output_root: Path, source: str, config_values: dict[str, Any]
) -> Iterator[None]:
    """Persist rendering events and inference failures in a fresh source log."""
    log_dir = output_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = (
        log_dir / f"{source}_{datetime.now(timezone.utc):%Y%m%dT%H%M%S_%fZ}.jsonl"
    )
    handler = logging.FileHandler(log_path, mode="x", encoding="utf-8")
    logger = logging.getLogger("data_snapshot.rendering")
    old_level, old_propagate = logger.level, logger.propagate
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addHandler(handler)
    context = {"model": output_root.name, "source": source}
    print(f"Rendering diagnostics: {log_path}", flush=True)
    try:
        logger.info(
            json.dumps(
                {
                    "timestamp": utc_now_iso(),
                    "event": "inference_started",
                    **context,
                    "adapter_config": config_values,
                },
                default=str,
            )
        )
        yield
        logger.info(
            json.dumps(
                {"timestamp": utc_now_iso(), "event": "inference_finished", **context}
            )
        )
    except BaseException as exc:
        logger.info(
            json.dumps(
                {
                    "timestamp": utc_now_iso(),
                    "event": "inference_failed",
                    "status": "error",
                    **context,
                    "exception": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                }
            )
        )
        raise
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)
        logger.propagate = old_propagate
        handler.close()


def evaluate_source(
    model: str,
    source: str,
    dataset_root: str | Path,
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    device: str = "cpu",
    adapter_config: dict[str, Any] | None = None,
    run_inference: bool = True,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Run one integrated model against one dataset source.

    Parameters
    ----------
    model : str
        Integrated adapter name: ``doclayoutyolo``, ``tfid``, ``yolo11``,
        ``yolo26``, or ``unlimitedocr``.
    source : str
        Dataset source directory name, such as ``unhcr``.
    dataset_root : str | Path
        Dataset root containing ``documents`` and ``annotations`` directories.
    output_root : str | Path
        Root directory for generated ground truth, predictions, and reports.
    device : str
        Device passed to the selected adapter, such as ``cpu`` or ``cuda:0``.
    adapter_config : dict[str, Any] | None
        Optional model-specific configuration overrides.
    run_inference : bool
        Run the adapter when ``True``. Reuse an existing prediction file when
        ``False``.
    overwrite : bool
        Replace existing outputs when ``True``.

    Returns
    -------
    dict[str, Any]
        Evaluation report containing Figure and Table metrics.

    Raises
    ------
    FileExistsError
        If an output exists and ``overwrite`` is ``False``.
    FileNotFoundError
        If source inputs or a requested existing prediction file are missing.
    ValueError
        If names, document coverage, or adapter configuration are invalid.
    """
    _validate_name(model, kind="model")
    _validate_name(source, kind="source")
    if model not in _ADAPTERS:
        _load_adapter(model)

    dataset_root = Path(dataset_root)
    output_root = Path(output_root) / model
    pdf_dir = dataset_root / "documents" / source
    annotation_dir = dataset_root / "annotations" / source
    annotation_paths = _validate_source_inputs(pdf_dir, annotation_dir)

    gt_path = output_root / "ground_truth/sources" / f"{source}.json"
    pred_path = output_root / "predictions/sources" / f"{source}.json"
    report_path = output_root / "reports/sources" / f"{source}.json"
    generated_paths = [gt_path, report_path]
    if run_inference:
        generated_paths.append(pred_path)
    elif not pred_path.is_file():
        raise FileNotFoundError(f"Prediction file not found: {pred_path}")
    _ensure_outputs_available(generated_paths, overwrite=overwrite)

    if run_inference:
        config_type, runner = _load_adapter(model)
        config_values = {
            "device": device,
            "store_doc_path_as": "absolute",
            "filter_small": True,
        }
        config_values.update(adapter_config or {})
        config = config_type(**config_values)
        with _render_diagnostics_log(output_root, source, config_values):
            runner(pdf_dir, pred_path, config=config)

    combine_evaluation_files(annotation_paths, gt_path)
    _validate_matching_documents(gt_path, pred_path)
    report = evaluate(gt_path, pred_path, output_path=report_path)
    print_summary_metrics(report_path, iou_threshold=0.5)
    return report


def evaluate_corpus(
    model: str,
    sources: Sequence[str],
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Combine completed source runs and evaluate the full corpus.

    Parameters
    ----------
    model : str
        Integrated adapter name used for every source prediction.
    sources : Sequence[str]
        Source names to include in the corpus.
    output_root : str | Path
        Root directory containing the completed source outputs.
    overwrite : bool
        Replace existing corpus outputs when ``True``.

    Returns
    -------
    dict[str, Any]
        Full-corpus evaluation report containing Figure and Table metrics.

    Raises
    ------
    FileExistsError
        If a corpus output exists and ``overwrite`` is ``False``.
    FileNotFoundError
        If a requested source output is missing.
    ValueError
        If model or source names are invalid, repeated, or have mismatched
        document coverage.
    """
    _validate_name(model, kind="model")
    if model not in _ADAPTERS:
        _load_adapter(model)
    if not sources:
        raise ValueError("At least one source is required.")
    if len(sources) != len(set(sources)):
        raise ValueError("Source names must be unique.")
    for source in sources:
        _validate_name(source, kind="source")

    model_root = Path(output_root) / model
    gt_paths = [
        model_root / "ground_truth/sources" / f"{source}.json" for source in sources
    ]
    pred_paths = [
        model_root / "predictions/sources" / f"{source}.json" for source in sources
    ]
    gt_path = model_root / "ground_truth/corpus.json"
    pred_path = model_root / "predictions/corpus.json"
    report_path = model_root / "reports/corpus.json"
    _ensure_outputs_available([gt_path, pred_path, report_path], overwrite=overwrite)

    for source_gt_path, source_pred_path in zip(gt_paths, pred_paths, strict=True):
        _validate_matching_documents(source_gt_path, source_pred_path)
    _validate_disjoint_sources(gt_paths)
    combine_evaluation_files(gt_paths, gt_path)
    combine_evaluation_files(pred_paths, pred_path)
    _validate_matching_documents(gt_path, pred_path)
    report = evaluate(gt_path, pred_path, output_path=report_path)
    print_summary_metrics(report_path, iou_threshold=0.5)
    return report
