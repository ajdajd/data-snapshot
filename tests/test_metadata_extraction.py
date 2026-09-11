"""Tests for the Schema v1.3 single-snapshot metadata extractor."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from data_snapshot.metadata_extraction import (
    extract_metadata,
    load_extraction_config,
)
from data_snapshot.metadata_schema import DataSnapshotMetadata


class FakeResponses:
    """Record Responses API requests and return a configured result."""

    def __init__(self, response: object | Exception) -> None:
        self.response = response
        self.request: dict[str, object] | None = None

    def create(self, **kwargs: object) -> object:
        """Record a request and return or raise the configured result."""
        self.request = kwargs
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def _write_image(path: Path) -> None:
    """Write a minimal file accepted as a PNG input by the extractor."""
    path.write_bytes(b"png-data")


def _write_config(path: Path, **overrides: object) -> None:
    """Write a minimal extraction configuration with optional overrides."""
    config: dict[str, object] = {
        "model": "gpt-5.6-luna",
        "service_tier": "flex",
        "prompt_cache_key": "metadata-extraction-v1-3",
    }
    config.update(overrides)
    path.write_text(json.dumps(config), encoding="utf-8")


def test_default_config_uses_luna_flex_and_prompt_caching() -> None:
    """The package defaults select the agreed cost-saving API settings."""
    config = load_extraction_config()

    assert config["model"] == "gpt-5.6-luna"
    assert config["service_tier"] == "flex"
    assert config["prompt_cache_key"] == "metadata-extraction-v1-3"


def test_extract_metadata_uses_pydantic_and_snapshot_only(tmp_path: Path) -> None:
    """A successful request uses the canonical model and only image evidence."""
    image_path = tmp_path / "secret_source_figure_001.png"
    config_path = tmp_path / "config.json"
    _write_image(image_path)
    _write_config(config_path)
    metadata = DataSnapshotMetadata(title="Displacement by year")
    response = SimpleNamespace(
        id="resp_test",
        status="completed",
        output_text=metadata.model_dump_json(),
        usage=SimpleNamespace(input_tokens=12, output_tokens=4, total_tokens=16),
    )
    responses = FakeResponses(response)

    result = extract_metadata(
        image_path,
        config_path=config_path,
        client=SimpleNamespace(responses=responses),
    )

    assert result.metadata == metadata
    assert result.error is None
    assert result.response_id == "resp_test"
    assert result.usage == {
        "input_tokens": 12,
        "output_tokens": 4,
        "total_tokens": 16,
    }
    assert responses.request is not None
    assert responses.request["model"] == "gpt-5.6-luna"
    response_format = responses.request["text"]["format"]
    assert response_format["strict"] is True
    output_schema = response_format["schema"]
    serialized_schema = json.dumps(output_schema)
    for unsupported in ("allOf", "else", "if", "not", "then"):
        assert f'"{unsupported}"' not in serialized_schema
    assert '"format": "uri"' not in serialized_schema
    assert "Validation rules:" in serialized_schema
    assert output_schema["required"] == list(output_schema["properties"])
    pending: list[object] = [output_schema]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            assert "$ref" not in value or len(value) == 1
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    assert responses.request["service_tier"] == "flex"
    assert responses.request["prompt_cache_key"] == "metadata-extraction-v1-3"
    request_input = responses.request["input"]
    prompt_text = " ".join(
        item["text"]
        for message in request_input
        for item in message["content"]
        if item["type"] == "input_text"
    )
    assert image_path.name not in prompt_text
    assert request_input[1]["content"][1]["image_url"].startswith(
        "data:image/png;base64,"
    )


def test_extract_metadata_returns_api_failure_details(tmp_path: Path) -> None:
    """An API exception becomes a structured result for later JSONL logging."""
    image_path = tmp_path / "snapshot.png"
    config_path = tmp_path / "config.json"
    _write_image(image_path)
    _write_config(config_path)
    responses = FakeResponses(RuntimeError("rate limited"))

    result = extract_metadata(
        image_path,
        config_path=config_path,
        client=SimpleNamespace(responses=responses),
    )

    assert result.metadata is None
    assert result.model == "gpt-5.6-luna"
    assert result.error_type == "RuntimeError"
    assert result.error == "rate limited"
    assert result.elapsed_seconds is not None


def test_extract_metadata_rejects_missing_structured_output(tmp_path: Path) -> None:
    """An incomplete response is returned as a retryable extraction failure."""
    image_path = tmp_path / "snapshot.png"
    config_path = tmp_path / "config.json"
    _write_image(image_path)
    _write_config(config_path)
    response = SimpleNamespace(
        id="resp_incomplete",
        status="incomplete",
        output_text=None,
        usage=None,
    )

    result = extract_metadata(
        image_path,
        config_path=config_path,
        client=SimpleNamespace(responses=FakeResponses(response)),
    )

    assert result.metadata is None
    assert result.response_id == "resp_incomplete"
    assert result.error_type == "ValueError"
    assert result.error == "Structured output was missing or incomplete."


def test_config_rejects_pipeline_owned_fields(tmp_path: Path) -> None:
    """Config files cannot replace prompts, image input, or output contracts."""
    config_path = tmp_path / "config.json"
    _write_config(config_path, input=[])

    try:
        load_extraction_config(config_path)
    except ValueError as exc:
        assert "'input'" in str(exc)
    else:
        raise AssertionError("Pipeline-owned input config was accepted.")
