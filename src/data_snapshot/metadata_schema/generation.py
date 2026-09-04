"""Generate JSON Schema and Markdown reference artifacts from v1.2 models."""

from __future__ import annotations

import argparse
import json
from functools import cache
from pathlib import Path
from typing import Any

from data_snapshot.metadata_schema.models import DataSnapshotMetadata


_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_JSON_PATH = (
    _ROOT / "docs/schema_v1.2/data_snapshot_metadata_schema_v1.2.schema.json"
)
_DEFAULT_MARKDOWN_PATH = _ROOT / "docs/schema_v1.2/schema_reference_v1.2.md"


@cache
def _metadata_schema() -> dict[str, Any]:
    return DataSnapshotMetadata.model_json_schema(mode="validation")


@cache
def serialize_metadata_schema() -> str:
    """Serialize the canonical metadata schema once per process.

    Returns
    -------
    str
        Compact JSON suitable for repeated use as model input context.
    """
    return json.dumps(_metadata_schema(), ensure_ascii=False, separators=(",", ":"))


def render_json_schema() -> str:
    """Render the canonical model's JSON Schema deterministically.

    Returns
    -------
    str
        Pretty-printed JSON Schema with one trailing newline.
    """
    schema = _metadata_schema()
    return json.dumps(schema, ensure_ascii=False, indent=2) + "\n"


def render_markdown_reference() -> str:
    """Render a human-readable schema reference from generated JSON Schema.

    Returns
    -------
    str
        Markdown reference with one trailing newline.
    """
    schema = _metadata_schema()
    lines = [
        "# Data Snapshot Metadata Schema v1.2 Reference",
        "",
        "<!-- Generated from DataSnapshotMetadata. Do not edit manually. -->",
        "",
        _summary(
            schema.get("description", "Canonical metadata for one data snapshot.")
        ),
        "",
        f"Schema version: `{schema['x-schema-version']}`",
        "",
        "## Snapshot fields",
        "",
    ]
    lines.extend(_object_table(schema))
    for name, definition in schema.get("$defs", {}).items():
        lines.extend(["", f"## {name}", ""])
        description = definition.get("description")
        if description:
            lines.extend([_summary(description), ""])
        if "enum" in definition:
            lines.append(", ".join(f"`{value}`" for value in definition["enum"]))
        elif definition.get("type") == "object":
            lines.extend(_object_table(definition))
        else:
            lines.append(f"Type: `{_type_label(definition)}`")
    return "\n".join(lines).rstrip() + "\n"


def write_schema_artifacts(
    json_path: str | Path = _DEFAULT_JSON_PATH,
    markdown_path: str | Path = _DEFAULT_MARKDOWN_PATH,
) -> None:
    """Write both schema artifacts derived from the canonical model.

    Parameters
    ----------
    json_path : str | Path, optional
        Destination for the generated JSON Schema.
    markdown_path : str | Path, optional
        Destination for the generated Markdown reference.
    """
    json_output = Path(json_path)
    markdown_output = Path(markdown_path)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(render_json_schema(), encoding="utf-8")
    markdown_output.write_text(render_markdown_reference(), encoding="utf-8")


def _object_table(schema: dict[str, Any]) -> list[str]:
    required = set(schema.get("required", []))
    lines = [
        "| Field | Type | Required | Default | Description | Standards |",
        "|---|---|---:|---|---|---|",
    ]
    for name, field_schema in schema.get("properties", {}).items():
        standards = ", ".join(
            f"[{mapping['term']}]({mapping['term']}) ({mapping['relationship']})"
            for mapping in field_schema.get("x-standards", [])
        )
        default = (
            f"`{json.dumps(field_schema['default'], ensure_ascii=False)}`"
            if "default" in field_schema
            else "—"
        )
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{name}`",
                    _cell(f"`{_type_label(field_schema)}`"),
                    "yes" if name in required else "no",
                    default,
                    _cell(field_schema.get("description", "")),
                    standards,
                )
            )
            + " |"
        )
    return lines


def _type_label(schema: dict[str, Any]) -> str:
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if "enum" in schema:
        return "enum"
    if "anyOf" in schema:
        labels = [
            _type_label(option)
            for option in schema["anyOf"]
            if option.get("type") != "null"
        ]
        return " | ".join(labels) + " | null"
    if schema.get("type") == "array":
        return f"array[{_type_label(schema.get('items', {}))}]"
    return schema.get("format", schema.get("type", "unknown"))


def _cell(value: str) -> str:
    return " ".join(value.split()).replace("|", "\\|")


def _summary(value: str) -> str:
    return value.strip().split("\n\n", 1)[0]


def main() -> None:
    """Generate artifacts or verify that checked-in artifacts are current."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when generated artifacts differ from checked-in files.",
    )
    args = parser.parse_args()
    if args.check:
        expected = {
            _DEFAULT_JSON_PATH: render_json_schema(),
            _DEFAULT_MARKDOWN_PATH: render_markdown_reference(),
        }
        stale = [
            str(path.relative_to(_ROOT))
            for path, content in expected.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        if stale:
            parser.error(f"stale generated artifacts: {', '.join(stale)}")
        return
    write_schema_artifacts()


if __name__ == "__main__":
    main()
