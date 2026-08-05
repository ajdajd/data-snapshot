"""Call the OpenAI Responses API for snapshot metadata extraction."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_PROMPT_DIR = Path(__file__).parent / "prompts"
_RESERVED_CONFIG_FIELDS = {"input", "model", "text"}


@dataclass(frozen=True)
class ExtractionResult:
    """Outcome of a single metadata extraction request.

    Attributes
    ----------
    metadata : dict[str, Any] | None
        Extracted metadata, or ``None`` when extraction failed.
    model : str | None
        Model requested for the API call, if configuration loaded successfully.
    elapsed_seconds : float | None
        API-call duration in seconds, or ``None`` if no call was attempted.
    usage : dict[str, Any] | None
        Serializable token-usage data returned by the API.
    error : str | None
        Error message, or ``None`` on success.
    """

    metadata: dict[str, Any] | None
    model: str | None
    elapsed_seconds: float | None
    usage: dict[str, Any] | None
    error: str | None


def load_extraction_config(config_path: str | Path) -> dict[str, Any]:
    """Load and validate Responses API request settings from JSON.

    Parameters
    ----------
    config_path : str | Path
        Path to a JSON object containing ``model`` and optional request
        settings such as ``temperature``, ``max_output_tokens``, and
        ``reasoning``. Pipeline-owned request fields (``input`` and ``text``)
        are not allowed.

    Returns
    -------
    dict[str, Any]
        Validated request settings ready to pass to ``responses.create``.

    Raises
    ------
    ValueError
        If the file is not a JSON object, lacks a model, or contains an
        a pipeline-owned request field.
    """
    with Path(config_path).open(encoding="utf-8") as file:
        config = json.load(file)
    if not isinstance(config, dict):
        raise ValueError("Extraction config must be a JSON object.")
    reserved = set(config) & _RESERVED_CONFIG_FIELDS - {"model"}
    if reserved:
        raise ValueError(
            f"Extraction config cannot set pipeline-owned keys: {sorted(reserved)}."
        )
    if not isinstance(config.get("model"), str) or not config["model"].strip():
        raise ValueError("Extraction config requires a non-empty 'model' string.")
    return config


def extract_metadata(
    image_path: str | Path,
    openai_schema_path: str | Path,
    output_jsonl_path: str | Path,
    log_jsonl_path: str | Path,
    config_path: str | Path,
    source_document_metadata_path: str | Path | None = None,
    source: str | None = None,
    client: Any | None = None,
) -> ExtractionResult:
    """Extract semantic metadata from one data snapshot image.

    The OpenAI Structured Outputs schema must already exist. Use
    :func:`data_snapshot.metadata_extraction.build_openai_schema` first when
    starting from the canonical metadata field map.

    Parameters
    ----------
    image_path : str | Path
        Path to the data snapshot image.
    openai_schema_path : str | Path
        Path to the generated OpenAI Structured Outputs schema JSON file.
    output_jsonl_path : str | Path
        JSONL file to append successful extracted metadata records to.
    log_jsonl_path : str | Path
        JSONL file to append one record per API call to.
    config_path : str | Path
        Path to the Responses API request configuration JSON file.
    source_document_metadata_path : str | Path | None, optional
        Optional JSON file containing supplementary document metadata.
    source : str | None, optional
        Caller-provided source label written to both JSONL outputs.
    client : Any | None, optional
        OpenAI-compatible client. If omitted, a client is constructed from
        ``OPENAI_API_KEY`` after loading the project ``.env`` file.

    Returns
    -------
    ExtractionResult
        Successful metadata and call details, or a failure result without
        raising for invalid inputs or API errors.
    """
    try:
        config = load_extraction_config(config_path)
        openai_schema = _load_json_object(openai_schema_path, "OpenAI schema")
        document_metadata = (
            _load_json_object(source_document_metadata_path, "Document metadata")
            if source_document_metadata_path is not None
            else None
        )
        system_prompt = (_PROMPT_DIR / "system.md").read_text(encoding="utf-8")
        user_template = (_PROMPT_DIR / "user.md").read_text(encoding="utf-8")
        user_prompt = _render_user_prompt(
            user_template, openai_schema["schema"], document_metadata
        )
        image_url = _image_data_url(image_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return ExtractionResult(None, None, None, None, str(exc))

    model = config.pop("model")
    try:
        api_client = client if client is not None else _create_openai_client()
        started_at = time.perf_counter()
        response = api_client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": user_prompt},
                        {"type": "input_image", "image_url": image_url},
                    ],
                },
            ],
            text={"format": openai_schema},
            **config,
        )
        elapsed_seconds = time.perf_counter() - started_at
        usage = _serialize_usage(getattr(response, "usage", None))
        metadata = json.loads(response.output_text)
    except Exception as exc:
        elapsed_seconds = (
            time.perf_counter() - started_at if "started_at" in locals() else None
        )
        result = ExtractionResult(None, model, elapsed_seconds, None, str(exc))
        _append_log(log_jsonl_path, image_path, source, result)
        return result

    result = ExtractionResult(metadata, model, elapsed_seconds, usage, None)
    _append_jsonl(
        output_jsonl_path,
        {
            "image_name": Path(image_path).name,
            "image_path": str(image_path),
            "source": source,
            "metadata": metadata,
        },
    )
    _append_log(log_jsonl_path, image_path, source, result)
    return result


def _create_openai_client() -> Any:
    """Create an OpenAI client from the project environment."""
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def _image_data_url(image_path: str | Path) -> str:
    """Encode a local image as a base64 data URL."""
    path = Path(image_path)
    mime_type, _ = mimetypes.guess_type(path.name)
    if not mime_type or not mime_type.startswith("image/"):
        raise ValueError(f"Unsupported image file: {path}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _load_json_object(path: str | Path, label: str) -> dict[str, Any]:
    """Load a JSON object from a path."""
    with Path(path).open(encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object.")
    return value


def _render_user_prompt(
    template: str,
    metadata_schema: dict[str, Any],
    document_metadata: dict[str, Any] | None,
) -> str:
    """Render the generated schema and optional document metadata into a prompt."""
    rendered = template.replace(
        "{{METADATA_SCHEMA}}", json.dumps(metadata_schema, ensure_ascii=False, indent=2)
    )
    section_start = "{{#if DOCUMENT_METADATA}}"
    section_end = "{{/if}}"
    if document_metadata is None:
        start = rendered.find(section_start)
        end = rendered.find(section_end)
        if start != -1 and end != -1:
            return rendered[:start] + rendered[end + len(section_end) :]
        return rendered
    rendered = rendered.replace(section_start, "").replace(section_end, "")
    return rendered.replace(
        "{{DOCUMENT_METADATA}}",
        json.dumps(document_metadata, ensure_ascii=False, indent=2),
    )


def _serialize_usage(usage: Any) -> dict[str, Any] | None:
    """Convert an SDK usage object to JSON-compatible data."""
    if usage is None:
        return None
    if hasattr(usage, "model_dump"):
        return usage.model_dump(mode="json")
    if isinstance(usage, dict):
        return usage
    return {
        key: getattr(usage, key)
        for key in ("input_tokens", "output_tokens", "total_tokens")
        if hasattr(usage, key)
    }


def _append_log(
    log_jsonl_path: str | Path,
    image_path: str | Path,
    source: str | None,
    result: ExtractionResult,
) -> None:
    """Append one API-call log record."""
    _append_jsonl(
        log_jsonl_path,
        {
            "image_name": Path(image_path).name,
            "source": source,
            "model": result.model,
            "elapsed_seconds": result.elapsed_seconds,
            "usage": result.usage,
            "error": result.error,
        },
    )


def _append_jsonl(path: str | Path, record: dict[str, Any]) -> None:
    """Append one JSON object as a line, creating parent directories."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
