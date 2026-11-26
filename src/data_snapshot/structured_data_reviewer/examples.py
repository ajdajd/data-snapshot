"""Load labeled working examples and preprocess uploaded PNGs for local review."""

import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

from data_snapshot.structured_data_extraction.accepted_extraction import (
    accepted_result_model,
)
from data_snapshot.structured_data_extraction.llm import _write_json
from data_snapshot.structured_data_extraction.model_review import (
    apply_proposal,
    create_session,
    load_session,
    save_draft,
)
from data_snapshot.structured_data_extraction.working_model import (
    WorkingModel,
    model_digest,
)

REPO = Path(__file__).resolve().parents[3]


def load_examples() -> dict[str, dict[str, Any]]:
    """Read the three labeled prototype examples from package data.

    Returns
    -------
    dict
        Example definitions keyed by their safe, fixed local identifiers.
    """
    pack = json.loads(Path(__file__).with_name("examples.json").read_text())
    return {
        c["id"]: {**c, "image_path": str(Path(pack["dataset_root"]) / c["image"])}
        for c in pack["examples"]
    }


def open_example(case: dict[str, Any], workspace: Path) -> Path:
    """Create a separate draft session or resume existing user work.

    Parameters
    ----------
    case : dict
        One known example definition, not arbitrary client-supplied paths.
    workspace : Path
        Local prototype work directory.

    Returns
    -------
    Path
        Session with a saved, unaccepted initial draft.
    """
    if case["id"] not in {"income", "financing", "education"}:
        raise ValueError("Unknown working example")
    directory = workspace / case["id"]
    if directory.exists():
        load_session(directory)
        return directory
    image = Path(case["image_path"])
    if hashlib.sha256(image.read_bytes()).hexdigest() != case["image_sha256"]:
        raise ValueError("Working example image changed")
    create_session(image, REPO / case["docling"], directory)
    if case["proposal_dir"]:
        apply_proposal(
            directory, REPO / case["proposal_dir"], 0, "Preloaded saved proposal"
        )
    else:
        save_draft(
            directory,
            WorkingModel.model_validate(case["model"]),
            0,
            "Example sketch",
            "Preloaded hand-authored example; not an LLM output or user acceptance",
        )
    return directory


def load_preloaded_values(session_dir: Path, case: dict[str, Any]) -> Path:
    """Load clearly labeled example data under the current accepted model.

    Parameters
    ----------
    session_dir : Path
        Current accepted review session.
    case : dict
        Known prototype example; values are never passed to live generation.

    Returns
    -------
    Path
        Reviewable preloaded-data directory, explicitly not a new model extraction.
    """
    session = load_session(session_dir)
    if session.accepted_revision is None:
        raise ValueError("Accept the current data model before loading example data")
    model = session.revisions[-1].model
    if (
        model_digest(WorkingModel.model_validate(case["model"]))
        != session.revisions[0].sha256
    ):
        raise ValueError("This session was not initialized from the selected example")
    checked = (
        accepted_result_model(model)
        .model_validate(case["data"])
        .model_dump(mode="json")
    )
    output = (
        session_dir / "extractions" / f"preloaded_revision_{session.accepted_revision}"
    )
    if output.exists():
        return output
    output.mkdir(parents=True)
    _write_json(output / "working_model.json", model.model_dump(mode="json"))
    _write_json(output / "observations.json", checked)
    _write_json(
        output / "run.json",
        {
            "status": "preloaded",
            "data_origin": "Manually transcribed example values; not a live extraction",
            "model_revision": session.accepted_revision,
            "model_sha256": model_digest(model),
            "image_sha256": session.image_sha256,
            "docling_sha256": session.docling_sha256,
            "docling_run_sha256": session.docling_run_sha256,
            "api_attempts": 0,
        },
    )
    return output


def preprocess_upload(content: bytes, workspace: Path) -> Path:
    """Run existing local Docling CLI offline and create a fresh PNG review session.

    Parameters
    ----------
    content : bytes
        Uploaded PNG bytes, validated before local preprocessing.
    workspace : Path
        Local work directory; generated identifiers never use upload filenames.

    Returns
    -------
    Path
        Session with matched image/Docling snapshots and no proposed model yet.
    """
    import fitz

    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Please upload a PNG image")
    with fitz.open(stream=content, filetype="png") as document:
        document[0].get_pixmap()
    root = workspace / "uploads" / uuid.uuid4().hex
    root.mkdir(parents=True)
    image = root / "snapshot.png"
    image.write_bytes(content)
    environment = {
        **os.environ,
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "TOKENIZERS_PARALLELISM": "false",
    }
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_snapshot.structured_data_extraction",
                str(image),
                "--pipeline",
                "standard",
                "--device",
                "cpu",
                "--output-dir",
                str(root / "docling"),
            ],
            env=environment,
            capture_output=True,
            text=True,
            timeout=900,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError(
            f"Local Docling preprocessing timed out; uploaded input remains at {image}"
        ) from error
    (root / "docling.log").write_text(completed.stdout + "\n" + completed.stderr)
    if completed.returncode:
        raise ValueError(
            f'Local Docling preprocessing failed. See {root / "docling.log"}'
        )
    directory = root / "review"
    create_session(image, root / "docling/snapshot/native.json", directory)
    return directory
