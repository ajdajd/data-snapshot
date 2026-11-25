"""Discover image-grounded representation requirements without supplying a DSD."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .llm import (
    APISettings,
    _DEFAULT_CONFIG,
    _PACKAGE,
    _prepare_image_request,
    _run_prepared_request,
    _write_json,
)


def prepare_discovery_request(image_path: Path, config: APISettings) -> dict[str, Any]:
    """Prepare one independent PNG discovery request without a client or DSD.

    Parameters
    ----------
    image_path : Path
        PNG evidence; its filename is excluded from model input.
    config : APISettings
        Independent OpenRouter model and execution settings.

    Returns
    -------
    dict
        Strict JSON request containing only prompts, recording schema and image.
    """
    schema = json.loads(
        (_PACKAGE / "schemas/discovery_record.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    return _prepare_image_request(
        image_path,
        config,
        (_PACKAGE / "prompts/discovery_system.md").read_text(encoding="utf-8"),
        (_PACKAGE / "prompts/discovery_user.md").read_text(encoding="utf-8"),
        schema,
        "data_snapshot_discovery",
    )


def validate_discovery(record: dict[str, Any], schema: dict[str, Any]) -> None:
    """Check recording shape and image-local identifier integrity.

    Parameters
    ----------
    record : dict
        Parsed discovery result.
    schema : dict
        Frozen recording schema used in this request.

    Raises
    ------
    jsonschema.ValidationError
        If the record violates its recording schema.
    ValueError
        If IDs repeat, references do not resolve or a relationship repeats an ID.
        These checks do not establish factual correctness against the image.
    """
    Draft202012Validator(schema).validate(record)
    units = record["analytical_units"]
    requirements = [r for unit in units for r in unit["requirements"]]
    ids = [item["id"] for item in [*units, *requirements]]
    if len(ids) != len(set(ids)):
        raise ValueError("Discovery IDs must be unique throughout the image")
    requirement_ids = {item["id"] for item in requirements}
    for unit in units:
        for example in unit["observation_examples"]:
            if not set(example["context_requirement_ids"]) <= requirement_ids:
                raise ValueError(
                    "Observation example references an unknown requirement"
                )
    for relationship in record["relationships"]:
        related = relationship["related_ids"]
        if len(related) != len(set(related)):
            raise ValueError("A relationship must connect distinct IDs")
        if not set(related) <= set(ids):
            raise ValueError("Relationship references an unknown unit or requirement")


def run_discovery(
    image_path: Path,
    output_dir: Path,
    config_path: Path = _DEFAULT_CONFIG,
    execute: bool = False,
    client: Any | None = None,
    ledger_path: Path | None = None,
    batch_id: str | None = None,
) -> dict[str, Any]:
    """Prepare offline or execute one discovery call under the shared $5 budget.

    Parameters
    ----------
    image_path, output_dir : Path
        One input PNG and a fresh output directory.
    config_path : Path, optional
        OpenRouter model/settings file, independent of any DSD.
    execute : bool, optional
        Allow one paid attempt; false by default.
    client : Any, optional
        Injectable Responses client for offline tests.
    ledger_path : Path, optional
        Shared workstream spending journal; never reset between batches.
    batch_id : str, optional
        Label for cumulative batch accounting.

    Returns
    -------
    dict
        Preparation or execution report, including billed cost when available.

    Raises
    ------
    FileExistsError
        If the output directory already exists, before any call.
    ValueError
        If the image, settings or request schema is invalid.
    """
    if output_dir.exists():
        raise FileExistsError(output_dir)
    config = APISettings.model_validate_json(config_path.read_text(encoding="utf-8"))
    request = prepare_discovery_request(image_path, config)
    schema = request["text"]["format"]["schema"]
    contract = {key: request[key] for key in ("input", "text")}

    def process_output(text: str) -> dict[str, Any]:
        record = json.loads(text)
        validate_discovery(record, schema)
        _write_json(output_dir / "discovery.json", record)
        return {
            "status": "discovered",
            "analytical_units": len(record["analytical_units"]),
            "requirements": sum(
                len(unit["requirements"]) for unit in record["analytical_units"]
            ),
            "ambiguities": len(record["ambiguities"]),
        }

    return _run_prepared_request(
        image_path,
        output_dir,
        config,
        request,
        process_output,
        {"discovery.schema.json": schema},
        {
            "task": "open_discovery",
            "contract_sha256": hashlib.sha256(
                json.dumps(contract, sort_keys=True).encode()
            ).hexdigest(),
        },
        execute,
        client,
        ledger_path,
        batch_id,
    )


def main() -> None:
    """Prepare one independent discovery request or explicitly execute it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=_DEFAULT_CONFIG)
    parser.add_argument("--batch-id")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    report = run_discovery(
        args.image, args.output_dir, args.config, args.execute, batch_id=args.batch_id
    )
    print(json.dumps(report, ensure_ascii=False))
    if report["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
