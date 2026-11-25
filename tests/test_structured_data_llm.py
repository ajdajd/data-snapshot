"""Exercise the independent OpenRouter path offline, including failure evidence."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import fitz
import pytest
from pydantic import ValidationError

from data_snapshot.structured_data_extraction.llm import run_extraction
from data_snapshot.structured_data_extraction.statistical import (
    DraftDSD,
    extraction_model,
    statistical_messages,
)

PACKAGE = Path(__file__).parents[1] / "src/data_snapshot/structured_data_extraction"


@pytest.fixture(autouse=True)
def offline_spending(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep cost tests isolated and prohibit live pricing/network lookups."""
    from data_snapshot.structured_data_extraction import llm

    monkeypatch.setattr(llm, "_DEFAULT_LEDGER", tmp_path / "spend.jsonl")
    monkeypatch.setattr(
        llm,
        "quote_request",
        lambda *args: {
            "allowance_usd": "0.10",
            "provider_max_price": {
                "prompt": 0.5,
                "completion": 1.8,
                "image": 0,
                "request": 0,
            },
        },
    )


@pytest.fixture
def dsd() -> DraftDSD:
    """Load the bundled experimental numerical-observation draft."""
    return DraftDSD.model_validate_json(
        (PACKAGE / "profiles/snapshot_indicators.json").read_text()
    )


@pytest.fixture
def payload(dsd: DraftDSD) -> dict:
    """Use manually transcribed income values, with explicit unsupported context."""
    dimensions = {c.id: None for c in dsd.dimensions}
    dimensions.update(
        INDICATOR="Income", CATEGORY="Agriculture", STATISTICAL_OPERATION="Mean"
    )
    row = {
        "dimensions": dimensions,
        "attributes": {c.id: None for c in dsd.attributes},
        "value": 5930,
        "evidence": {
            "raw_text": "5930",
            "location": "Agriculture row, Mean column",
            "method": "printed",
            "note": None,
        },
    }
    return {
        "status": "complete",
        "not_extracted": [],
        "notes": None,
        "datasets": [{"id": "D1", "title": "Income", "observations": [row]}],
    }


@pytest.fixture
def image(tmp_path: Path) -> Path:
    """Write a valid tiny PNG without downloading or loading extraction models."""
    path = tmp_path / "sensitive_filename_not_evidence.png"
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 8, 8), False)
    pixmap.clear_with(255)
    path.write_bytes(pixmap.tobytes("png"))
    return path


def fake_client(payload: dict | str, status: str = "completed") -> SimpleNamespace:
    """Build an injected Responses endpoint, retaining the actual request."""
    calls = []
    text = json.dumps(payload) if isinstance(payload, dict) else payload
    raw = {
        "id": "offline_response",
        "status": status,
        "usage": {"input_tokens": 123, "output_tokens": 45, "cost": 0.001},
        "incomplete_details": (
            {"reason": "max_output_tokens"} if status == "incomplete" else None
        ),
        "output": [
            {"type": "message", "content": [{"type": "output_text", "text": text}]}
        ],
    }

    def create(**kwargs: object) -> SimpleNamespace:
        calls.append(kwargs)
        return SimpleNamespace(output_text=text, model_dump=lambda **_: raw)

    return SimpleNamespace(responses=SimpleNamespace(create=create), calls=calls)


