"""Build OpenAI Structured Outputs schemas from metadata field maps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_openai_schema(
    metadata_schema_path: str | Path, output_schema_path: str | Path
) -> dict[str, Any]:
    """Build and save an OpenAI Structured Outputs schema.

    Run this function before :func:`data_snapshot.metadata_extraction.extract_metadata`
    when starting with the canonical Data Snapshot Metadata Schema field map.
    ``extract_metadata`` accepts only the generated OpenAI schema file, allowing
    batch processing to reuse a previously validated schema.

    Parameters
    ----------
    metadata_schema_path : str | Path
        Path to the canonical metadata field-map JSON file.
    output_schema_path : str | Path
        Destination path for the generated OpenAI Structured Outputs schema JSON.

    Returns
    -------
    dict[str, Any]
        The generated OpenAI response-format configuration.

    Raises
    ------
    ValueError
        If the metadata field map has an unsupported or invalid field definition.
    """
    with Path(metadata_schema_path).open(encoding="utf-8") as file:
        field_map = json.load(file)

    properties: dict[str, Any] = {}
    required: list[str] = []
    for field_name, field_definition in field_map.items():
        if field_name.startswith("$"):
            continue
        if not isinstance(field_definition, dict):
            raise ValueError(f"Schema field {field_name!r} must be an object.")

        multiple = field_definition.get("multiple")
        field_type = field_definition.get("type")
        description = field_definition.get("definition")
        if not isinstance(multiple, bool) or not isinstance(description, str):
            raise ValueError(
                f"Schema field {field_name!r} requires boolean 'multiple' "
                "and string 'definition' values."
            )

        if multiple and field_type == "array[string]":
            properties[field_name] = {
                "type": ["array", "null"],
                "items": {"type": "string"},
                "description": description,
            }
        elif not multiple and field_type == "string":
            properties[field_name] = {
                "type": ["string", "null"],
                "description": description,
            }
        else:
            raise ValueError(
                f"Unsupported definition for {field_name!r}: "
                f"type={field_type!r}, multiple={multiple!r}."
            )
        required.append(field_name)

    if not properties:
        raise ValueError("Metadata schema does not define any fields.")

    version = str(field_map.get("$schema_version", "unknown")).replace(".", "_")
    openai_schema = {
        "type": "json_schema",
        "name": f"data_snapshot_metadata_v{version}",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": properties,
            "required": required,
        },
    }
    output_path = Path(output_schema_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(openai_schema, file, indent=2)
        file.write("\n")
    return openai_schema
