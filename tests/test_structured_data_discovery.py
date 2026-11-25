"""Check independent discovery and shared accounting without network access."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import fitz
import pytest

from data_snapshot.structured_data_extraction import llm
from data_snapshot.structured_data_extraction.discovery import run_discovery


@pytest.fixture
def image(tmp_path: Path) -> Path:
    """Create PNG evidence whose filename must never become model context."""
    path = tmp_path / "country_and_year_not_evidence.png"
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 8, 8), False)
    pixmap.clear_with(255)
    path.write_bytes(pixmap.tobytes("png"))
    return path


@pytest.fixture
def record() -> dict:
    """Describe a synthetic artifact with an unrestricted candidate name/function."""
    return {
        "analytical_units": [
            {
                "id": "u1",
                "description": "Synthetic analytical unit",
                "location": "whole image",
                "requirements": [
                    {
                        "id": "r1",
                        "candidate_name": "Unusual artifact-specific concept",
                        "description": "Synthetic requirement",
                        "function_in_this_unit": "A freely described local function",
                        "observed_examples": ["Synthetic label"],
                        "why_needed": "Preserves interpretation",
                        "evidence": [{"text": None, "location": "top left"}],
                        "interpretation_note": None,
                    }
                ],
                "observation_examples": [
                    {
                        "source_value": "37",
                        "location": "centre",
                        "context_requirement_ids": ["r1"],
                        "interpretation": None,
                    }
                ],
            }
        ],
        "relationships": [
            {
                "related_ids": ["u1", "r1"],
                "description": "Synthetic connection",
                "evidence": [{"text": None, "location": "whole image"}],
                "interpretation_note": None,
            }
        ],
        "ambiguities": [],
        "other_analytical_content": [],
    }


@pytest.fixture(autouse=True)
def offline_spending(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate accounting and prevent live pricing calls."""
    monkeypatch.setattr(llm, "_DEFAULT_LEDGER", tmp_path / "spend.jsonl")
    monkeypatch.setattr(
        llm,
        "quote_request",
        lambda *args: {"allowance_usd": "0.10", "provider_max_price": {}},
    )


def fake_client(record: dict) -> SimpleNamespace:
    """Return one billed offline response and retain submitted requests."""
    calls = []
    text = json.dumps(record)
    raw = {
        "id": "offline_discovery",
        "status": "completed",
        "usage": {"input_tokens": 100, "output_tokens": 200, "cost": 0.001},
    }

    def create(**kwargs: object) -> SimpleNamespace:
        calls.append(kwargs)
        return SimpleNamespace(output_text=text, model_dump=lambda **_: raw)

    return SimpleNamespace(responses=SimpleNamespace(create=create), calls=calls)


def test_offline_discovery_excludes_dsd_and_file_context(
    tmp_path: Path, image: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep discovery independent and offline without constructing a client."""
    import dotenv
    import openai

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Offline discovery initialized API access")

    monkeypatch.setattr(dotenv, "load_dotenv", forbidden)
    monkeypatch.setattr(openai, "OpenAI", forbidden)
    output = tmp_path / "prepared"
    report = run_discovery(image, output)
    assert report["status"] == "prepared" and report["api_attempts"] == 0
    preview = (output / "request.preview.json").read_text()
    assert image.name not in preview and "base64," not in preview
    assert "SNAPSHOT_OBSERVATIONS" not in preview
    assert "STATISTICAL_OPERATION" not in preview
    assert "dsd" not in report
    assert (output / "discovery.schema.json").exists()
    assert not (output / "dsd.json").exists()


def test_discovery_preserves_raw_output_and_shared_cost(
    tmp_path: Path, image: Path, record: dict
) -> None:
    """Validate a record and settle its charge without producing SDMX."""
    output = tmp_path / "success"
    client = fake_client(record)
    report = run_discovery(image, output, execute=True, client=client, batch_id="D0")
    assert report["status"] == "discovered" and report["requirements"] == 1
    assert len(client.calls) == 1
    assert json.loads((output / "discovery.json").read_text()) == record
    assert (output / "raw_output.txt").exists()
    assert report["spending"]["running_total_usd"] == "0.001"
    assert not (output / "data.sdmx.json").exists()
    with pytest.raises(FileExistsError):
        run_discovery(image, output, execute=True, client=client)
    assert len(client.calls) == 1


@pytest.mark.parametrize(
    "damage",
    [
        "duplicate",
        "unknown_context",
        "unknown_relation",
        "self_relation",
        "no_evidence",
        "extra",
    ],
)
def test_invalid_discovery_is_billed_and_retained_without_repair(
    tmp_path: Path, image: Path, record: dict, damage: str
) -> None:
    """Reject structural or reference errors after retaining the paid response."""
    unit = record["analytical_units"][0]
    if damage == "duplicate":
        unit["requirements"].append(copy.deepcopy(unit["requirements"][0]))
    elif damage == "unknown_context":
        unit["observation_examples"][0]["context_requirement_ids"] = ["r99"]
    elif damage == "unknown_relation":
        record["relationships"][0]["related_ids"] = ["u1", "r99"]
    elif damage == "self_relation":
        record["relationships"][0]["related_ids"] = ["r1", "r1"]
    elif damage == "no_evidence":
        unit["requirements"][0]["evidence"] = []
    else:
        record["fixed_dsd"] = {}
    client = fake_client(record)
    output = tmp_path / "failed"
    report = run_discovery(image, output, execute=True, client=client)
    assert report["status"] == "failed"
    assert report["spending"]["call_cost_usd"] == "0.001"
    assert len(client.calls) == 1
    assert (output / "raw_output.txt").exists()
    assert not (output / "discovery.json").exists()
