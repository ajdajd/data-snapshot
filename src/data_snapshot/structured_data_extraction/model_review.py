"""Save local model-review drafts and explicit acceptances without making API calls."""

import argparse
import fcntl
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .model_proposal import read_docling_evidence
from .working_model import Text, WorkingModel, model_digest


class ModelRevision(BaseModel):
    """Retain one immutable-by-convention model revision with attribution."""

    model_config = ConfigDict(extra="forbid", strict=True)
    number: int = Field(gt=0)
    model: WorkingModel
    sha256: str
    author: Text
    note: Text
    origin: Literal["human", "model"]
    created_at: str


class ModelAcceptance(BaseModel):
    """Record the reviewer's acceptance of a specific model revision."""

    model_config = ConfigDict(extra="forbid", strict=True)
    revision: int = Field(gt=0)
    sha256: str
    image_sha256: str
    docling_sha256: str
    docling_run_sha256: str
    reviewer: Text
    accepted_at: str


class ModelReviewSession(BaseModel):
    """Preserve revision history and acceptance separately from model proposals."""

    model_config = ConfigDict(extra="forbid", strict=True)
    version: Literal["0.1.0"]
    source_image: str
    source_docling: str
    image_sha256: str
    docling_sha256: str
    docling_run_sha256: str
    revisions: list[ModelRevision]
    acceptances: list[ModelAcceptance]
    accepted_revision: int | None

    @model_validator(mode="after")
    def check_history(self) -> "ModelReviewSession":
        """Reject edited revision content and inconsistent acceptance pointers."""
        for number, revision in enumerate(self.revisions, start=1):
            if revision.number != number or revision.sha256 != model_digest(
                revision.model
            ):
                raise ValueError("Revision numbering or content hash changed")
        for acceptance in self.acceptances:
            if (
                acceptance.revision > len(self.revisions)
                or self.revisions[acceptance.revision - 1].sha256 != acceptance.sha256
            ):
                raise ValueError(
                    "Acceptance does not match a saved data model revision"
                )
            if any(
                getattr(acceptance, key) != getattr(self, key)
                for key in ("image_sha256", "docling_sha256", "docling_run_sha256")
            ):
                raise ValueError("Acceptance source identity changed")
        if self.accepted_revision is not None and (
            self.accepted_revision != len(self.revisions)
            or not any(a.revision == self.accepted_revision for a in self.acceptances)
        ):
            raise ValueError("Current acceptance must match the current draft revision")
        return self


def _persist(directory: Path, session: ModelReviewSession) -> None:
    checked = ModelReviewSession.model_validate_json(session.model_dump_json())
    temporary = directory / "session.tmp.json"
    with temporary.open("w", encoding="utf-8") as file:
        file.write(checked.model_dump_json(indent=2) + "\n")
        file.flush()
        os.fsync(file.fileno())
    temporary.replace(directory / "session.json")


