"""Represent long observations and serialize a local SDMX prototype profile."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft201909Validator, FormatChecker
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator


class Axis(BaseModel):
    """Describe a statistical dimension selected by the mapping profile."""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    name: str = Field(min_length=1)


class Profile(BaseModel):
    """Define the two axes of a simple numerical table, independently of OCR."""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    title: str = Field(min_length=1)
    measure: str = Field(min_length=1)
    axes: list[Axis] = Field(min_length=2, max_length=2)
    column_labels: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def check_axes(self) -> "Profile":
        """Require distinct, non-reserved dimension identifiers."""
        ids = [a.id for a in self.axes]
        if len(set(ids)) != 2 or set(ids) & {"OBS_VALUE", "TIME_PERIOD"}:
            raise ValueError("Axes must have distinct non-reserved identifiers")
        if any(not s.strip() for s in self.column_labels) or len(
            {s.casefold() for s in self.column_labels}
        ) != len(self.column_labels):
            raise ValueError("Column labels must be nonempty and distinct")
        return self


class Observation(BaseModel):
    """Retain a value, its full dimension key, and its extraction evidence."""

    model_config = ConfigDict(extra="forbid")
    key: tuple[str, str]
    value: FiniteFloat | None
    raw_text: str
    cell_ref: str


class Dataset(BaseModel):
    """Represent explicitly mapped observations before exchange serialization."""

    model_config = ConfigDict(extra="forbid")
    profile: Profile
    source_image: str
    observations: list[Observation] = Field(min_length=1)

    @model_validator(mode="after")
    def check_keys(self) -> "Dataset":
        """Reject empty, duplicated or undefined observation coordinates."""
        keys = [o.key for o in self.observations]
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate observation key")
        for row, column in keys:
            if not row.strip() or column not in self.profile.column_labels:
                raise ValueError("Empty row label or undefined column label")
        return self


def map_table(native: dict[str, Any], profile: Profile, image: Path) -> Dataset:
    """Map one rectangular table using a reviewed first-row/first-column profile.

    Parameters
    ----------
    native : dict
        Native Docling document. Exactly one table is required.
    profile : Profile
        Reviewed meaning of row and column labels; contains no expected values.
    image : Path
        Source image retained as provenance.

    Returns
    -------
    Dataset
        Long observations with native cell references and original number text.

    Raises
    ------
    ValueError
        If structure is ambiguous, cells are missing, or numbers need interpretation.
    """
    tables = native.get("tables", [])
    if len(tables) != 1:
        raise ValueError(
            f"Expected one table, found {len(tables)}; inspect native.json"
        )
    table = tables[0]["data"]
    rows, columns = table["num_rows"], table["num_cols"]
    if rows < 2 or columns != len(profile.column_labels) + 1:
        raise ValueError("Table shape does not match the reviewed profile")
    grid = {}
    for index, cell in enumerate(table["table_cells"]):
        if cell.get("row_span", 1) != 1 or cell.get("col_span", 1) != 1:
            raise ValueError("Merged cells require a reviewed mapping")
        key = (cell["start_row_offset_idx"], cell["start_col_offset_idx"])
        if key in grid:
            raise ValueError("Overlapping cells require review")
        if not (0 <= key[0] < rows and 0 <= key[1] < columns):
            raise ValueError("Cell lies outside the declared table grid")
        grid[key] = (cell["text"].strip(), f"#/tables/0/data/table_cells/{index}")
    # shortcut: only single-level headers are mapped; extend after native trials.
    for column, expected in enumerate(profile.column_labels, 1):
        if grid.get((0, column), ("",))[0].casefold() != expected.casefold():
            raise ValueError(f"Column {column} is not the expected header {expected!r}")
    observations = []
    for row in range(1, rows):
        label = grid.get((row, 0), ("",))[0]
        for column, header in enumerate(profile.column_labels, 1):
            if (row, column) not in grid:
                raise ValueError(f"Missing cell at row {row}, column {column}")
            text, ref = grid[row, column]
            if text in {"", "..", "...", "—", "–"}:
                value = None
            elif re.fullmatch(
                r"[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)", text
            ):
                value = float(text.replace(",", ""))
            else:
                raise ValueError(f"Ambiguous number {text!r} at {ref}; requires review")
            observations.append(
                Observation(
                    key=(label, header), value=value, raw_text=text, cell_ref=ref
                )
            )
    return Dataset(
        profile=profile, source_image=str(image.resolve()), observations=observations
    )


def sdmx_messages(dataset: Dataset) -> tuple[dict, dict]:
    """Build and validate matching SDMX-JSON 2.1.0 structure and data messages.

    Parameters
    ----------
    dataset : Dataset
        Observations mapped to the local prototype profile.

    Returns
    -------
    tuple[dict, dict]
        Structure message (including concepts and DSD), followed by data message.
    """
    profile = dataset.profile
    version = "0.1.0"
    identity = {
        "id": profile.id,
        "agencyID": "LOCAL",
        "version": version,
        "name": profile.title,
    }
    concept_prefix = f"urn:sdmx:org.sdmx.infomodel.conceptscheme.Concept=LOCAL:{profile.id}({version})."
    dsd_urn = f"urn:sdmx:org.sdmx.infomodel.datastructure.DataStructure=LOCAL:{profile.id}({version})"
    prepared = datetime.now(timezone.utc).isoformat()
    meta = {
        "id": profile.id,
        "prepared": prepared,
        "sender": {"id": "LOCAL"},
        "test": True,
    }
    concepts = [{"id": a.id, "name": a.name} for a in profile.axes]
    concepts.append({"id": "OBS_VALUE", "name": profile.measure})
    dims = [
        {
            "id": a.id,
            "position": index,
            "conceptIdentity": concept_prefix + a.id,
            "localRepresentation": {"format": {"dataType": "String"}},
        }
        for index, a in enumerate(profile.axes)
    ]
    measure = {
        "id": "OBS_VALUE",
        "conceptIdentity": concept_prefix + "OBS_VALUE",
        "localRepresentation": {"format": {"dataType": "Double"}},
    }
    structure = {
        "$schema": "https://json.sdmx.org/2.1.0/sdmx-json-structure-schema.json",
        "meta": meta,
        "data": {
            "conceptSchemes": [{**identity, "concepts": concepts}],
            "dataStructures": [
                {
                    **identity,
                    "dataStructureComponents": {
                        "dimensionList": {
                            "id": "DimensionDescriptor",
                            "dimensions": dims,
                        },
                        "measureList": {
                            "id": "MeasureDescriptor",
                            "measures": [measure],
                        },
                    },
                }
            ],
        },
    }
    values = [
        list(dict.fromkeys(o.key[i] for o in dataset.observations)) for i in range(2)
    ]
    observations = {
        ":".join(str(values[i].index(v)) for i, v in enumerate(o.key)): [o.value]
        for o in dataset.observations
    }
    data = {
        "$schema": "https://json.sdmx.org/2.1.0/sdmx-json-data-schema.json",
        "meta": meta,
        "data": {
            "structures": [
                {
                    "name": profile.title,
                    "links": [
                        {
                            "rel": "datastructure",
                            "urn": dsd_urn,
                            "href": "structure.sdmx.json",
                        }
                    ],
                    "dimensions": {
                        "observation": [
                            {
                                "id": a.id,
                                "name": a.name,
                                "keyPosition": i,
                                "format": {"dataType": "String"},
                                "values": [{"value": v} for v in values[i]],
                            }
                            for i, a in enumerate(profile.axes)
                        ]
                    },
                    "measures": {
                        "observation": [
                            {
                                "id": "OBS_VALUE",
                                "name": profile.measure,
                                "format": {"dataType": "Double"},
                            }
                        ]
                    },
                }
            ],
            "dataSets": [
                {"structure": 0, "action": "Information", "observations": observations}
            ],
        },
    }
    for kind, message in (("structure", structure), ("data", data)):
        schema = json.loads(
            (
                Path(__file__).parent / "schemas" / f"sdmx-json-{kind}-schema.json"
            ).read_text()
        )
        Draft201909Validator(schema, format_checker=FormatChecker()).validate(message)
    return structure, data
