"""Define a provisional DSD and validate model-produced long observations."""

import json
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FiniteFloat,
    StrictInt,
    create_model,
    model_validator,
)

from .exchange import exchange_messages


class Component(BaseModel):
    """Describe a local, uncoded DSD component and its intended meaning."""

    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    data_type: Literal["String", "Double", "Integer"]


class DraftDSD(BaseModel):
    """Configure a LOCAL DSD independently of any extraction engine.

    This draft supports uncoded string dimensions and observation attributes.
    It is a design configuration, not an imported registry DSD.
    """

    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    title: str = Field(min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    scope: str = Field(min_length=1)
    dimensions: list[Component] = Field(min_length=1)
    attributes: list[Component]

    @model_validator(mode="after")
    def check_components(self) -> "DraftDSD":
        """Reject collisions and representations the serializer cannot express."""
        identifiers = [c.id for c in self.dimensions + self.attributes]
        reserved = {
            "OBS_VALUE",
            "TIME_PERIOD",
            "EVIDENCE_TEXT",
            "EXTRACTION_METHOD",
            "SOURCE_LOCATION",
            "EXTRACTION_NOTE",
        }
        if len(identifiers) != len(set(identifiers)) or set(identifiers) & reserved:
            raise ValueError("DSD component IDs must be unique and non-reserved")
        if any(c.data_type != "String" for c in self.dimensions):
            raise ValueError("This draft supports only uncoded string dimensions")
        numeric_attributes = {
            "LOWER_BOUND": "Double",
            "UPPER_BOUND": "Double",
            "CONFIDENCE_LEVEL": "Double",
            "UNIT_MULT": "Integer",
        }
        for component in self.attributes:
            expected = numeric_attributes.get(component.id)
            if expected is not None and component.data_type != expected:
                raise ValueError(f"Attribute {component.id} requires {expected}")
        return self


class Evidence(BaseModel):
    """Retain image-local evidence and distinguish printed from estimated values."""

    model_config = ConfigDict(extra="forbid", strict=True)
    raw_text: str | None
    location: str = Field(min_length=1)
    method: Literal["printed", "estimated"]
    note: str | None


class Omission(BaseModel):
    """Explain content that could not be represented or extracted reliably."""

    model_config = ConfigDict(extra="forbid", strict=True)
    location: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class LongObservation(BaseModel):
    """Validate a numeric observation independently of its generated key model."""

    model_config = ConfigDict(extra="forbid", strict=True)
    value: FiniteFloat | None
    evidence: Evidence

    @model_validator(mode="after")
    def check_evidence(self) -> "LongObservation":
        """Require evidence for values and an explanation for estimates/missingness."""
        if self.value is not None and self.evidence.method == "printed":
            if not self.evidence.raw_text or not self.evidence.raw_text.strip():
                raise ValueError("Printed values need their original number text")
        if self.value is None or self.evidence.method == "estimated":
            if not self.evidence.note or not self.evidence.note.strip():
                raise ValueError("Missing or estimated values need an evidence note")
        if any(
            v is not None and not v.strip()
            for v in self.dimensions.model_dump().values()
        ):
            raise ValueError("Dimension labels must be nonempty or null")
        attributes = self.attributes.model_dump()
        lower, upper = attributes.get("LOWER_BOUND"), attributes.get("UPPER_BOUND")
        if lower is not None and upper is not None and lower > upper:
            raise ValueError("Lower bound exceeds upper bound")
        confidence = attributes.get("CONFIDENCE_LEVEL")
        if confidence is not None and not 0 < confidence <= 100:
            raise ValueError("Confidence level must be a percentage in (0, 100]")
        return self


class StatisticalDataset(BaseModel):
    """Identify a component dataset without exposing filenames to the model."""

    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    title: str = Field(min_length=1)

    @model_validator(mode="after")
    def check_keys(self) -> "StatisticalDataset":
        """Refuse silent overwrites of observations with the same full key."""
        keys = [tuple(o.dimensions.model_dump().values()) for o in self.observations]
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate observation key; DSD may lack a distinction")
        return self


class StatisticalExtraction(BaseModel):
    """Describe completion relative to the image, without claiming correctness."""

    model_config = ConfigDict(extra="forbid", strict=True)
    status: Literal["complete", "partial", "unsupported"]
    not_extracted: list[Omission]
    notes: str | None

    @model_validator(mode="after")
    def check_status(self) -> "StatisticalExtraction":
        """Make partial/unsupported results explicit and internally consistent."""
        if (self.status == "unsupported") != (not self.datasets):
            raise ValueError("Only unsupported extraction may have no datasets")
        if (self.status == "complete") != (not self.not_extracted):
            raise ValueError(
                "Partial/unsupported results require omitted-content reasons"
            )
        ids = [d.id for d in self.datasets]
        if len(ids) != len(set(ids)):
            raise ValueError("Dataset IDs must be unique")
        return self


def extraction_model(dsd: DraftDSD) -> type[StatisticalExtraction]:
    """Build the strict response model from the chosen DSD components.

    Parameters
    ----------
    dsd : DraftDSD
        Reviewed draft defining every dimension and attribute.

    Returns
    -------
    type of StatisticalExtraction
        Pydantic model with exact key/attribute fields and semantic checks.
    """
    types = {"String": str, "Double": FiniteFloat, "Integer": StrictInt}

    def component_model(name: str, components: list[Component]) -> type[BaseModel]:
        return create_model(
            name,
            __config__=ConfigDict(extra="forbid", strict=True),
            **{
                c.id: (types[c.data_type] | None, Field(description=c.description))
                for c in components
            },
        )

    dimensions = component_model("Dimensions", dsd.dimensions)
    attributes = component_model("Attributes", dsd.attributes)
    observation = create_model(
        "Observation",
        __base__=LongObservation,
        dimensions=(dimensions, ...),
        attributes=(attributes, ...),
    )
    dataset = create_model(
        "Dataset",
        __base__=StatisticalDataset,
        observations=(list[observation], Field(min_length=1)),
    )
    return create_model(
        "Extraction", __base__=StatisticalExtraction, datasets=(list[dataset], ...)
    )


def statistical_messages(
    dsd: DraftDSD, result: StatisticalExtraction
) -> tuple[dict, dict]:
    """Write numeric datasets plus evidence using the same DSD as validation.

    Parameters
    ----------
    dsd : DraftDSD
        Validated local definition.
    result : StatisticalExtraction
        Model output validated with ``extraction_model(dsd)``.

    Returns
    -------
    tuple of dict
        Official-schema-validated SDMX structure and data messages.

    Raises
    ------
    ValueError
        If the extraction is unsupported and contains no numeric dataset.
    """
    if not result.datasets:
        raise ValueError("Unsupported content has no SDMX observation dataset")
    evidence_components = [
        {"id": identifier, "name": name, "data_type": "String"}
        for identifier, name in [
            ("EVIDENCE_TEXT", "Original displayed number text"),
            ("SOURCE_LOCATION", "Location within source image"),
            ("EXTRACTION_METHOD", "Printed or estimated extraction"),
            ("EXTRACTION_NOTE", "Extraction qualification"),
        ]
    ]
    datasets = []
    for dataset in result.datasets:
        rows = []
        for o in dataset.observations:
            dimensions = o.dimensions.model_dump()
            rows.append(
                {
                    "key": [
                        dimensions[c.id] if dimensions[c.id] is not None else "_UNKNOWN"
                        for c in dsd.dimensions
                    ],
                    "value": o.value,
                    "attributes": {
                        **o.attributes.model_dump(),
                        "EVIDENCE_TEXT": o.evidence.raw_text,
                        "SOURCE_LOCATION": o.evidence.location,
                        "EXTRACTION_METHOD": o.evidence.method,
                        "EXTRACTION_NOTE": o.evidence.note,
                    },
                }
            )
        datasets.append(rows)
    return exchange_messages(
        dsd.id,
        dsd.title,
        dsd.version,
        [c.model_dump() for c in dsd.dimensions],
        [c.model_dump() for c in dsd.attributes] + evidence_components,
        datasets,
        dataset_annotations=[
            {
                "id": dataset.id,
                "title": dataset.title,
                "type": "DATA_SNAPSHOT_COMPONENT",
                "text": json.dumps(
                    {
                        "extraction_status": result.status,
                        "not_extracted": [o.model_dump() for o in result.not_extracted],
                        "notes": result.notes,
                    },
                    ensure_ascii=False,
                ),
            }
            for dataset in result.datasets
        ],
    )
