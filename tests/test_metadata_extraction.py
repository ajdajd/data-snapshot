"""Tests for the snapshot metadata extraction pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from data_snapshot.metadata_extraction import build_openai_schema, extract_metadata


class FakeResponses:
    """Record a Responses API request and return a fixed response."""

    def __init__(self, response: object) -> None:
        self.response = response
        self.kwargs: dict[str, object] | None = None

    def create(self, **kwargs: object) -> object:
        """Record the request and return the configured response."""
        self.kwargs = kwargs
        return self.response


def _write_field_map(path: Path) -> None:
    """Write a minimal canonical metadata field map."""
    path.write_text(
        json.dumps(
            {
                "$schema_version": "1.1",
                "title": {
                    "type": "string",
                    "multiple": False,
                    "definition": "Snapshot title.",
                },
                "labels": {
                    "type": "array[string]",
                    "multiple": True,
                    "definition": "Visible category labels.",
                },
            }
        ),
        encoding="utf-8",
    )


def test_build_openai_schema_writes_nullable_strict_schema(tmp_path: Path) -> None:
    """The builder converts a canonical field map into strict output schema."""
    field_map_path = tmp_path / "field_map.json"
    output_schema_path = tmp_path / "openai_schema.json"
    _write_field_map(field_map_path)

    schema = build_openai_schema(field_map_path, output_schema_path)

    assert output_schema_path.exists()
    assert schema["strict"] is True
    assert schema["schema"]["required"] == ["title", "labels"]
    assert schema["schema"]["properties"]["title"]["type"] == ["string", "null"]
    assert schema["schema"]["properties"]["labels"]["type"] == ["array", "null"]


def test_extract_metadata_writes_output_and_log_with_source(tmp_path: Path) -> None:
    """A structured response is written to both JSONL files with its source."""
    field_map_path = tmp_path / "field_map.json"
    schema_path = tmp_path / "openai_schema.json"
    _write_field_map(field_map_path)
    build_openai_schema(field_map_path, schema_path)
    image_path = tmp_path / "snapshot.png"
    image_path.write_bytes(b"png-data")
    config_path = tmp_path / "config.json"
    config_path.write_text('{"model": "gpt-5.4-mini"}', encoding="utf-8")
    response = SimpleNamespace(
        output_text='{"title": "Coverage", "labels": ["Niger"]}',
        usage=SimpleNamespace(input_tokens=12, output_tokens=4, total_tokens=16),
    )
    fake_responses = FakeResponses(response)
    client = SimpleNamespace(responses=fake_responses)
    output_path = tmp_path / "metadata.jsonl"
    log_path = tmp_path / "calls.jsonl"

    result = extract_metadata(
        image_path,
        schema_path,
        output_path,
        log_path,
        config_path,
        source="unhcr",
        client=client,
    )

    assert result.error is None
    assert result.metadata == {"title": "Coverage", "labels": ["Niger"]}
    assert fake_responses.kwargs is not None
    assert fake_responses.kwargs["model"] == "gpt-5.4-mini"
    user_content = fake_responses.kwargs["input"][1]["content"][0]["text"]
    assert '"title"' in user_content
    output = json.loads(output_path.read_text(encoding="utf-8"))
    log = json.loads(log_path.read_text(encoding="utf-8"))
    assert output["source"] == log["source"] == "unhcr"
    assert log["usage"]["total_tokens"] == 16


def test_extract_metadata_logs_api_errors_without_output(tmp_path: Path) -> None:
    """An API failure is logged and does not produce a metadata record."""
    field_map_path = tmp_path / "field_map.json"
    schema_path = tmp_path / "openai_schema.json"
    _write_field_map(field_map_path)
    build_openai_schema(field_map_path, schema_path)
    image_path = tmp_path / "snapshot.png"
    image_path.write_bytes(b"png-data")
    config_path = tmp_path / "config.json"
    config_path.write_text('{"model": "gpt-5.4-mini"}', encoding="utf-8")
    fake_responses = FakeResponses(RuntimeError("rate limited"))
    fake_responses.create = lambda **_: (_ for _ in ()).throw(
        RuntimeError("rate limited")
    )
    client = SimpleNamespace(responses=fake_responses)
    output_path = tmp_path / "metadata.jsonl"
    log_path = tmp_path / "calls.jsonl"

    result = extract_metadata(
        image_path,
        schema_path,
        output_path,
        log_path,
        config_path,
        client=client,
    )

    assert result.metadata is None
    assert result.error == "rate limited"
    assert not output_path.exists()
    assert json.loads(log_path.read_text(encoding="utf-8"))["error"] == "rate limited"