def test_default_is_offline_and_never_loads_a_key(
    tmp_path: Path, image: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Require a deliberate opt-in before even loading dotenv or creating a client."""
    import dotenv
    import openai

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Offline preparation touched API setup")

    monkeypatch.setattr(dotenv, "load_dotenv", forbidden)
    monkeypatch.setattr(openai, "OpenAI", forbidden)
    output = tmp_path / "run"
    report = run_extraction(image, output)
    assert report["status"] == "prepared" and report["api_attempts"] == 0
    preview = json.loads((output / "request.preview.json").read_text())
    assert image.name not in json.dumps(preview)
    assert "base64," not in json.dumps(preview)
    assert preview["extra_body"]["provider"]["require_parameters"]
    assert preview["text"]["format"]["strict"]
    assert (output / "dsd.json").exists()
    assert not (output / "response.json").exists()


def test_explicit_execution_preserves_evidence_and_resolves_indexes(
    tmp_path: Path, image: Path, payload: dict
) -> None:
    """Check the full request/response-to-SDMX path using an offline fake only."""
    client = fake_client(payload)
    output = tmp_path / "run"
    report = run_extraction(image, output, execute=True, client=client)
    assert report["status"] == "complete", report
    assert len(client.calls) == 1
    request = client.calls[0]
    assert request["timeout"] == 900
    assert request["input"][1]["content"][1]["image_url"].startswith(
        "data:image/png;base64,"
    )
    assert image.name not in request["input"][1]["content"][0]["text"]
    assert report["usage"]["output_tokens"] == 45
    assert report["spending"]["running_total_usd"] == "0.001"
    assert request["extra_body"]["provider"]["allow_fallbacks"] is False
    assert (output / "raw_output.txt").read_text() == json.dumps(payload)
    data = json.loads((output / "data.sdmx.json").read_text())["data"]
    structure = data["structures"][0]
    key, values = next(iter(data["dataSets"][0]["observations"].items()))
    restored = {
        d["id"]: d["values"][int(index)]["value"]
        for d, index in zip(structure["dimensions"]["observation"], key.split(":"))
    }
    assert restored["CATEGORY"] == "Agriculture"
    assert restored["REPORTING_PERIOD"] == "_UNKNOWN"
    assert values[0] == 5930
    attrs = structure["attributes"]["observation"]
    restored_attributes = {
        a["id"]: a["values"][index]["value"] if index is not None else None
        for a, index in zip(attrs, values[1:])
    }
    assert restored_attributes["EVIDENCE_TEXT"] == "5930"
    assert restored_attributes["UNIT_MULT"] is None


@pytest.mark.parametrize(
    "status,text",
    [
        ("incomplete", "{}"),
        ("failed", "{}"),
        ("completed", ""),
        ("completed", "invalid json"),
        ("completed", '{"unexpected":true}'),
    ],
)
def test_failures_keep_raw_response_without_sdmx(
    tmp_path: Path, image: Path, status: str, text: str
) -> None:
    """Reject truncation, refusal/empty text and invalid output without repair calls."""
    output = tmp_path / "run"
    client = fake_client(text, status)
    report = run_extraction(image, output, execute=True, client=client)
    assert report["status"] == "failed"
    assert len(client.calls) == 1
    assert (output / "response.json").exists()
    assert not (output / "data.sdmx.json").exists()
    assert report["error_type"]
    assert report["spending"]["call_cost_usd"] == "0.001"


@pytest.mark.parametrize(
    "damage",
    [
        "duplicate",
        "extra_dimension",
        "missing_dimension",
        "string_number",
        "boolean_number",
        "nan",
        "blank_label",
        "no_evidence",
        "estimate_without_note",
        "bounds",
        "confidence",
        "status",
    ],
)
def test_structural_and_semantic_validation(
    dsd: DraftDSD, payload: dict, damage: str
) -> None:
    """Reject silent merges, unknown fields and unsupported evidence claims."""
    row = payload["datasets"][0]["observations"][0]
    if damage == "duplicate":
        payload["datasets"][0]["observations"].append(copy.deepcopy(row))
    elif damage == "extra_dimension":
        row["dimensions"]["NEW_AXIS"] = "unreviewed"
    elif damage == "missing_dimension":
        del row["dimensions"]["AGE"]
    elif damage == "string_number":
        row["value"] = "5930"
    elif damage == "boolean_number":
        row["value"] = True
    elif damage == "nan":
        row["value"] = float("nan")
    elif damage == "blank_label":
        row["dimensions"]["CATEGORY"] = " "
    elif damage == "no_evidence":
        row["evidence"]["raw_text"] = None
    elif damage == "estimate_without_note":
        row["evidence"]["method"] = "estimated"
    elif damage == "bounds":
        row["attributes"].update(LOWER_BOUND=10, UPPER_BOUND=1)
    elif damage == "confidence":
        row["attributes"]["CONFIDENCE_LEVEL"] = 101
    else:
        payload["status"] = "partial"
    with pytest.raises(ValidationError):
        extraction_model(dsd).model_validate(payload)


def test_partial_multi_dataset_and_numeric_attributes(
    dsd: DraftDSD, payload: dict
) -> None:
    """Allow distinct components while preserving typed bounds and missing values."""
    second = copy.deepcopy(payload["datasets"][0])
    second["id"] = "D2"
    row = second["observations"][0]
    row.update(value=0)
    row["attributes"].update(
        LOWER_BOUND=-1, UPPER_BOUND=1, CONFIDENCE_LEVEL=95, UNIT_MULT=3
    )
    row["evidence"].update(
        raw_text=None, method="estimated", note="Approximate digitization"
    )
    payload["datasets"].append(second)
    payload.update(
        status="partial",
        not_extracted=[
            {"location": "Map inset", "reason": "Geometry is outside numeric scope"}
        ],
    )
    result = extraction_model(dsd).model_validate(payload)
    _, message = statistical_messages(dsd, result)
    assert len(message["data"]["dataSets"]) == 2
    annotations = message["data"]["structures"][0]["annotations"]
    assert message["data"]["dataSets"][1]["annotations"] == [1]
    assert annotations[1]["id"] == "D2" and annotations[1]["title"] == "Income"
    assert json.loads(annotations[1]["text"])["extraction_status"] == "partial"
    assert next(iter(message["data"]["dataSets"][1]["observations"].values()))[0] == 0


def test_unsupported_is_explicit_and_has_no_sdmx(tmp_path: Path, image: Path) -> None:
    """Do not fabricate an observation dataset for a context-only map."""
    payload = {
        "status": "unsupported",
        "datasets": [],
        "not_extracted": [
            {
                "location": "Entire image",
                "reason": "Context map without numerical observations",
            }
        ],
        "notes": None,
    }
    output = tmp_path / "run"
    report = run_extraction(image, output, execute=True, client=fake_client(payload))
    assert report["status"] == "unsupported"
    assert (output / "observations.json").exists()
    assert not (output / "data.sdmx.json").exists()


def test_bad_config_input_and_overwrite_fail_before_any_call(
    tmp_path: Path, image: Path, payload: dict
) -> None:
    """Keep evidence, request format and run folders under pipeline control."""
    client = fake_client(payload)
    output = tmp_path / "run"
    output.mkdir()
    with pytest.raises(FileExistsError):
        run_extraction(image, output, execute=True, client=client)
    config = json.loads((PACKAGE / "config/openrouter.json").read_text())
    config["input"] = "Replace image evidence"
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    with pytest.raises(ValidationError):
        run_extraction(
            image,
            tmp_path / "bad_config",
            config_path=config_path,
            execute=True,
            client=client,
        )
    image.write_bytes(b"not a png")
    with pytest.raises(ValueError, match="Only PNG"):
        run_extraction(image, tmp_path / "bad_image", execute=True, client=client)
    assert not client.calls


def test_invalid_dsd_is_rejected_before_request_preparation(dsd: DraftDSD) -> None:
    """Keep semantic numeric attributes typed correctly before any paid call."""
    definition = dsd.model_dump()
    definition["attributes"][0]["data_type"] = "String"
    with pytest.raises(ValidationError, match="UNIT_MULT requires Integer"):
        DraftDSD.model_validate(definition)
    definition = dsd.model_dump()
    definition["dimensions"][0]["id"] = "TIME_PERIOD"
    with pytest.raises(ValidationError, match="non-reserved"):
        DraftDSD.model_validate(definition)


def test_budget_blocks_call_before_generation(
    tmp_path: Path, image: Path, payload: dict
) -> None:
    """Persist spending across runs and refuse calls that cannot fit the cap."""
    from data_snapshot.structured_data_extraction.spending import record_spending

    ledger = tmp_path / "spend.jsonl"
    record_spending(ledger, "old_run", "previous_batch", "model", "4.99", "reserve")
    record_spending(ledger, "old_run", "previous_batch", "model", "4.99", "settle")
    client = fake_client(payload)
    report = run_extraction(image, tmp_path / "blocked", execute=True, client=client)
    assert report["status"] == "failed" and report["api_attempts"] == 0
    assert "$5 budget would be exceeded" in report["error"]
    assert not client.calls
