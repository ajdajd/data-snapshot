"""Encode an accepted snapshot model and reviewed observations as portable SDMX."""

import hashlib
import io
import json
import math
import zipfile
from pathlib import Path
from typing import Any

from .data_review import reviewed_export
from .accepted_extraction import accepted_result_model
from .exchange import exchange_messages, validate_messages
from .working_model import WorkingModel


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def _contexts(model: WorkingModel, row: dict) -> dict:
    matched = {}
    for context in model.contexts:
        if any(
            scope.component_id == row["component_id"]
            and (not scope.result_ids or row["result_id"] in scope.result_ids)
            and all(
                row["dimensions"][selection.field_id] in selection.category_ids
                for selection in scope.where
            )
            for scope in context.applies_to
        ):
            matched[context.id] = {"value": context.value, "status": context.status}
    return matched


def _annotation(kind: str, value: Any) -> dict:
    return {"type": kind, "text": _json(value)}


def _metadata(dsd: dict) -> dict:
    return json.loads(
        next(
            a["text"]
            for a in dsd["annotations"]
            if a["type"] == "DATA_SNAPSHOT_MAPPING"
        )
    )


def _urn(kind: str, item: dict) -> str:
    family = {
        "DataStructure": "datastructure",
        "Codelist": "codelist",
        "ConceptScheme": "conceptscheme",
    }[kind]
    return f"urn:sdmx:org.sdmx.infomodel.{family}.{kind}={item['agencyID']}:{item['id']}({item['version']})"


def _record(row: dict, contexts: dict) -> dict:
    return {**row, "contexts": contexts}


