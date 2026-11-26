"""Store editable document names independently of model revisions and approvals."""

import fcntl
import os
import unicodedata
from pathlib import Path

from data_snapshot.structured_data_extraction.model_review import load_session


def sanitize_name(value: str) -> str:
    """Make a readable, filename-safe name while preserving Unicode letters.

    Parameters
    ----------
    value : str
        Snapshot title or reviewer-supplied name.

    Returns
    -------
    str
        Single-line name without path separators, with an untitled fallback.
    """
    value = unicodedata.normalize("NFC", value)
    clean = "".join(c if c.isalnum() or c in " -_.()" else " " for c in value)
    clean = " ".join(clean.split()).strip(" .")
    clean = clean.encode("utf-8")[:180].decode("utf-8", errors="ignore").rstrip(" .")
    if clean.partition(".")[0].upper() in {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *[f"COM{i}" for i in range(1, 10)],
        *[f"LPT{i}" for i in range(1, 10)],
    }:
        clean = "_" + clean
    return clean or "Untitled snapshot"


def session_name(directory: Path) -> str:
    """Read a custom name, falling back to the first proposed snapshot title.

    Parameters
    ----------
    directory : Path
        Existing review session.

    Returns
    -------
    str
        Custom or generated display name; older sessions need no migration.
    """
    path = directory / "session_name.txt"
    if path.exists():
        return sanitize_name(path.read_text(encoding="utf-8"))
    session = load_session(directory)
    return (
        sanitize_name(session.revisions[0].model.title)
        if session.revisions
        else "Untitled snapshot"
    )


def save_session_name(directory: Path, value: str) -> str:
    """Atomically save a display name without changing statistical review state.

    Parameters
    ----------
    directory : Path
        Existing review session.
    value : str
        New name, sanitized before persistence.

    Returns
    -------
    str
        Persisted name.
    """
    name = sanitize_name(value)
    with (directory / ".name.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        load_session(directory)
        temporary = directory / "session_name.tmp"
        with temporary.open("w", encoding="utf-8") as file:
            file.write(name + "\n")
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(directory / "session_name.txt")
    return name
