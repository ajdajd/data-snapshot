"""Persist reviewed long results while retaining the immutable generated layer."""

import fcntl
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .accepted_extraction import accepted_result_model, current_model_matches
from .working_model import WorkingModel, model_digest


def _digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def load_data_review(extraction_dir: Path) -> dict[str, Any]:
    """Load and validate generated results plus any saved correction history.

    Parameters
    ----------
    extraction_dir : Path
        Successful extraction or clearly labeled preloaded-example directory.

    Returns
    -------
    dict
        Report, model, generated/working results and correction/approval state.
    """
    report = json.loads((extraction_dir / "run.json").read_text())
    if report["status"] not in {
        "complete",
        "partial",
        "unsupported",
        "stale",
        "preloaded",
    }:
        raise ValueError("Extraction did not produce reviewable results")
    model = WorkingModel.model_validate_json(
        (extraction_dir / "working_model.json").read_text()
    )
    if model_digest(model) != report["model_sha256"]:
        raise ValueError("Extraction data model snapshot changed")
    validator = accepted_result_model(model)
    generated = validator.model_validate_json(
        (extraction_dir / "observations.json").read_text()
    ).model_dump(mode="json")
    if report["status"] != "preloaded":
        raw = validator.model_validate_json(
            (extraction_dir / "raw_output.txt").read_text()
        ).model_dump(mode="json")
        if raw != generated:
            raise ValueError("Generated results differ from saved raw output")
    path = extraction_dir / "data_review.json"
    review = (
        json.loads(path.read_text())
        if path.exists()
        else {
            "generated_sha256": _digest(generated),
            "revisions": [],
            "reviewed_revision": None,
            "reviewed_by": None,
            "reviewed_at": None,
        }
    )
    if review["generated_sha256"] != _digest(generated):
        raise ValueError("Generated data changed after review began")
    for index, revision in enumerate(review["revisions"], 1):
        checked = validator.model_validate(revision["data"]).model_dump(mode="json")
        if revision["number"] != index or revision["sha256"] != _digest(checked):
            raise ValueError("Data-review history changed")
    if review["reviewed_revision"] is not None and (
        review["reviewed_revision"] != len(review["revisions"])
        or not review["revisions"]
    ):
        raise ValueError("Data approval does not match the current revision")
    working = review["revisions"][-1]["data"] if review["revisions"] else generated
    return {
        "report": report,
        "model": model,
        "generated": generated,
        "working": working,
        "review": review,
    }


def save_data_review(
    session_dir: Path,
    extraction_dir: Path,
    data: dict[str, Any],
    expected_revision: int,
    reviewer: str,
    reviewed: bool = False,
) -> dict[str, Any]:
    """Save a correction draft or explicit review decision under the current model.

    Parameters
    ----------
    session_dir, extraction_dir : Path
        Current model-review session and source extraction.
    data : dict
        Edited long results, revalidated against the extraction's model.
    expected_revision : int
        Data revision the editor loaded, or zero for generated data.
    reviewer : str
        Local reviewer label, not an authentication mechanism.
    reviewed : bool, optional
        Explicitly approve the reviewed result, including any declared omissions.

    Returns
    -------
    dict
        Updated working data and review history.

    Raises
    ------
    ValueError
        If edits are stale, invalid, or no longer match the accepted model.
    """
    if not reviewer.strip():
        raise ValueError("Reviewer must not be blank")
    with (extraction_dir / ".review.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = load_data_review(extraction_dir)
        if not current_model_matches(session_dir, state["report"]):
            raise ValueError(
                "Data model changed; accept and extract again before saving these data"
            )
        history = state["review"]
        if expected_revision != len(history["revisions"]):
            raise ValueError("Data changed; reload before saving")
        checked = (
            accepted_result_model(state["model"])
            .model_validate(data)
            .model_dump(mode="json")
        )
        if not history["revisions"] or _digest(checked) != _digest(state["working"]):
            history["revisions"].append(
                {
                    "number": len(history["revisions"]) + 1,
                    "data": checked,
                    "sha256": _digest(checked),
                    "reviewer": reviewer,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            history["reviewed_revision"] = None
            history["reviewed_by"] = None
            history["reviewed_at"] = None
        if reviewed:
            history["reviewed_revision"] = len(history["revisions"])
            history["reviewed_by"] = reviewer
            history["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        temporary = extraction_dir / "data_review.tmp.json"
        with temporary.open("w", encoding="utf-8") as file:
            file.write(
                json.dumps(history, ensure_ascii=False, indent=2, allow_nan=False)
                + "\n"
            )
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(extraction_dir / "data_review.json")
    return load_data_review(extraction_dir)


def reviewed_export(session_dir: Path, extraction_dir: Path) -> dict[str, Any]:
    """Export explicitly reviewed interim JSON with model, provenance and omissions.

    Parameters
    ----------
    session_dir, extraction_dir : Path
        Current accepted session and reviewed extraction.

    Returns
    -------
    dict
        Review package explicitly identified as interim JSON, not SDMX-JSON.

    Raises
    ------
    ValueError
        If the data are unreviewed or stale against the current model.
    """
    state = load_data_review(extraction_dir)
    if state["review"]["reviewed_revision"] is None or not current_model_matches(
        session_dir, state["report"]
    ):
        raise ValueError(
            "Review data against the current accepted data model before export"
        )
    return {
        "format": "data-snapshot-reviewed-json",
        "sdmx_formalization": "pending",
        "model": state["model"].model_dump(mode="json"),
        "model_revision": state["report"]["model_revision"],
        "model_sha256": state["report"]["model_sha256"],
        "image_sha256": state["report"]["image_sha256"],
        "docling_sha256": state["report"]["docling_sha256"],
        "data_origin": state["report"].get("data_origin", "live LLM extraction"),
        "data": state["working"],
        "review": state["review"],
    }