def snapshot_messages(reviewed: dict) -> tuple[dict, dict]:
    """Encode typed component/results with scoped attributes and local codelists.

    Parameters
    ----------
    reviewed : dict
        Validated and approved package returned by reviewed_export.

    Returns
    -------
    tuple of dict
        Schema-validated SDMX structure and data messages. Each component/result
        has its own typed DSD and dataset, avoiding numeric/text coercion.
    """
    model = WorkingModel.model_validate(reviewed["model"])
    accepted_result_model(model).model_validate(reviewed["data"])
    observations = reviewed["data"]["observations"]
    token = hashlib.sha256(
        _json({"model": reviewed["model"], "data": reviewed["data"]}).encode()
    ).hexdigest()[:20]
    structure = data = None
    for ci, component in enumerate(model.components, 1):
        for ri, result in enumerate(component.results, 1):
            selected = [
                o
                for o in observations
                if o["component_id"] == component.id and o["result_id"] == result.id
            ]
            dimensions, mapping = [], {}
            for field in component.fields:
                sources = {category.id: category.id for category in field.categories}
                codes = [
                    {
                        "id": c.id,
                        "name": c.source_label,
                        **(
                            {
                                "annotations": [
                                    {"type": "DISPLAY_LABEL", "text": c.display_label}
                                ]
                            }
                            if c.display_label
                            else {}
                        ),
                    }
                    for c in field.categories
                ]
                if not codes:
                    for value in dict.fromkeys(
                        o["dimensions"][field.id]
                        for o in selected
                        if o["dimensions"][field.id] is not None
                    ):
                        code = f"V{len(codes) + 1}"
                        sources[code] = value
                        codes.append({"id": code, "name": value})
                if any(o["dimensions"][field.id] is None for o in selected):
                    code = "MISSING_KEY"
                    while code in sources:
                        code += "_"
                    sources[code] = None
                    codes.append({"id": code, "name": "Unspecified identifying value"})
                dimensions.append(
                    {
                        "id": "D_" + field.id,
                        "name": field.name,
                        "description": field.meaning,
                        "codes": codes,
                    }
                )
                mapping[field.id] = {"id": "D_" + field.id, "sources": sources}
            if not dimensions:
                dimensions = [
                    {
                        "id": "SNAPSHOT_RECORD",
                        "name": "Snapshot scalar record",
                        "codes": [
                            {
                                "id": "SINGLE",
                                "name": "The scalar result in this snapshot",
                            }
                        ],
                    }
                ]
            attributes = [
                {"id": key, "name": name, "data_type": dtype}
                for key, name, dtype in [
                    ("EVIDENCE_TEXT", "Original value text", "String"),
                    ("SOURCE_LOCATION", "Source location", "String"),
                    ("EXTRACTION_METHOD", "Printed, estimated or missing", "String"),
                    ("EXTRACTION_NOTE", "Extraction or review note", "String"),
                    ("LOWER_BOUND", "Lower displayed bound", "Double"),
                    ("UPPER_BOUND", "Upper displayed bound", "Double"),
                    ("BOUND_EVIDENCE", "Evidence for displayed bounds", "String"),
                ]
            ]
            contexts = [
                c
                for c in model.contexts
                if any(
                    s.component_id == component.id
                    and (not s.result_ids or result.id in s.result_ids)
                    for s in c.applies_to
                )
            ]
            for context in contexts:
                attributes.extend(
                    [
                        {
                            "id": "A_" + context.id,
                            "name": context.name,
                            "description": context.meaning,
                        },
                        {
                            "id": "S_" + context.id,
                            "name": context.name + " — knowledge status",
                        },
                    ]
                )
            rows = []
            for observation in selected:
                evidence, bounds = observation["evidence"], observation["bounds"]
                values = {
                    "EVIDENCE_TEXT": evidence["raw_text"],
                    "SOURCE_LOCATION": evidence["location"],
                    "EXTRACTION_METHOD": evidence["method"],
                    "EXTRACTION_NOTE": evidence["note"],
                    "LOWER_BOUND": bounds["lower"] if bounds else None,
                    "UPPER_BOUND": bounds["upper"] if bounds else None,
                    "BOUND_EVIDENCE": _json(bounds["evidence"]) if bounds else None,
                }
                for key, context in _contexts(model, observation).items():
                    values["A_" + key] = context["value"]
                    values["S_" + key] = context["status"]
                keys = [
                    next(
                        code
                        for code, value in definition["sources"].items()
                        if value == observation["dimensions"][field]
                    )
                    for field, definition in mapping.items()
                ]
                rows.append(
                    {
                        "key": keys or ["SINGLE"],
                        "value": observation["value"],
                        "attributes": values,
                    }
                )
            identifier = f"SNAPSHOT_{token}_C{ci}_R{ri}"
            single_structure, single_data = exchange_messages(
                identifier,
                f"{component.name} — {result.name}",
                "1.0.0",
                dimensions,
                attributes,
                [rows],
                result.name,
                measure_data_type=(
                    "Double" if result.value_type == "number" else "String"
                ),
            )
            descriptor = single_structure["data"]["dataStructures"][0]
            descriptor["annotations"] = [
                _annotation(
                    "DATA_SNAPSHOT_MAPPING",
                    {
                        "component_id": component.id,
                        "result_id": result.id,
                        "dimensions": mapping,
                        "contexts": [c.id for c in contexts],
                    },
                ),
                _annotation(
                    "DATA_SNAPSHOT_MODEL",
                    {
                        "component": component.model_dump(mode="json"),
                        "result": result.model_dump(mode="json"),
                        "contexts": [c.model_dump(mode="json") for c in contexts],
                        "relationships": [
                            r.model_dump(mode="json") for r in model.relationships
                        ],
                        "questions": [
                            q.model_dump(mode="json") for q in model.questions
                        ],
                    },
                ),
                _annotation(
                    "DATA_SNAPSHOT_REVIEW",
                    {
                        key: reviewed[key]
                        for key in [
                            "image_sha256",
                            "model_revision",
                            "model_sha256",
                            "data_origin",
                        ]
                    },
                ),
                _annotation(
                    "EXTRACTION_STATUS",
                    {
                        key: reviewed["data"][key]
                        for key in ["status", "omissions", "notes"]
                    },
                ),
            ]
            if structure is None:
                structure, data = single_structure, single_data
            else:
                offset = len(data["data"]["structures"])
                for key in ["dataStructures", "conceptSchemes", "codelists"]:
                    if key in single_structure["data"]:
                        structure["data"].setdefault(key, []).extend(
                            single_structure["data"][key]
                        )
                data["data"]["structures"].extend(single_data["data"]["structures"])
                for dataset in single_data["data"]["dataSets"]:
                    dataset["structure"] = offset
                    data["data"]["dataSets"].append(dataset)
    validate_snapshot_messages(reviewed, structure, data)
    return structure, data


