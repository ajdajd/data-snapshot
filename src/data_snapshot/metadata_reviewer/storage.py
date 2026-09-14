"""Discover, load, compare, validate, and save metadata review records."""

from __future__ import annotations

import json
import os
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from data_snapshot.metadata_schema import DataSnapshotMetadata


_SOURCES = {"prwp", "refugee", "unhcr"}
_ARTIFACT_TYPES = {"figure", "table"}
_GENERATED_SUFFIX = "_metadata"


@dataclass(frozen=True)
class ReviewItem:
    """Describe the files associated with one reviewable snapshot.

    Parameters
    ----------
    snapshot_id : str
        Globally unique snapshot filename stem.
    snapshot_path : pathlib.Path
        Path to the immutable snapshot image.
    generated_path : pathlib.Path
        Path to the immutable generated metadata JSON.
    gold_path : pathlib.Path
        Existing or intended path for the reviewed gold metadata JSON.
    """

    snapshot_id: str
    snapshot_path: Path
    generated_path: Path
    gold_path: Path

    @property
    def reviewed(self) -> bool:
        """Return whether a gold file exists for the snapshot.

        Returns
        -------
        bool
            ``True`` when the gold path is an existing file.
        """

        return self.gold_path.is_file()


@dataclass(frozen=True)
class DiscoveryResult:
    """Contain reviewable items and nonfatal discovery warnings.

    Parameters
    ----------
    items : tuple[ReviewItem, ...]
        Reviewable snapshot/generated pairs in deterministic ID order.
    warnings : tuple[str, ...]
        Nonfatal problems found while indexing the roots.
    """

    items: tuple[ReviewItem, ...]
    warnings: tuple[str, ...]


def discover_review_items(
    snapshot_root: str | Path,
    generated_root: str | Path,
    gold_root: str | Path,
) -> DiscoveryResult:
    """Discover reviewable files by globally unique snapshot stem.

    Generated JSON filenames may use the exporter's ``_metadata.json`` suffix.
    New gold paths mirror the snapshot's relative source/type layout. Files
    without a snapshot/generated counterpart are excluded with a warning.

    Parameters
    ----------
    snapshot_root : str | pathlib.Path
        Root recursively searched for PNG snapshots.
    generated_root : str | pathlib.Path
        Root recursively searched for generated JSON metadata.
    gold_root : str | pathlib.Path
        Root recursively searched for existing gold JSON metadata and used for
        new gold files.

    Returns
    -------
    DiscoveryResult
        Matched review items and nonfatal warnings.

    Raises
    ------
    FileNotFoundError
        If the snapshot or generated root does not exist.
    NotADirectoryError
        If a supplied root exists but is not a directory.
    ValueError
        If generated and gold roots overlap or a root contains duplicate IDs.
    """

    snapshots = Path(snapshot_root)
    generated = Path(generated_root)
    gold = Path(gold_root)
    _require_directory(snapshots)
    _require_directory(generated)
    if gold.exists() and not gold.is_dir():
        raise NotADirectoryError(gold)
    _require_separate_roots(generated, gold)

    warnings: list[str] = []
    snapshot_paths: dict[str, Path] = {}
    for path in _files_with_suffix(snapshots, ".png"):
        relative = path.relative_to(snapshots)
        if len(relative.parts) < 3 or relative.parts[0] not in _SOURCES:
            warnings.append(f"Excluded snapshot outside a supported source: {path}")
            continue
        if relative.parts[1] not in _ARTIFACT_TYPES:
            warnings.append(f"Excluded snapshot outside a supported type: {path}")
            continue
        _add_unique(snapshot_paths, path.stem, path, "snapshot")

    generated_paths = _index_json(generated, "generated")
    gold_paths = _index_json(gold, "gold") if gold.is_dir() else {}

    items: list[ReviewItem] = []
    for snapshot_id in sorted(snapshot_paths.keys() & generated_paths.keys()):
        snapshot_path = snapshot_paths[snapshot_id]
        gold_path = gold_paths.get(
            snapshot_id,
            gold / snapshot_path.relative_to(snapshots).with_suffix(".json"),
        )
        items.append(
            ReviewItem(
                snapshot_id=snapshot_id,
                snapshot_path=snapshot_path,
                generated_path=generated_paths[snapshot_id],
                gold_path=gold_path,
            )
        )

    for snapshot_id in sorted(snapshot_paths.keys() - generated_paths.keys()):
        warnings.append(
            f"Excluded snapshot without generated metadata: {snapshot_paths[snapshot_id]}"
        )
    for snapshot_id in sorted(generated_paths.keys() - snapshot_paths.keys()):
        warnings.append(
            f"Excluded generated metadata without snapshot: {generated_paths[snapshot_id]}"
        )
    for snapshot_id in sorted(gold_paths.keys() - snapshot_paths.keys()):
        warnings.append(
            f"Orphan gold metadata without snapshot: {gold_paths[snapshot_id]}"
        )

    return DiscoveryResult(items=tuple(items), warnings=tuple(warnings))