def load_session(directory: Path) -> ModelReviewSession:
    """Load validated review history and check the saved input snapshots.

    Parameters
    ----------
    directory : Path
        Existing model-review session.

    Returns
    -------
    ModelReviewSession
        Current draft/history and explicit acceptance pointer.

    Raises
    ------
    ValueError
        If source snapshots or revision/acceptance hashes no longer match.
    """
    session = ModelReviewSession.model_validate_json(
        (directory / "session.json").read_text()
    )
    for filename, digest in (
        ("input.png", session.image_sha256),
        ("native.json", session.docling_sha256),
        ("run.json", session.docling_run_sha256),
    ):
        if hashlib.sha256((directory / filename).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Saved source changed: {filename}")
    return session


def create_session(
    image_path: Path, native_path: Path, directory: Path
) -> ModelReviewSession:
    """Create a fresh session with local PNG and matched Docling snapshots.

    Parameters
    ----------
    image_path, native_path : Path
        Source PNG and native Docling JSON with its sibling run report.
    directory : Path
        Fresh output directory; never overwritten.

    Returns
    -------
    ModelReviewSession
        Empty review session ready for a proposal or a human draft.

    Raises
    ------
    FileExistsError
        If the session directory exists.
    ValueError
        If source evidence does not match the PNG or conversion was unsuccessful.
    """
    _, hashes = read_docling_evidence(image_path, native_path)
    session = ModelReviewSession(
        version="0.1.0",
        source_image=str(image_path.resolve()),
        source_docling=str(native_path.resolve()),
        **hashes,
        revisions=[],
        acceptances=[],
        accepted_revision=None,
    )
    directory.mkdir(parents=True, exist_ok=False)
    for target, source in (
        ("input.png", image_path),
        ("native.json", native_path),
        ("run.json", native_path.with_name("run.json")),
    ):
        (directory / target).write_bytes(source.read_bytes())
    _persist(directory, session)
    return load_session(directory)


def _check_revision(session: ModelReviewSession, expected_revision: int) -> None:
    if expected_revision != len(session.revisions):
        raise ValueError("Draft changed; reload before saving or accepting")


def _append_draft(
    directory: Path,
    session: ModelReviewSession,
    model: WorkingModel,
    author: str,
    note: str,
    origin: Literal["human", "model"],
) -> ModelReviewSession:
    model = WorkingModel.model_validate_json(model.model_dump_json())
    digest = model_digest(model)
    if session.revisions and session.revisions[-1].sha256 == digest:
        return session
    session.revisions.append(
        ModelRevision(
            number=len(session.revisions) + 1,
            model=model,
            sha256=digest,
            author=author,
            note=note,
            origin=origin,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )
    session.accepted_revision = None
    _persist(directory, session)
    return session


def save_draft(
    directory: Path, model: WorkingModel, expected_revision: int, author: str, note: str
) -> ModelReviewSession:
    """Save direct edits as a new draft and clear current acceptance on change.

    Parameters
    ----------
    directory : Path
        Review session directory.
    model : WorkingModel
        Edited model; revalidated at the persistence boundary.
    expected_revision : int
        Revision the editor loaded, or zero for an empty session.
    author, note : str
        Reviewer identity and reason for the change.

    Returns
    -------
    ModelReviewSession
        Updated session; unchanged models do not create redundant revisions.

    Raises
    ------
    ValueError
        If the editor's revision is stale or saved source identities changed.
    """
    with (directory / ".session.lock").open("a") as file:
        fcntl.flock(file, fcntl.LOCK_EX)
        session = load_session(directory)
        _check_revision(session, expected_revision)
        return _append_draft(directory, session, model, author, note, "human")


def apply_proposal(
    directory: Path, proposal_dir: Path, expected_revision: int, author: str
) -> ModelReviewSession:
    """Apply a matching proposal as a draft, without accepting it.

    Parameters
    ----------
    directory : Path
        Review session directory.
    proposal_dir : Path
        Successful model-proposal output with original raw response and report.
    expected_revision : int
        Current revision expected by the caller.
    author : str
        Person applying the proposed revision.

    Returns
    -------
    ModelReviewSession
        Updated draft/history; stale proposals and wrong-image evidence are rejected.

    Raises
    ------
    ValueError
        If the proposal, source evidence or expected draft revision does not match.
    """
    with (directory / ".session.lock").open("a") as file:
        fcntl.flock(file, fcntl.LOCK_EX)
        session = load_session(directory)
        _check_revision(session, expected_revision)
        report = json.loads((proposal_dir / "run.json").read_text())
        current_hash = session.revisions[-1].sha256 if session.revisions else None
        if (
            report.get("status") != "proposed"
            or report.get("current_model_sha256") != current_hash
        ):
            raise ValueError("Proposal failed or was based on a different draft")
        for key in ("image_sha256", "docling_sha256", "docling_run_sha256"):
            if report.get(key) != getattr(session, key):
                raise ValueError("Proposal source evidence differs from this session")
        model = WorkingModel.model_validate_json(
            (proposal_dir / "proposed_model.json").read_text()
        )
        raw = WorkingModel.model_validate_json(
            (proposal_dir / "raw_output.txt").read_text()
        )
        if model_digest(model) != model_digest(raw):
            raise ValueError(
                "Proposal differs from raw output; save direct edits separately"
            )
        return _append_draft(
            directory,
            session,
            model,
            author,
            f"Applied proposal from {proposal_dir.resolve()}",
            "model",
        )


def accept_model(
    directory: Path, expected_revision: int, reviewer: str
) -> ModelReviewSession:
    """Record explicit local acceptance, allowing clearly represented unknowns.

    Parameters
    ----------
    directory : Path
        Review session directory.
    expected_revision : int
        Exact current draft revision to accept.
    reviewer : str
        Reviewer identity; this local MVP does not authenticate reviewers.

    Returns
    -------
    ModelReviewSession
        Session with acceptance pinned to the current model/source identities.

    Raises
    ------
    ValueError
        If no draft exists, the revision is stale or the source identity changed.
    """
    with (directory / ".session.lock").open("a") as file:
        fcntl.flock(file, fcntl.LOCK_EX)
        session = load_session(directory)
        _check_revision(session, expected_revision)
        if not session.revisions:
            raise ValueError("No data model draft to accept")
        if session.accepted_revision == expected_revision:
            return session
        session.acceptances.append(
            ModelAcceptance(
                revision=expected_revision,
                sha256=session.revisions[-1].sha256,
                image_sha256=session.image_sha256,
                docling_sha256=session.docling_sha256,
                docling_run_sha256=session.docling_run_sha256,
                reviewer=reviewer,
                accepted_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        session.accepted_revision = expected_revision
        _persist(directory, session)
        return session


def main() -> None:
    """Initialize, edit, apply, accept or inspect local model-review state."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    for action in ("init", "save", "apply", "accept", "show"):
        command = subparsers.add_parser(action)
        command.add_argument("--session-dir", type=Path, required=True)
        if action == "init":
            command.add_argument("image", type=Path)
            command.add_argument("--docling", type=Path, required=True)
        if action in {"save", "apply", "accept"}:
            command.add_argument("--expected-revision", type=int, required=True)
            command.add_argument("--reviewer", required=True)
        if action == "save":
            command.add_argument("--model", type=Path, required=True)
            command.add_argument("--note", required=True)
        if action == "apply":
            command.add_argument("--proposal-dir", type=Path, required=True)
        if action == "show":
            command.add_argument("--model-output", type=Path)
    args = parser.parse_args()
    if args.action == "init":
        session = create_session(args.image, args.docling, args.session_dir)
    elif args.action == "save":
        model = WorkingModel.model_validate_json(args.model.read_text())
        session = save_draft(
            args.session_dir, model, args.expected_revision, args.reviewer, args.note
        )
    elif args.action == "apply":
        session = apply_proposal(
            args.session_dir, args.proposal_dir, args.expected_revision, args.reviewer
        )
    elif args.action == "accept":
        session = accept_model(args.session_dir, args.expected_revision, args.reviewer)
    else:
        session = load_session(args.session_dir)
        if args.model_output:
            if not session.revisions:
                raise ValueError("No draft to export")
            with args.model_output.open("x", encoding="utf-8") as file:
                file.write(session.revisions[-1].model.model_dump_json(indent=2) + "\n")
    print(
        json.dumps(
            {
                "draft_revision": len(session.revisions),
                "accepted_revision": session.accepted_revision,
                "acceptance_records": len(session.acceptances),
                "session_dir": str(args.session_dir.resolve()),
            }
        )
    )


if __name__ == "__main__":
    main()