def decode_messages(structure: dict, data: dict) -> list[dict]:
    """Decode indexed data while resolving local DSDs, concepts and codelists.

    Parameters
    ----------
    structure, data : dict
        SDMX-JSON structure and observation messages.

    Returns
    -------
    list of dict
        Restored source keys, typed values, evidence, bounds and scoped contexts.

    Raises
    ------
    ValueError
        If references, indexes, component order or representations are inconsistent.
    """
    validate_messages(structure, data)
    dsds = {_urn("DataStructure", d): d for d in structure["data"]["dataStructures"]}
    lists = {_urn("Codelist", c): c for c in structure["data"].get("codelists", [])}
    concepts = {
        _urn("ConceptScheme", scheme).replace(".ConceptScheme=", ".Concept=")
        + "."
        + c["id"]
        for scheme in structure["data"]["conceptSchemes"]
        for c in scheme["concepts"]
    }
    restored = []

    def indexed(values: list, index: Any) -> Any:
        if type(index) is not int or not 0 <= index < len(values):
            raise ValueError("Invalid SDMX dictionary index")
        return values[index]

    for dataset in data["data"]["dataSets"]:
        definition = indexed(data["data"]["structures"], dataset["structure"])
        reference = next(
            link["urn"]
            for link in definition["links"]
            if link["rel"] == "datastructure"
        )
        if reference not in dsds:
            raise ValueError("SDMX dataset references an absent DSD")
        dsd = dsds[reference]
        metadata = _metadata(dsd)
        descriptors = dsd["dataStructureComponents"]
        dimensions = definition["dimensions"]["observation"]
        attributes = definition["attributes"]["observation"]
        if [d["id"] for d in dimensions] != [
            d["id"] for d in descriptors["dimensionList"]["dimensions"]
        ] or [a["id"] for a in attributes] != [
            a["id"] for a in descriptors["attributeList"]["attributes"]
        ]:
            raise ValueError("SDMX component order differs from DSD")
        components = (
            descriptors["dimensionList"]["dimensions"]
            + descriptors["measureList"]["measures"]
            + descriptors["attributeList"]["attributes"]
        )
        if any(c["conceptIdentity"] not in concepts for c in components):
            raise ValueError("SDMX concept reference does not resolve")
        if (
            definition["measures"]["observation"][0]["format"]
            != descriptors["measureList"]["measures"][0]["localRepresentation"][
                "format"
            ]
        ):
            raise ValueError("SDMX measure type differs from DSD")
        for dimension, declared in zip(
            dimensions, descriptors["dimensionList"]["dimensions"]
        ):
            urn = declared["localRepresentation"].get("enumeration")
            if urn:
                if urn not in lists or [v["id"] for v in dimension["values"]] != [
                    c["id"] for c in lists[urn]["codes"]
                ]:
                    raise ValueError(
                        "SDMX dimension values differ from referenced codelist"
                    )
        for key, packed in dataset.get("observations", {}).items():
            indexes = key.split(":")
            if len(indexes) != len(dimensions) or len(packed) != 1 + len(attributes):
                raise ValueError("SDMX observation tuple has incorrect length")
            dtype = definition["measures"]["observation"][0]["format"]["dataType"]
            if packed[0] is not None and (
                dtype == "String"
                and not isinstance(packed[0], str)
                or dtype == "Double"
                and (
                    type(packed[0]) not in (int, float) or not math.isfinite(packed[0])
                )
            ):
                raise ValueError("SDMX observation value violates its measure type")
            codes = {
                d["id"]: indexed(d["values"], int(index))["id"]
                for d, index in zip(dimensions, indexes)
            }
            values = {
                a["id"]: (
                    indexed(a["values"], index)["value"] if index is not None else None
                )
                for a, index in zip(attributes, packed[1:])
            }
            bounds = None
            if values["BOUND_EVIDENCE"] is not None:
                bounds = {
                    "lower": values["LOWER_BOUND"],
                    "upper": values["UPPER_BOUND"],
                    "evidence": json.loads(values["BOUND_EVIDENCE"]),
                }
            restored.append(
                _record(
                    {
                        "component_id": metadata["component_id"],
                        "result_id": metadata["result_id"],
                        "dimensions": {
                            field: mapping["sources"][codes[mapping["id"]]]
                            for field, mapping in metadata["dimensions"].items()
                        },
                        "value": packed[0],
                        "bounds": bounds,
                        "evidence": {
                            "raw_text": values["EVIDENCE_TEXT"],
                            "location": values["SOURCE_LOCATION"],
                            "method": values["EXTRACTION_METHOD"],
                            "note": values["EXTRACTION_NOTE"],
                        },
                    },
                    {
                        cid: {"value": values["A_" + cid], "status": values["S_" + cid]}
                        for cid in metadata["contexts"]
                        if values["S_" + cid] is not None
                    },
                )
            )
    return restored