def load_review_records(
    item: ReviewItem,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load immutable generated metadata and the editable working record.

    Parameters
    ----------
    item : ReviewItem
        Review item whose JSON records should be loaded.

    Returns
    -------
    tuple[dict[str, Any], dict[str, Any]]
        Generated metadata followed by an independent working copy. The working
        copy comes from gold when it exists, otherwise from generated metadata.

    Raises
    ------
    ValueError
        If either loaded JSON value is not an object.
    json.JSONDecodeError
        If either file contains invalid JSON.
    """

    generated = _load_json_object(item.generated_path)
    working_path = item.gold_path if item.reviewed else item.generated_path
    working = _load_json_object(working_path)
    return generated, deepcopy(working)


def metadata_values_equal(left: Any, right: Any) -> bool:
    """Compare metadata values while treating missing and null as equivalent.

    Parameters
    ----------
    left : Any
        First JSON-compatible value.
    right : Any
        Second JSON-compatible value.

    Returns
    -------
    bool
        Whether the values are equal after omitting null-valued object fields.
    """

    return _without_null_fields(left) == _without_null_fields(right)


def validate_metadata(record: dict[str, Any]) -> DataSnapshotMetadata:
    """Validate a working record with the canonical Pydantic model.

    Parameters
    ----------
    record : dict[str, Any]
        Editable metadata record.

    Returns
    -------
    DataSnapshotMetadata
        Validated canonical model instance.

    Raises
    ------
    pydantic.ValidationError
        If the record violates the canonical metadata schema.
    """

    return DataSnapshotMetadata.model_validate(record)


def save_gold(item: ReviewItem, record: dict[str, Any]) -> DataSnapshotMetadata:
    """Validate and atomically save one canonical gold metadata record.

    Parameters
    ----------
    item : ReviewItem
        Review item defining the immutable generated and writable gold paths.
    record : dict[str, Any]
        Edited metadata record to validate and save.

    Returns
    -------
    DataSnapshotMetadata
        Validated model whose canonical JSON representation was saved.

    Raises
    ------
    ValueError
        If the gold and generated paths resolve to the same location.
    pydantic.ValidationError
        If the record violates the canonical metadata schema.
    OSError
        If the atomic write cannot be completed.
    """

    if item.gold_path.resolve() == item.generated_path.resolve():
        raise ValueError("Gold metadata path cannot overwrite generated metadata.")
    metadata = validate_metadata(record)
    serialized = (
        json.dumps(
            metadata.model_dump(mode="json", exclude_none=True),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    _atomic_write_text(item.gold_path, serialized)
    return metadata


def _require_directory(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_dir():
        raise NotADirectoryError(path)


def _require_separate_roots(generated: Path, gold: Path) -> None:
    generated_resolved = generated.resolve()
    gold_resolved = gold.resolve()
    if generated_resolved.is_relative_to(gold_resolved) or gold_resolved.is_relative_to(
        generated_resolved
    ):
        raise ValueError("Generated and gold roots must not overlap.")


def _files_with_suffix(root: Path, suffix: str) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() == suffix
    )


def _index_json(root: Path, kind: str) -> dict[str, Path]:
    indexed: dict[str, Path] = {}
    for path in _files_with_suffix(root, ".json"):
        snapshot_id = path.stem.removesuffix(_GENERATED_SUFFIX)
        _add_unique(indexed, snapshot_id, path, kind)
    return indexed


def _add_unique(index: dict[str, Path], key: str, path: Path, kind: str) -> None:
    existing = index.get(key)
    if existing is not None:
        raise ValueError(f"Duplicate {kind} ID {key!r}: {existing} and {path}")
    index[key] = path


def _load_json_object(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, dict):
        raise ValueError(f"Metadata JSON must contain an object: {path}")
    return value


def _without_null_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_null_fields(item)
            for key, item in value.items()
            if item is not None
        }
    if isinstance(value, list):
        return [_without_null_fields(item) for item in value]
    return value


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
