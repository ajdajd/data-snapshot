"""Serialize reviewed observation keys and attributes as SDMX-JSON."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft201909Validator, FormatChecker


def exchange_messages(
    identifier: str,
    title: str,
    version: str,
    dimensions: list[dict[str, Any]],
    attributes: list[dict[str, Any]],
    datasets: list[list[dict[str, Any]]],
    measure_name: str = "Observation value",
    dataset_annotations: list[dict[str, str]] | None = None,
) -> tuple[dict, dict]:
    """Serialize validated long observations using one local DSD.

    Parameters
    ----------
    identifier, title, version : str
        Identity of the experimental LOCAL structure.
    dimensions, attributes : list of dict
        Component definitions with id, name, description and data_type.
    datasets : list of list of dict
        Each row contains a complete string key, numeric value and attribute map.
        Callers validate source semantics before invoking this serializer.
    measure_name : str, optional
        Display name of the numeric observation measure.
    dataset_annotations : list of dict, optional
        One SDMX annotation per dataset, retaining component identity and status.

    Returns
    -------
    tuple of dict
        Matching structure and data messages, checked against official schemas.

    Raises
    ------
    ValueError
        If keys are incomplete or duplicate within a dataset.
    jsonschema.ValidationError
        If a generated message fails its official exchange schema.
    """
    if dataset_annotations is not None and len(dataset_annotations) != len(datasets):
        raise ValueError("Dataset annotations must match datasets")
    for rows in datasets:
        keys = [tuple(row["key"]) for row in rows]
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate observation key")
        if any(len(key) != len(dimensions) for key in keys):
            raise ValueError("Incomplete observation key")
    identity = dict(id=identifier, agencyID="LOCAL", version=version, name=title)
    prefix = (
        "urn:sdmx:org.sdmx.infomodel.conceptscheme.Concept="
        f"LOCAL:{identifier}({version})."
    )
    dsd_urn = (
        "urn:sdmx:org.sdmx.infomodel.datastructure.DataStructure="
        f"LOCAL:{identifier}({version})"
    )
    meta = {
        "id": identifier,
        "prepared": datetime.now(timezone.utc).isoformat(),
        "sender": {"id": "LOCAL"},
        "test": True,
    }
    measure = {"id": "OBS_VALUE", "name": measure_name, "data_type": "Double"}
    components = dimensions + [measure] + attributes
    concepts = [
        {k: c[k] for k in ("id", "name", "description") if k in c} for c in components
    ]

    def representation(component: dict[str, Any]) -> dict:
        return {"format": {"dataType": component.get("data_type", "String")}}

    descriptors = {
        "dimensionList": {
            "id": "DimensionDescriptor",
            "dimensions": [
                {
                    "id": c["id"],
                    "position": i,
                    "conceptIdentity": prefix + c["id"],
                    "localRepresentation": representation(c),
                }
                for i, c in enumerate(dimensions)
            ],
        },
        "measureList": {
            "id": "MeasureDescriptor",
            "measures": [
                {
                    "id": "OBS_VALUE",
                    "conceptIdentity": prefix + "OBS_VALUE",
                    "localRepresentation": representation(measure),
                }
            ],
        },
    }
    if attributes:
        descriptors["attributeList"] = {
            "id": "AttributeDescriptor",
            "attributes": [
                {
                    "id": c["id"],
                    "conceptIdentity": prefix + c["id"],
                    "localRepresentation": representation(c),
                    "usage": "optional",
                    "attributeRelationship": {"observation": {}},
                }
                for c in attributes
            ],
        }
    structure = {
        "$schema": "https://json.sdmx.org/2.1.0/sdmx-json-structure-schema.json",
        "meta": meta,
        "data": {
            "conceptSchemes": [{**identity, "concepts": concepts}],
            "dataStructures": [{**identity, "dataStructureComponents": descriptors}],
        },
    }
    rows = [row for dataset in datasets for row in dataset]
    dimension_values = [
        list(dict.fromkeys(row["key"][i] for row in rows))
        for i in range(len(dimensions))
    ]
    attribute_values = [
        list(
            dict.fromkeys(
                row.get("attributes", {}).get(c["id"])
                for row in rows
                if row.get("attributes", {}).get(c["id"]) is not None
            )
        )
        for c in attributes
    ]
    data_structure = {
        "name": title,
        "links": [
            {"rel": "datastructure", "urn": dsd_urn, "href": "structure.sdmx.json"}
        ],
        "dimensions": {
            "observation": [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "keyPosition": i,
                    "format": representation(c)["format"],
                    "values": [{"value": v} for v in dimension_values[i]],
                }
                for i, c in enumerate(dimensions)
            ]
        },
        "measures": {
            "observation": [
                {
                    "id": "OBS_VALUE",
                    "name": measure["name"],
                    "format": representation(measure)["format"],
                }
            ]
        },
    }
    if attributes:
        data_structure["attributes"] = {
            "observation": [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "format": representation(c)["format"],
                    "relationship": {"observation": {}},
                    # No reported value still needs an index dictionary.
                    "values": [{"value": v} for v in attribute_values[i]] or [None],
                }
                for i, c in enumerate(attributes)
            ]
        }
    if dataset_annotations:
        data_structure["annotations"] = dataset_annotations
    output_datasets = []
    for dataset_index, dataset in enumerate(datasets):
        observations = {}
        for row in dataset:
            key = ":".join(
                str(dimension_values[i].index(v)) for i, v in enumerate(row["key"])
            )
            indexes = []
            for i, c in enumerate(attributes):
                value = row.get("attributes", {}).get(c["id"])
                indexes.append(
                    attribute_values[i].index(value) if value is not None else None
                )
            observations[key] = [row["value"], *indexes]
        output_datasets.append(
            {"structure": 0, "action": "Information", "observations": observations}
        )
        if dataset_annotations:
            output_datasets[-1]["annotations"] = [dataset_index]
    data = {
        "$schema": "https://json.sdmx.org/2.1.0/sdmx-json-data-schema.json",
        "meta": meta,
        "data": {"structures": [data_structure], "dataSets": output_datasets},
    }
    for kind, message in (("structure", structure), ("data", data)):
        schema = json.loads(
            (
                Path(__file__).parent / "schemas" / f"sdmx-json-{kind}-schema.json"
            ).read_text()
        )
        Draft201909Validator(schema, format_checker=FormatChecker()).validate(message)
    return structure, data
