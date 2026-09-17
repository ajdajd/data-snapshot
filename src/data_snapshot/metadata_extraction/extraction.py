"""Extract Schema v1.3 metadata from one data snapshot image."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import time
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Literal

from data_snapshot.metadata_schema import DataSnapshotMetadata


_PACKAGE_DIR = Path(__file__).parent
_DEFAULT_CONFIG_PATH = _PACKAGE_DIR / "config" / "default.json"
_PROMPT_DIR = _PACKAGE_DIR / "prompts"
_MODEL_FACING_SCHEMA_SECTION_PLACEHOLDER = "{{MODEL_FACING_SCHEMA_SECTION}}"
_COMPLETENESS_GUIDANCE_PLACEHOLDER = "{{COMPLETENESS_GUIDANCE}}"
_PRODUCTION_COMPLETENESS_GUIDANCE = (
    "Before returning, re-scan the image against the entire schema and correct any "
    "omissions of fields supported by visible evidence. Leave every unsupported "
    "field null."
)
_PIPELINE_OWNED_CONFIG_FIELDS = {
    "input",
    "instructions",
    "model",
    "stream",
    "text",
    "text_format",
}
_UNSUPPORTED_SCHEMA_KEYWORDS = {
    "$schema",
    "allOf",
    "default",
    "dependentRequired",
    "dependentSchemas",
    "else",
    "examples",
    "if",
    "not",
    "then",
}
_SUPPORTED_STRING_FORMATS = {
    "date",
    "date-time",
    "duration",
    "email",
    "hostname",
    "ipv4",
    "ipv6",
    "time",
    "uuid",
}
_SchemaExampleMode = Literal[
    "none",
    "first",
    "all",
    "normalization",
    "c9_targeted",
]
_SCHEMA_EXAMPLE_MODES = {
    "none",
    "first",
    "all",
    "normalization",
    "c9_targeted",
}
_NORMALIZATION_EXAMPLE_PATHS = {
    ("$defs", "Currency", "properties", "code"),
    ("$defs", "GeographicLocation", "properties", "iso3_code"),
    ("$defs", "Place", "properties", "iso3_code"),
    ("$defs", "Unit", "properties", "code"),
    ("$defs", "Unit", "properties", "multiplier_exponent"),
}
_C9_TARGETED_EXAMPLE_PATHS = {
    ("$defs", "CategoryGroup", "properties", "name"),
    ("$defs", "CategoryGroup", "properties", "categories"),
    ("$defs", "Dimension", "properties", "category_groups"),
    ("$defs", "GeographicLocation", "properties", "name"),
    ("$defs", "Place", "properties", "name"),
}


@dataclass(frozen=True)
class ExtractionResult:
    """Represent the outcome of one metadata extraction request.

    Attributes
    ----------
    metadata : DataSnapshotMetadata | None
        Validated Schema v1.3 metadata, or ``None`` after a failure.
    model : str | None
        Requested model, if the configuration loaded successfully.
    response_id : str | None
        OpenAI response identifier, when available.
    api_status : str | None
        OpenAI response status, when available.
    elapsed_seconds : float | None
        API-call duration, or ``None`` if no call was attempted.
    usage : dict[str, Any] | None
        JSON-compatible token usage returned by the API.
    raw_output : str | None
        Structured output text returned by the API, when available.
    error_type : str | None
        Exception class name after a failure.
    error : str | None
        Error message after a failure.
    """

    metadata: DataSnapshotMetadata | None
    model: str | None
    response_id: str | None
    api_status: str | None
    elapsed_seconds: float | None
    usage: dict[str, Any] | None
    raw_output: str | None
    error_type: str | None
    error: str | None


def load_extraction_config(
    config_path: str | Path = _DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    """Load Responses API settings from a JSON object.

    Parameters
    ----------
    config_path : str | Path, optional
        JSON file containing ``model`` and optional Responses API settings.

    Returns
    -------
    dict[str, Any]
        Validated request settings.

    Raises
    ------
    ValueError
        If the config is not an object, lacks a model, or overrides a field
        owned by the extraction pipeline.
    """
    with Path(config_path).open(encoding="utf-8") as file:
        config = json.load(file)
    if not isinstance(config, dict):
        raise ValueError("Extraction config must be a JSON object.")
    model = config.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("Extraction config requires a non-empty 'model' string.")
    forbidden = (set(config) - {"model"}) & _PIPELINE_OWNED_CONFIG_FIELDS
    if forbidden:
        raise ValueError(
            f"Extraction config cannot set pipeline-owned keys: {sorted(forbidden)}."
        )
    return config


def extract_metadata(
    image_path: str | Path,
    config_path: str | Path = _DEFAULT_CONFIG_PATH,
    client: Any | None = None,
    *,
    user_prompt_addendum: str | None = None,
    system_prompt_addendum: str | None = None,
    completeness_guidance: str | None = _PRODUCTION_COMPLETENESS_GUIDANCE,
    schema_example_mode: _SchemaExampleMode = "none",
    include_schema_reference: bool = False,
) -> ExtractionResult:
    """Extract validated Schema v1.3 metadata from one snapshot image.

    Only the image and package prompts are sent to the model. Filenames,
    directory names, and source-document metadata are not included.

    Parameters
    ----------
    image_path : str | Path
        Path to a supported snapshot image.
    config_path : str | Path, optional
        Responses API configuration. Defaults to the package configuration.
    client : Any | None, optional
        OpenAI-compatible client used for offline tests. A client using
        ``OPENAI_API_KEY`` is created when omitted.
    user_prompt_addendum : str | None, optional
        Additional user-prompt guidance for controlled calibration runs.
    system_prompt_addendum : str | None, optional
        Additional system-prompt guidance for controlled calibration runs.
    completeness_guidance : str | None, optional
        Guidance rendered at the explicit completeness placeholder. Defaults to
        the production re-scan instruction; use ``None`` for historical controls.
    schema_example_mode : {"none", "first", "all", "normalization", "c9_targeted"}, optional
        Whether model-facing schema descriptions include no examples, the
        first example, all examples, or all examples for selected
        normalization fields from the canonical Pydantic schema.
    include_schema_reference : bool, optional
        Whether to render the response schema in the user prompt in addition
        to supplying it as the authoritative Structured Outputs contract.

    Returns
    -------
    ExtractionResult
        Validated metadata and call details, or structured failure details.
    """
    model: str | None = None
    started_at: float | None = None
    response: Any | None = None
    try:
        config = load_extraction_config(config_path)
        model = config.pop("model")
        system_prompt = (_PROMPT_DIR / "system.md").read_text(encoding="utf-8")
        if system_prompt.count(_COMPLETENESS_GUIDANCE_PLACEHOLDER) != 1:
            raise ValueError(
                "The system prompt must contain exactly one completeness placeholder."
            )
        system_prompt = system_prompt.replace(
            _COMPLETENESS_GUIDANCE_PLACEHOLDER,
            completeness_guidance.strip() if completeness_guidance else "",
        )
        if system_prompt_addendum:
            system_prompt = (
                f"{system_prompt.rstrip()}\n\n{system_prompt_addendum.strip()}\n"
            )
        response_format = _response_format(schema_example_mode)
        user_prompt = _production_user_prompt(
            schema_example_mode,
            include_schema_reference,
        )
        if user_prompt_addendum:
            user_prompt = f"{user_prompt.rstrip()}\n\n{user_prompt_addendum.strip()}\n"
        image_url = _image_data_url(image_path)
        api_client = client if client is not None else _create_openai_client()

        started_at = time.perf_counter()
        response = api_client.responses.create(
            model=model,
            text={"format": response_format},
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
            **config,
        )
        elapsed_seconds = time.perf_counter() - started_at
        raw_output = getattr(response, "output_text", None)
        if not isinstance(raw_output, str) or not raw_output:
            raise ValueError("Structured output was missing or incomplete.")
        metadata = DataSnapshotMetadata.model_validate_json(raw_output)
        return ExtractionResult(
            metadata=metadata,
            model=model,
            response_id=getattr(response, "id", None),
            api_status=getattr(response, "status", None),
            elapsed_seconds=elapsed_seconds,
            usage=_serialize_usage(getattr(response, "usage", None)),
            raw_output=raw_output,
            error_type=None,
            error=None,
        )
    except Exception as exc:
        elapsed_seconds = (
            time.perf_counter() - started_at if started_at is not None else None
        )
        return ExtractionResult(
            metadata=None,
            model=model,
            response_id=getattr(response, "id", None),
            api_status=getattr(response, "status", None),
            elapsed_seconds=elapsed_seconds,
            usage=_serialize_usage(getattr(response, "usage", None)),
            raw_output=getattr(response, "output_text", None),
            error_type=type(exc).__name__,
            error=str(exc),
        )


def _image_data_url(image_path: str | Path) -> str:
    """Encode a supported local image as a base64 data URL."""
    path = Path(image_path)
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type not in {"image/gif", "image/jpeg", "image/png", "image/webp"}:
        raise ValueError(f"Unsupported image file: {path}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _openai_compatible_schema(value: Any) -> Any:
    """Remove unsupported keywords from canonical Pydantic JSON Schema data."""
    if isinstance(value, list):
        return [_openai_compatible_schema(item) for item in value]
    if not isinstance(value, dict):
        return value

    validation_rules = value.get("x-validation-rules")
    result: dict[str, Any] = {}
    for key, item in value.items():
        if key in _UNSUPPORTED_SCHEMA_KEYWORDS or key.startswith("x-"):
            continue
        if key == "format" and item not in _SUPPORTED_STRING_FORMATS:
            continue
        if key == "anyOf" and _contains_schema_keyword(item, "not"):
            continue
        result[key] = _openai_compatible_schema(item)

    if isinstance(validation_rules, list) and all(
        isinstance(rule, str) for rule in validation_rules
    ):
        guidance = "Validation rules:\n- " + "\n- ".join(validation_rules)
        description = result.get("description")
        result["description"] = (
            f"{description}\n\n{guidance}" if description else guidance
        )
    properties = result.get("properties")
    if result.get("type") == "object" and isinstance(properties, dict):
        result["required"] = list(properties)
        result["additionalProperties"] = False
    return result


def _append_schema_examples_to_descriptions(
    value: Any,
    mode: Literal["first", "all", "normalization", "c9_targeted"],
    path: tuple[str, ...] = (),
) -> None:
    """Append canonical schema examples to their associated descriptions.

    Parameters
    ----------
    value : Any
        JSON-compatible schema value to transform in place.
    mode : {"first", "all", "normalization", "c9_targeted"}
        Whether to append the first example, the complete examples list, or
        complete examples only for a selected set of fields.
    path : tuple[str, ...], optional
        Location of ``value`` within the root schema.
    """
    if isinstance(value, list):
        for index, item in enumerate(value):
            _append_schema_examples_to_descriptions(item, mode, (*path, str(index)))
        return
    if not isinstance(value, dict):
        return

    examples = value.get("examples")
    if (
        isinstance(examples, list)
        and examples
        and (
            mode not in {"normalization", "c9_targeted"}
            or (mode == "normalization" and path in _NORMALIZATION_EXAMPLE_PATHS)
            or (mode == "c9_targeted" and path in _C9_TARGETED_EXAMPLE_PATHS)
        )
    ):
        selected: Any = examples[0] if mode == "first" else examples
        label = "Example" if mode == "first" else "Examples"
        guidance = f"{label}: {json.dumps(selected, ensure_ascii=False)}"
        description = value.get("description")
        value["description"] = (
            f"{description}\n\n{guidance}" if description else guidance
        )

    for key, item in value.items():
        _append_schema_examples_to_descriptions(item, mode, (*path, key))


def _contains_schema_keyword(value: Any, keyword: str) -> bool:
    """Return whether nested JSON Schema data contain a named keyword."""
    if isinstance(value, dict):
        return keyword in value or any(
            _contains_schema_keyword(item, keyword) for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_schema_keyword(item, keyword) for item in value)
    return False


def _inline_ref_siblings(value: Any, root: dict[str, Any]) -> Any:
    """Inline local references that have sibling schema keywords."""
    if isinstance(value, list):
        return [_inline_ref_siblings(item, root) for item in value]
    if not isinstance(value, dict):
        return value

    ref = value.get("$ref")
    if isinstance(ref, str) and len(value) > 1:
        if not ref.startswith("#/"):
            raise ValueError(f"Unsupported JSON Schema reference: {ref}")
        resolved: Any = root
        for part in ref[2:].split("/"):
            key = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(resolved, dict) or key not in resolved:
                raise ValueError(f"Unresolved JSON Schema reference: {ref}")
            resolved = resolved[key]
        if not isinstance(resolved, dict):
            raise ValueError(f"JSON Schema reference is not an object: {ref}")
        value = {**resolved, **value}
        value.pop("$ref")

    return {key: _inline_ref_siblings(item, root) for key, item in value.items()}


@cache
def _response_format(
    schema_example_mode: _SchemaExampleMode = "none",
) -> dict[str, Any]:
    """Build the strict response format from the canonical Pydantic model."""
    if schema_example_mode not in _SCHEMA_EXAMPLE_MODES:
        raise ValueError(f"Unknown schema example mode: {schema_example_mode}")
    canonical_schema = DataSnapshotMetadata.model_json_schema(mode="validation")
    if schema_example_mode != "none":
        _append_schema_examples_to_descriptions(
            canonical_schema,
            schema_example_mode,
        )
    schema = _openai_compatible_schema(canonical_schema)
    schema = _inline_ref_siblings(schema, schema)
    return {
        "type": "json_schema",
        "name": "data_snapshot_metadata_v1_3",
        "strict": True,
        "schema": schema,
    }


@cache
def _production_user_prompt(
    schema_example_mode: _SchemaExampleMode = "none",
    include_schema_reference: bool = False,
) -> str:
    """Build the production prompt with the model-facing response schema."""
    prompt = (_PROMPT_DIR / "user.md").read_text(encoding="utf-8").rstrip()
    if prompt.count(_MODEL_FACING_SCHEMA_SECTION_PLACEHOLDER) != 1:
        raise ValueError(
            "The user prompt must contain exactly one model-facing schema placeholder."
        )
    schema_section = ""
    if include_schema_reference:
        schema = json.dumps(
            _response_format(schema_example_mode)["schema"],
            ensure_ascii=False,
            indent=2,
        )
        schema_section = (
            "## Model-facing Schema v1.3 reference\n\n"
            "Use this schema as field-level extraction guidance. The API response "
            "format remains the authoritative output contract.\n\n"
            f"```json\n{schema}\n```"
        )
    return (
        prompt.replace(
            _MODEL_FACING_SCHEMA_SECTION_PLACEHOLDER, schema_section
        ).rstrip()
        + "\n"
    )


def _create_openai_client() -> Any:
    """Create an OpenAI client with automatic retries disabled."""
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key, max_retries=0)


def _serialize_usage(usage: Any) -> dict[str, Any] | None:
    """Convert an SDK usage object to JSON-compatible dictionary data."""
    if usage is None:
        return None
    if hasattr(usage, "model_dump"):
        return usage.model_dump(mode="json", warnings=False)
    if isinstance(usage, dict):
        return usage
    return {
        key: getattr(usage, key)
        for key in ("input_tokens", "output_tokens", "total_tokens")
        if hasattr(usage, key)
    }