def validate_snapshot_messages(reviewed: dict, structure: dict, data: dict) -> None:
    """Check official schemas and lossless decoding against the reviewed source.

    Parameters
    ----------
    reviewed : dict
        Approved source package.
    structure, data : dict
        Exported SDMX messages.

    Raises
    ------
    ValueError
        If SDMX decoding changes or drops any source value or scoped context.
    """
    model = WorkingModel.model_validate(reviewed["model"])
    accepted_result_model(model).model_validate(reviewed["data"])
    definitions = {(c.id, r.id): (c, r) for c in model.components for r in c.results}
    seen = []
    for dsd in structure["data"]["dataStructures"]:
        metadata = _metadata(dsd)
        pair = (metadata["component_id"], metadata["result_id"])
        if pair not in definitions:
            raise ValueError("Exported DSD does not belong to the accepted data model")
        seen.append(pair)
        component, result = definitions[pair]
        if set(metadata["dimensions"]) != {f.id for f in component.fields}:
            raise ValueError("DSD dimensions do not match accepted identifying fields")
        dtype = dsd["dataStructureComponents"]["measureList"]["measures"][0][
            "localRepresentation"
        ]["format"]["dataType"]
        if dtype != ("Double" if result.value_type == "number" else "String"):
            raise ValueError(
                "DSD measure representation differs from accepted result type"
            )
        annotation = json.loads(
            next(
                a["text"]
                for a in dsd["annotations"]
                if a["type"] == "DATA_SNAPSHOT_MODEL"
            )
        )
        if annotation["component"] != component.model_dump(mode="json") or annotation[
            "result"
        ] != result.model_dump(mode="json"):
            raise ValueError("DSD model annotation changed")
    if len(seen) != len(definitions) or set(seen) != set(definitions):
        raise ValueError(
            "Export must include each accepted component/result exactly once"
        )
    expected = [
        _record(o, _contexts(model, o)) for o in reviewed["data"]["observations"]
    ]
    restored = decode_messages(structure, data)
    if sorted(map(_json, expected)) != sorted(map(_json, restored)):
        raise ValueError("SDMX round-trip differs from reviewed observations")


def export_bundle(session_dir: Path, extraction_dir: Path) -> bytes:
    """Bundle the PNG, validated SDMX messages and the full review audit record.

    Parameters
    ----------
    session_dir, extraction_dir : Path
        Current accepted model session and approved extraction.

    Returns
    -------
    bytes
        ZIP containing snapshot.png, structure.sdmx.json, data.sdmx.json,
        reviewed.json and a SHA-256 manifest. No API calls or source changes.
    """
    reviewed = reviewed_export(session_dir, extraction_dir)
    structure, data = snapshot_messages(reviewed)
    reviewed["sdmx_formalization"] = "encoded"
    parts = {
        "snapshot.png": (session_dir / "input.png").read_bytes(),
        "structure.sdmx.json": (_json(structure) + "\n").encode(),
        "data.sdmx.json": (_json(data) + "\n").encode(),
        "reviewed.json": (_json(reviewed) + "\n").encode(),
    }
    manifest = {
        "format": "data-snapshot-sdmx-bundle",
        "sdmx_json_version": "2.1.0",
        "sdmx_information_model": "3.1.0",
        "validation": "official schemas, local references and lossless reviewed-data round-trip",
        "sha256": {
            name: hashlib.sha256(content).hexdigest() for name, content in parts.items()
        },
    }
    parts["manifest.json"] = (_json(manifest) + "\n").encode()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            archive.writestr(name, content)
    return output.getvalue()


def validate_bundle(content: bytes) -> dict:
    """Verify a standalone exported ZIP, including PNG and review/source checksums.

    Parameters
    ----------
    content : bytes
        Downloaded bundle bytes.

    Returns
    -------
    dict
        Counts and identity of the independently validated export.

    Raises
    ------
    ValueError
        If a file checksum, source identity or decoded observation differs.
    """
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        if set(archive.namelist()) != {
            "snapshot.png",
            "structure.sdmx.json",
            "data.sdmx.json",
            "reviewed.json",
            "manifest.json",
        }:
            raise ValueError("Unexpected bundle contents")
        for name in [
            "snapshot.png",
            "structure.sdmx.json",
            "data.sdmx.json",
            "reviewed.json",
        ]:
            if hashlib.sha256(archive.read(name)).hexdigest() != manifest["sha256"].get(
                name
            ):
                raise ValueError("Bundle checksum mismatch")
        reviewed = json.loads(archive.read("reviewed.json"))
        if (
            hashlib.sha256(archive.read("snapshot.png")).hexdigest()
            != reviewed["image_sha256"]
        ):
            raise ValueError("Bundle PNG differs from reviewed source")
        structure = json.loads(archive.read("structure.sdmx.json"))
        data = json.loads(archive.read("data.sdmx.json"))
        validate_snapshot_messages(reviewed, structure, data)
        return {
            "datasets": len(data["data"]["dataSets"]),
            "observations": len(reviewed["data"]["observations"]),
            "image_sha256": reviewed["image_sha256"],
        }
