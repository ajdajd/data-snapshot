"""Check reviewed SDMX bundles independently of live LLM actions."""

import copy
import json

import pytest

from data_snapshot.structured_data_extraction.sdmx_export import (
    snapshot_messages,
    validate_snapshot_messages,
)
from data_snapshot.structured_data_reviewer import examples


def _reviewed(case: dict) -> dict:
    return {
        "model": copy.deepcopy(case["model"]),
        "data": copy.deepcopy(case["data"]),
        "image_sha256": "abc",
        "model_sha256": "def",
        "model_revision": 1,
        "data_origin": "hand-authored test",
    }


@pytest.mark.parametrize("sample", ["income", "financing", "education"])
def test_examples_round_trip_with_codelists_and_scoped_attributes(sample: str) -> None:
    """Retain printed/missing/zero values and context without adding units or dates."""
    payload = _reviewed(examples.load_examples()[sample])
    structure, data = snapshot_messages(payload)
    validate_snapshot_messages(payload, structure, data)
    assert structure["data"]["codelists"]
    assert sum(len(d["observations"]) for d in data["data"]["dataSets"]) == len(
        payload["data"]["observations"]
    )
    assert "TIME_PERIOD" not in json.dumps(structure)


def test_text_open_and_missing_keys_scalar_and_bounds() -> None:
    """Support all value/key cases without coercing text to numeric missing values."""
    base = _reviewed(examples.load_examples()["financing"])
    component = base["model"]["components"][0]
    component["fields"][0]["categories"] = []
    component["results"][0]["value_type"] = "text"
    base["model"]["relationships"] = []
    for row in base["data"]["observations"]:
        row["value"] = "Sí"
    base["data"]["observations"][0]["dimensions"]["f1"] = None
    s, d = snapshot_messages(base)
    assert (
        d["data"]["structures"][0]["measures"]["observation"][0]["format"]["dataType"]
        == "String"
    )
    scalar = _reviewed(examples.load_examples()["income"])
    c = scalar["model"]["components"][0]
    c["fields"] = []
    c["extraction_policy"] = "allow_estimates"
    scalar["model"]["relationships"] = []
    scalar["data"]["observations"] = [scalar["data"]["observations"][0]]
    scalar["data"]["observations"][0]["dimensions"] = {}
    scalar["data"]["observations"][0]["bounds"] = {
        "lower": 5000,
        "upper": 6000,
        "evidence": {
            "raw_text": None,
            "location": "Plot bounds",
            "method": "estimated",
            "note": "Synthetic estimate",
        },
    }
    s, d = snapshot_messages(scalar)
    assert (
        d["data"]["structures"][0]["dimensions"]["observation"][0]["id"]
        == "SNAPSHOT_RECORD"
    )


def test_empty_unsupported_output_keeps_definitions_and_omissions() -> None:
    """Do not invent an observation merely to populate a valid SDMX dataset."""
    p = _reviewed(examples.load_examples()["financing"])
    p["data"].update(
        status="unsupported",
        observations=[],
        omissions=[{"location": "plot", "reason": "Nothing readable"}],
    )
    s, d = snapshot_messages(p)
    assert d["data"]["dataSets"][0]["observations"] == {}
    assert "Nothing readable" in json.dumps(s)


@pytest.mark.parametrize(
    "damage",
    ["value", "reference", "concept", "code", "attribute", "measure", "missing_row"],
)
def test_changed_messages_fail_round_trip_or_references(damage: str) -> None:
    """Schema-valid changes must still fail source/referential consistency checks."""
    p = _reviewed(examples.load_examples()["financing"])
    s, d = snapshot_messages(p)
    dataset = d["data"]["dataSets"][0]
    key = next(iter(dataset["observations"]))
    if damage == "value":
        dataset["observations"][key][0] = 999
    elif damage == "reference":
        d["data"]["structures"][0]["links"][0][
            "urn"
        ] = "urn:sdmx:org.sdmx.infomodel.datastructure.DataStructure=LOCAL:MISSING(1.0.0)"
    elif damage == "concept":
        s["data"]["conceptSchemes"][0]["concepts"].pop()
    elif damage == "code":
        s["data"]["codelists"][0]["codes"].pop()
    elif damage == "attribute":
        dataset["observations"][key][-1] = 99999
    elif damage == "measure":
        s["data"]["dataStructures"][0]["dataStructureComponents"]["measureList"][
            "measures"
        ][0]["localRepresentation"]["format"]["dataType"] = "String"
        d["data"]["structures"][0]["measures"]["observation"][0]["format"][
            "dataType"
        ] = "String"
    else:
        del dataset["observations"][key]
    with pytest.raises(ValueError):
        validate_snapshot_messages(p, s, d)
