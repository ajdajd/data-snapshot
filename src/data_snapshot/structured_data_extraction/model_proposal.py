"""Prepare or execute snapshot-model proposals using PNG and matched Docling evidence."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .llm import (
    APISettings,
    _DEFAULT_CONFIG,
    _PACKAGE,
    _prepare_image_request,
    _run_prepared_request,
    _write_json,
)
from .working_model import WorkingModel, model_digest


def read_docling_evidence(
    image_path: Path, native_path: Path
) -> tuple[dict[str, Any], dict[str, str]]:
    """Load matched native evidence without document names or embedded page images.

    Parameters
    ----------
    image_path : Path
        PNG used to create the Docling artifact.
    native_path : Path
        Docling JSON with a sibling run.json from the local extraction CLI.

    Returns
    -------
    tuple of dict, dict
        Projected document content and hashes of the image/native/report inputs.

    Raises
    ------
    ValueError
        If the PNG/native format, source match or conversion status is invalid.
    """
    import fitz

    image_bytes = image_path.read_bytes()
    if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Only PNG snapshot input is supported")
    with fitz.open(stream=image_bytes, filetype="png") as document:
        document[0].get_pixmap()
    native_bytes = native_path.read_bytes()
    report_bytes = native_path.with_name("run.json").read_bytes()
    native = json.loads(native_bytes)
    report = json.loads(report_bytes)
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    if report.get("image_sha256") != image_hash:
        raise ValueError("Docling evidence belongs to a different image")
    if report.get("status") not in {"success", "extracted_only"}:
        raise ValueError("Docling conversion did not finish successfully")
    if native.get("schema_name") != "DoclingDocument":
        raise ValueError("Expected native DoclingDocument JSON")

    def strip_assets(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: strip_assets(item)
                for key, item in value.items()
                if key not in {"image", "uri"}
            }
        if isinstance(value, list):
            return [strip_assets(item) for item in value]
        return value

    evidence = {
        key: strip_assets(native[key])
        for key in (
            "furniture",
            "body",
            "groups",
            "texts",
            "tables",
            "pictures",
            "key_value_items",
            "form_items",
            "pages",
        )
        if key in native
    }
    if not any(native.get(key) for key in ("texts", "tables", "pictures")):
        raise ValueError("No Docling text, table or picture evidence is available")
    json.dumps(evidence, allow_nan=False)
    return evidence, {
        "image_sha256": image_hash,
        "docling_sha256": hashlib.sha256(native_bytes).hexdigest(),
        "docling_run_sha256": hashlib.sha256(report_bytes).hexdigest(),
    }


def prepare_model_request(
    image_path: Path,
    native_path: Path,
    config: APISettings,
    current_model: WorkingModel | None = None,
    instruction: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    """Prepare a proposal or revision without loading a key or contacting a provider.

    Parameters
    ----------
    image_path, native_path : Path
        PNG and matched native Docling JSON.
    config : APISettings
        Validated OpenRouter settings.
    current_model : WorkingModel, optional
        Current editable draft for a revision, without session/acceptance metadata.
    instruction : str, optional
        Explicit reviewer instruction; required for a revision.

    Returns
    -------
    tuple of dict, dict, dict
        SDK request, projected evidence and source fingerprints.

    Raises
    ------
    ValueError
        If sources, revision instructions or prompt placeholders are invalid.
    """
    if instruction is not None and not instruction.strip():
        raise ValueError("Reviewer instruction must not be blank")
    if current_model is not None and instruction is None:
        raise ValueError("A model revision requires a reviewer instruction")
    if current_model is not None:
        current_model = WorkingModel.model_validate_json(
            current_model.model_dump_json()
        )
    evidence, hashes = read_docling_evidence(image_path, native_path)
    system = (_PACKAGE / "prompts/model_proposal_system.md").read_text()
    user = (_PACKAGE / "prompts/model_proposal_user.md").read_text()
    values = {
        "DOCLING": evidence,
        "CURRENT_MODEL": (
            current_model.model_dump(mode="json") if current_model is not None else None
        ),
        "INSTRUCTION": instruction,
    }
    for name in values:
        if user.count("{{" + name + "}}") != 1:
            raise ValueError(f"Expected one {name} prompt placeholder")
    # Replace in one pass: source text cannot introduce a new template placeholder.
    import re

    user = re.sub(
        r"\{\{(DOCLING|CURRENT_MODEL|INSTRUCTION)\}\}",
        lambda match: json.dumps(values[match[1]], ensure_ascii=False, allow_nan=False),
        user,
    )
    request = _prepare_image_request(
        image_path,
        config,
        system,
        user,
        WorkingModel.model_json_schema(),
        "snapshot_working_model",
    )
    return request, evidence, hashes


def run_model_proposal(
    image_path: Path,
    native_path: Path,
    output_dir: Path,
    config_path: Path = _DEFAULT_CONFIG,
    current_model: WorkingModel | None = None,
    instruction: str | None = None,
    execute: bool = False,
    client: Any | None = None,
    ledger_path: Path | None = None,
    batch_id: str | None = None,
) -> dict[str, Any]:
    """Preserve one proposal attempt under the existing shared spending guardrail.

    Parameters
    ----------
    image_path, native_path, output_dir : Path
        PNG, matched Docling evidence, and fresh proposal directory.
    config_path : Path, optional
        Independent model/settings file.
    current_model : WorkingModel, optional
        Draft to revise; omitted for a first proposal.
    instruction : str, optional
        Reviewer instruction, required for revisions.
    execute : bool, optional
        Permit one API attempt; false prepares offline.
    client : Any, optional
        Injectable Responses client for offline tests.
    ledger_path : Path, optional
        Shared workstream journal; the existing $5 cap still applies.
    batch_id : str, optional
        Group costs across related calls.

    Returns
    -------
    dict
        Preparation or validation report with fingerprints, usage and costs.
        A proposed model is never automatically accepted or applied to a session.

    Raises
    ------
    FileExistsError
        If the proposal directory already exists.
    ValueError
        If sources, settings or revision preparation fail before execution.
    """
    if output_dir.exists():
        raise FileExistsError(output_dir)
    config = APISettings.model_validate_json(config_path.read_text())
    request, evidence, hashes = prepare_model_request(
        image_path, native_path, config, current_model, instruction
    )

    def process_output(text: str) -> dict[str, Any]:
        result = WorkingModel.model_validate_json(text)
        if current_model is None and instruction is None:
            if any(c.extraction_policy != "printed_only" for c in result.components):
                raise ValueError(
                    "Initial proposals must use printed-only policy without reviewer instructions"
                )
            evidence = [e for c in result.components for e in c.evidence] + [
                e
                for item in [*result.contexts, *result.relationships, *result.questions]
                for e in item.evidence
            ]
            if any(e.basis == "user" for e in evidence):
                raise ValueError(
                    "Initial proposal cannot invent user-provided evidence"
                )
        _write_json(output_dir / "proposed_model.json", result.model_dump(mode="json"))
        return {
            "status": "proposed",
            "components": len(result.components),
            "unresolved_questions": sum(
                q.resolution == "unresolved" for q in result.questions
            ),
        }

    return _run_prepared_request(
        image_path,
        output_dir,
        config,
        request,
        process_output,
        {
            "docling_evidence.json": evidence,
            "model.schema.json": WorkingModel.model_json_schema(),
            "revision_input.json": {
                "current_model": (
                    current_model.model_dump(mode="json") if current_model else None
                ),
                "instruction": instruction,
            },
        },
        {
            "task": "model_revision" if current_model else "model_proposal",
            **hashes,
            "current_model_sha256": (
                model_digest(current_model) if current_model else None
            ),
        },
        execute,
        client,
        ledger_path,
        batch_id,
    )


def main() -> None:
    """Prepare a proposal offline, or explicitly execute one proposal/revision."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--docling", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=_DEFAULT_CONFIG)
    parser.add_argument("--current-model", type=Path)
    parser.add_argument("--instruction")
    parser.add_argument("--batch-id")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    current = (
        WorkingModel.model_validate_json(args.current_model.read_text())
        if args.current_model
        else None
    )
    report = run_model_proposal(
        args.image,
        args.docling,
        args.output_dir,
        args.config,
        current,
        args.instruction,
        args.execute,
        batch_id=args.batch_id,
    )
    print(json.dumps(report, ensure_ascii=False))
    if report["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
