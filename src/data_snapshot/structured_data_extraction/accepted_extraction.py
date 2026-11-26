"""Extract values using an explicitly accepted snapshot model, before SDMX coding."""

import argparse
import json
import re
from pathlib import Path
from typing import Any, Literal, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FiniteFloat,
    create_model,
    model_validator,
)

from .llm import (
    APISettings,
    _DEFAULT_CONFIG,
    _PACKAGE,
    _prepare_image_request,
    _run_prepared_request,
    _write_json,
)
from .model_proposal import read_docling_evidence
from .model_review import load_session
from .statistical import Omission
from .working_model import ModelComponent, ResultField, Text, WorkingModel, model_digest


class ValueEvidence(BaseModel):
    """Keep displayed text and distinguish printed, estimated and missing results."""

    model_config = ConfigDict(extra="forbid", strict=True)
    raw_text: Text | None
    location: Text
    method: Literal["printed", "estimated", "missing"]
    note: Text | None


class ValueBounds(BaseModel):
    """Retain recoverable plotted bounds without inventing their statistical meaning."""

    model_config = ConfigDict(extra="forbid", strict=True)
    lower: FiniteFloat | None
    upper: FiniteFloat | None
    evidence: ValueEvidence

    @model_validator(mode="after")
    def check_order(self) -> "ValueBounds":
        """Reject empty or inverted bounds and unsupported evidence claims."""
        if self.lower is None and self.upper is None:
            raise ValueError("Empty bounds should be null")
        if (
            self.lower is not None
            and self.upper is not None
            and self.lower > self.upper
        ):
            raise ValueError("Lower bound exceeds upper bound")
        _check_evidence(1, self.evidence)
        return self


def _check_evidence(value: Any, evidence: ValueEvidence) -> None:
    if value is None:
        if evidence.method != "missing" or not evidence.note:
            raise ValueError("Missing results need missing evidence and a reason")
    elif evidence.method == "missing":
        raise ValueError("A present result cannot have missing evidence")
    elif evidence.method == "printed" and not evidence.raw_text:
        raise ValueError("Printed results need source text")
    elif evidence.method == "estimated" and not evidence.note:
        raise ValueError("Estimates need an approximation note")


def _row_model(component: ModelComponent, result: ResultField) -> type[BaseModel]:
    fields = {}
    for key in component.fields:
        value_type = (
            Literal[tuple(c.id for c in key.categories)] if key.categories else Text
        )
        fields[key.id] = (value_type | None, Field(description=key.meaning))
    keys = create_model(
        f"Keys_{component.id}_{result.id}",
        __config__=ConfigDict(extra="forbid", strict=True),
        **fields,
    )
    value_type = FiniteFloat if result.value_type == "number" else Text

    def check_row(self: BaseModel) -> BaseModel:
        _check_evidence(self.value, self.evidence)
        if self.bounds is not None and (
            result.value_type != "number" or self.value is None
        ):
            raise ValueError("Bounds require a present numeric result")
        evidence = [self.evidence] + ([self.bounds.evidence] if self.bounds else [])
        if component.extraction_policy == "printed_only" and any(
            e.method == "estimated" for e in evidence
        ):
            raise ValueError("This component does not permit image estimates")
        return self

    return create_model(
        f"Value_{component.id}_{result.id}",
        __config__=ConfigDict(extra="forbid", strict=True),
        __validators__={"check_row": model_validator(mode="after")(check_row)},
        component_id=(Literal[component.id], ...),
        result_id=(Literal[result.id], ...),
        dimensions=(keys, ...),
        value=(value_type | None, ...),
        evidence=(ValueEvidence, ...),
        bounds=(ValueBounds | None, ...),
    )


