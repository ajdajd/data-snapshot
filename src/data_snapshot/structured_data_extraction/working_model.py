"""Validate an editable snapshot-specific statistical model before SDMX encoding."""

import hashlib
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
Identifier = Annotated[str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_]*$")]


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ModelEvidence(_Record):
    """Locate source evidence or explicitly attributed user context."""

    basis: Literal["image", "docling", "user"]
    text: Text | None
    location: Text


class Category(_Record):
    """Keep a stable category identity and preserve its original source label."""

    id: Identifier
    source_label: Text
    display_label: Text | None


class IdentifyingField(_Record):
    """Describe a component-local key, optionally listing source categories."""

    id: Identifier
    name: Text
    meaning: Text
    source_label: Text | None
    categories: list[Category]


class ResultField(_Record):
    """Describe a numeric or categorical result without extracting its values."""

    id: Identifier
    name: Text
    meaning: Text
    source_label: Text | None
    value_type: Literal["number", "text"]


class ModelComponent(_Record):
    """Describe one coherent analytical component and its extraction policy."""

    id: Identifier
    name: Text
    one_result_means: Text
    fields: list[IdentifyingField]
    results: list[ResultField] = Field(min_length=1)
    extraction_policy: Literal["printed_only", "allow_estimates"]
    evidence: list[ModelEvidence] = Field(min_length=1)


class CategorySelection(_Record):
    """Select source categories within a component-local identifying field."""

    field_id: Identifier
    category_ids: list[Identifier] = Field(min_length=1)


class ModelScope(_Record):
    """Apply context to a component, selected results and optional category subsets.

    Empty result IDs mean all component results. Selections on different fields
    combine with AND; categories inside a selection combine with OR.
    """

    component_id: Identifier
    result_ids: list[Identifier]
    where: list[CategorySelection]


class ScopedContext(_Record):
    """Preserve units, time or qualifications with their scope and knowledge state."""

    id: Identifier
    kind: Literal[
        "unit", "scale", "time", "qualification", "uncertainty", "source", "other"
    ]
    name: Text
    meaning: Text
    value: Text | None
    status: Literal[
        "source_stated",
        "interpretation",
        "user_supplied",
        "unresolved",
        "not_applicable",
    ]
    applies_to: list[ModelScope] = Field(min_length=1)
    evidence: list[ModelEvidence]

    @model_validator(mode="after")
    def check_claim(self) -> "ScopedContext":
        """Keep unknown/inapplicable context distinct from sourced assertions."""
        if self.status in {"unresolved", "not_applicable"}:
            if self.value is not None:
                raise ValueError("Unresolved/inapplicable context must have null value")
        elif self.value is None or not self.evidence:
            raise ValueError("Asserted context needs a value and supporting evidence")
        if self.status == "user_supplied" and not any(
            e.basis == "user" for e in self.evidence
        ):
            raise ValueError("User-supplied context needs explicit user evidence")
        if self.status in {"source_stated", "interpretation"} and not any(
            e.basis in {"image", "docling"} for e in self.evidence
        ):
            raise ValueError(
                "Source/interpretive context needs image or Docling evidence"
            )
        return self


class ModelReference(_Record):
    """Reference a component, its field/category, or one of its result fields."""

    component_id: Identifier
    field_id: Identifier | None
    category_id: Identifier | None
    result_id: Identifier | None


class ModelRelationship(_Record):
    """Retain a directed relationship with explicit evidential qualification."""

    id: Identifier
    kind: Text
    description: Text
    status: Literal["source_stated", "interpretation", "user_supplied", "unresolved"]
    from_ref: ModelReference
    to_ref: ModelReference
    evidence: list[ModelEvidence] = Field(min_length=1)


class ModelQuestion(_Record):
    """Keep an unresolved question or an explicitly supported answer in the draft."""

    id: Identifier
    question: Text
    applies_to: list[ModelScope] = Field(min_length=1)
    answer: Text | None
    resolution: Literal["unresolved", "source", "user"]
    evidence: list[ModelEvidence]

    @model_validator(mode="after")
    def check_answer(self) -> "ModelQuestion":
        """Do not let an unsupported answer masquerade as a resolved question."""
        if self.resolution == "unresolved":
            if self.answer is not None:
                raise ValueError("An unresolved question must have a null answer")
        elif self.answer is None or not self.evidence:
            raise ValueError("A resolved question needs an answer and evidence")
        elif not any(
            e.basis in ({"user"} if self.resolution == "user" else {"image", "docling"})
            for e in self.evidence
        ):
            raise ValueError("Question evidence must match its resolution basis")
        return self