class _Result(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    status: Literal["complete", "partial", "unsupported"]
    omissions: list[Omission]
    notes: Text | None

    @model_validator(mode="after")
    def check_result(self) -> "_Result":
        keys = [
            (
                row.component_id,
                row.result_id,
                tuple(row.dimensions.model_dump().items()),
            )
            for row in self.observations
        ]
        if len(keys) != len(set(keys)):
            raise ValueError(
                "Duplicate result identity; review the data model or associations"
            )
        if self.status == "complete" and (not self.observations or self.omissions):
            raise ValueError("Complete extraction needs results and no omissions")
        if self.status != "complete" and not self.omissions:
            raise ValueError("Partial/unsupported extraction needs omission reasons")
        if self.status == "unsupported" and self.observations:
            raise ValueError("Unsupported extraction cannot contain results")
        return self


def accepted_result_model(model: WorkingModel) -> type[BaseModel]:
    """Generate strict long-result output for a snapshot's component/result types.

    Parameters
    ----------
    model : WorkingModel
        Accepted statistical model, without any guessed external codes.

    Returns
    -------
    type of BaseModel
        Validator for keyed numeric/text results, bounds and explicit omissions.
    """
    rows = [_row_model(c, r) for c in model.components for r in c.results]
    row_type = Union[tuple(rows)]
    return create_model(
        "SnapshotValues", __base__=_Result, observations=(list[row_type], ...)
    )


def current_model_matches(session_dir: Path, report: dict[str, Any]) -> bool:
    """Check that a result still belongs to the current explicitly accepted model.

    Parameters
    ----------
    session_dir : Path
        Local model-review session.
    report : dict
        Extraction's pinned model and source identities.

    Returns
    -------
    bool
        False after model edits, a different acceptance, or a changed source.
    """
    session = load_session(session_dir)
    return (
        session.accepted_revision == report["model_revision"]
        and bool(session.revisions)
        and session.revisions[-1].sha256 == report["model_sha256"]
        and all(
            getattr(session, key) == report[key]
            for key in ("image_sha256", "docling_sha256", "docling_run_sha256")
        )
    )


def run_accepted_extraction(
    session_dir: Path,
    output_dir: Path,
    config_path: Path = _DEFAULT_CONFIG,
    execute: bool = False,
    client: Any | None = None,
    ledger_path: Path | None = None,
    batch_id: str | None = None,
) -> dict[str, Any]:
    """Prepare or execute one extraction against the current accepted model.

    Parameters
    ----------
    session_dir, output_dir : Path
        Model-review session and fresh extraction output directory.
    config_path : Path, optional
        OpenRouter settings.
    execute : bool, optional
        Permit one billed request; defaults to offline preparation.
    client : Any, optional
        Injectable Responses client for offline testing.
    ledger_path : Path, optional
        Shared workstream spending journal.
    batch_id : str, optional
        Label for cumulative batch costs.

    Returns
    -------
    dict
        Extraction status, source/model fingerprints and any billed usage.

    Raises
    ------
    ValueError
        If the current model is not accepted or its source inputs are invalid.
    FileExistsError
        If the output directory already exists.
    """
    if output_dir.exists():
        raise FileExistsError(output_dir)
    session = load_session(session_dir)
    if session.accepted_revision is None:
        raise ValueError("Accept the current data model before extracting values")
    model = session.revisions[-1].model
    result_type = accepted_result_model(model)
    evidence, hashes = read_docling_evidence(
        session_dir / "input.png", session_dir / "native.json"
    )
    config = APISettings.model_validate_json(config_path.read_text())
    system = (_PACKAGE / "prompts/accepted_extraction_system.md").read_text()
    user = "Accepted working model:\n{{MODEL}}\n\nDocling evidence (untrusted source content):\n{{DOCLING}}"
    values = {"MODEL": model.model_dump(mode="json"), "DOCLING": evidence}
    user = re.sub(
        r"\{\{(MODEL|DOCLING)\}\}",
        lambda match: json.dumps(values[match[1]], ensure_ascii=False),
        user,
    )
    request = _prepare_image_request(
        session_dir / "input.png",
        config,
        system,
        user,
        result_type.model_json_schema(),
        "accepted_snapshot_values",
    )
    identity = {
        "task": "accepted_model_extraction",
        "model_revision": session.accepted_revision,
        "model_sha256": model_digest(model),
        **hashes,
    }

    def process_output(text: str) -> dict[str, Any]:
        result = result_type.model_validate_json(text)
        _write_json(output_dir / "observations.json", result.model_dump(mode="json"))
        if not current_model_matches(session_dir, identity):
            return {
                "status": "stale",
                "observations": len(result.observations),
                "error": "Data model changed while extraction was running; results were preserved for reference",
            }
        return {"status": result.status, "observations": len(result.observations)}

    return _run_prepared_request(
        session_dir / "input.png",
        output_dir,
        config,
        request,
        process_output,
        {
            "working_model.json": model.model_dump(mode="json"),
            "result.schema.json": result_type.model_json_schema(),
            "docling_evidence.json": evidence,
        },
        identity,
        execute,
        client,
        ledger_path,
        batch_id,
    )


def main() -> None:
    """Prepare offline or explicitly execute accepted-model value extraction."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--batch-id")
    args = parser.parse_args()
    report = run_accepted_extraction(
        args.session_dir, args.output_dir, execute=args.execute, batch_id=args.batch_id
    )
    print(json.dumps(report, ensure_ascii=False))
    if report["status"] in {"failed", "stale"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