def _unique(values: list[str], description: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {description}")


class WorkingModel(_Record):
    """Describe an editable statistical interpretation, not a formal SDMX DSD."""

    title: Text
    components: list[ModelComponent] = Field(min_length=1)
    contexts: list[ScopedContext]
    relationships: list[ModelRelationship]
    questions: list[ModelQuestion]

    @model_validator(mode="after")
    def check_references(self) -> "WorkingModel":
        """Reject dangling scopes and identities without claiming image accuracy."""
        _unique([c.id for c in self.components], "component IDs")
        for collection, name in (
            (self.contexts, "context"),
            (self.relationships, "relationship"),
            (self.questions, "question"),
        ):
            _unique([item.id for item in collection], f"{name} IDs")
        components = {c.id: c for c in self.components}
        for component in self.components:
            _unique(
                [f.id for f in component.fields] + [r.id for r in component.results],
                "field/result IDs within a component",
            )
            for field in component.fields:
                _unique([c.id for c in field.categories], "category IDs within a field")

        def get_component(identifier: str) -> ModelComponent:
            if identifier not in components:
                raise ValueError(f"Unknown component: {identifier}")
            return components[identifier]

        def check_scope(scope: ModelScope) -> None:
            component = get_component(scope.component_id)
            _unique(scope.result_ids, "result IDs in scope")
            if not set(scope.result_ids) <= {r.id for r in component.results}:
                raise ValueError("Unknown result in context/question scope")
            _unique([s.field_id for s in scope.where], "fields in scope conditions")
            fields = {f.id: f for f in component.fields}
            for selection in scope.where:
                _unique(selection.category_ids, "selected category IDs")
                if selection.field_id not in fields or not set(
                    selection.category_ids
                ) <= {c.id for c in fields[selection.field_id].categories}:
                    raise ValueError("Unknown field/category in scope")

        def check_reference(ref: ModelReference) -> None:
            component = get_component(ref.component_id)
            if ref.result_id is not None:
                if (
                    ref.field_id is not None
                    or ref.category_id is not None
                    or ref.result_id not in {r.id for r in component.results}
                ):
                    raise ValueError("Invalid result reference")
            elif ref.field_id is not None:
                fields = {f.id: f for f in component.fields}
                if ref.field_id not in fields or (
                    ref.category_id is not None
                    and ref.category_id
                    not in {c.id for c in fields[ref.field_id].categories}
                ):
                    raise ValueError("Invalid field/category reference")
            elif ref.category_id is not None:
                raise ValueError("Category reference requires a field")

        for item in [*self.contexts, *self.questions]:
            for scope in item.applies_to:
                check_scope(scope)
        for relationship in self.relationships:
            check_reference(relationship.from_ref)
            check_reference(relationship.to_ref)
            if relationship.from_ref == relationship.to_ref:
                raise ValueError("Relationship must connect distinct references")
            expected = (
                {"user"}
                if relationship.status == "user_supplied"
                else {"image", "docling"}
            )
            if not any(e.basis in expected for e in relationship.evidence):
                raise ValueError(
                    "Relationship evidence does not support its stated basis"
                )
        for component in self.components:
            for result in component.results:
                if result.value_type == "number" and not any(
                    context.kind == "unit"
                    and any(
                        scope.component_id == component.id
                        and (not scope.result_ids or result.id in scope.result_ids)
                        for scope in context.applies_to
                    )
                    for context in self.contexts
                ):
                    raise ValueError(
                        "Numeric results need a unit context, even if unresolved"
                    )
        return self


def model_digest(model: WorkingModel) -> str:
    """Fingerprint model content independently of JSON whitespace and key ordering.

    Parameters
    ----------
    model : WorkingModel
        Validated statistical working model.

    Returns
    -------
    str
        SHA-256 of canonical UTF-8 JSON.
    """
    content = json.dumps(
        model.model_dump(mode="json"),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(content.encode()).hexdigest()
