"""Prepare offline or explicitly execute independent OpenRouter PNG extraction."""

import argparse
import base64
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat

from .statistical import DraftDSD, extraction_model, statistical_messages
from .spending import quote_request, record_spending, reported_cost

_PACKAGE = Path(__file__).parent
_DEFAULT_CONFIG = _PACKAGE / "config" / "openrouter.json"
_DEFAULT_DSD = _PACKAGE / "profiles" / "snapshot_indicators.json"
_DEFAULT_LEDGER = (
    _PACKAGE.parents[2] / "data/structured_data_trials/openrouter_spend.jsonl"
)


class APISettings(BaseModel):
    """Allow API settings without allowing overrides of evidence or response format."""

    model_config = ConfigDict(extra="forbid", strict=True)
    provider: Literal["openrouter"]
    model: str = Field(min_length=1, pattern=r"^\S+/\S+$")
    max_output_tokens: int = Field(gt=0)
    timeout: FiniteFloat = Field(gt=0)
    reasoning: dict[str, str] | None = None
    service_tier: str | None = None


def prepare_request(
    image_path: Path,
    dsd: DraftDSD,
    config: APISettings,
) -> dict[str, Any]:
    """Prepare a strict image-only Responses request without creating an API client.

    Parameters
    ----------
    image_path : Path
        Local PNG. Filenames and parent-document metadata are not model evidence.
    dsd : DraftDSD
        Provisional statistical structure supplied to the model.
    config : APISettings
        Validated OpenRouter settings.

    Returns
    -------
    dict
        Request arguments, including the PNG data URL, ready for the OpenAI SDK.

    Raises
    ------
    ValueError
        If input is not a readable PNG or a prompt placeholder is missing.
    """
    import fitz

    content = image_path.read_bytes()
    if not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Only PNG snapshot input is supported")
    with fitz.open(stream=content, filetype="png") as document:
        document[0].get_pixmap()
    system = (_PACKAGE / "prompts" / "system.md").read_text(encoding="utf-8")
    user = (_PACKAGE / "prompts" / "user.md").read_text(encoding="utf-8")
    if user.count("{{DSD}}") != 1:
        raise ValueError("User prompt must contain {{DSD}} exactly once")
    user = user.replace("{{DSD}}", dsd.model_dump_json(indent=2))
    settings = config.model_dump(exclude={"provider", "timeout"}, exclude_none=True)
    return {
        **settings,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system}]},
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": user},
                    {
                        "type": "input_image",
                        "image_url": "data:image/png;base64,"
                        + base64.b64encode(content).decode("ascii"),
                    },
                ],
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "data_snapshot_observations",
                "strict": True,
                "schema": extraction_model(dsd).model_json_schema(),
            }
        },
        "extra_body": {"provider": {"require_parameters": True}},
    }


def run_extraction(
    image_path: Path,
    output_dir: Path,
    dsd_path: Path = _DEFAULT_DSD,
    config_path: Path = _DEFAULT_CONFIG,
    execute: bool = False,
    client: Any | None = None,
    ledger_path: Path | None = None,
    batch_id: str | None = None,
) -> dict[str, Any]:
    """Save a fresh run, preparing offline unless execution is explicitly requested.

    Parameters
    ----------
    image_path, output_dir : Path
        Input PNG and fresh output directory for exactly this image.
    dsd_path, config_path : Path, optional
        Independent DSD and OpenRouter configuration files.
    execute : bool, optional
        Allow one API attempt. False by default; no client or key is loaded then.
    client : Any, optional
        Injectable Responses client for offline tests.
    ledger_path : Path, optional
        Persistent ledger shared across batches; uses the workstream ledger by default.
    batch_id : str, optional
        Experiment group for cumulative batch reporting; defaults to output name.

    Returns
    -------
    dict
        Run report with preparation, extraction or failure status and usage.

    Raises
    ------
    FileExistsError
        If the output directory already exists, before any API call.
    ValueError
        If the input, DSD, configuration or request preparation is invalid.
    """
    if output_dir.exists():
        raise FileExistsError(output_dir)
    dsd = DraftDSD.model_validate_json(dsd_path.read_text(encoding="utf-8"))
    config = APISettings.model_validate_json(config_path.read_text(encoding="utf-8"))
    request = prepare_request(image_path, dsd, config)
    output_dir.mkdir(parents=True, exist_ok=False)

    def write(filename: str, value: Any) -> None:
        (output_dir / filename).write_text(
            json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )

    preview = json.loads(json.dumps(request))
    preview["input"][1]["content"][1][
        "image_url"
    ] = "<local PNG data URL omitted from preview>"
    write("request.preview.json", preview)
    write("dsd.json", dsd.model_dump(mode="json"))
    write("config.json", config.model_dump(mode="json", exclude_none=True))
    report = {
        "image": str(image_path.resolve()),
        "image_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
        "model": config.model,
        "dsd": f"LOCAL:{dsd.id}({dsd.version})",
        "dsd_sha256": hashlib.sha256(dsd.model_dump_json().encode()).hexdigest(),
        "request_sha256": hashlib.sha256(
            json.dumps(request, sort_keys=True).encode()
        ).hexdigest(),
        "execution_requested": execute,
        "status": "prepared",
        "api_attempts": 0,
    }
    write("run.json", report)
    if not execute:
        return report
    started = time.perf_counter()
    ledger_path = ledger_path or _DEFAULT_LEDGER
    batch_id = batch_id or output_dir.name
    run_id = str(output_dir.resolve())
    reserved = False
    cost = None
    try:
        if client is None:
            from dotenv import load_dotenv
            from openai import OpenAI

            load_dotenv()
            key = os.getenv("OPENROUTER_API_KEY")
            if not key:
                raise ValueError("OPENROUTER_API_KEY is not set")
            client = OpenAI(
                api_key=key, base_url="https://openrouter.ai/api/v1", max_retries=0
            )
        quote = quote_request(config.model, config.max_output_tokens)
        write("pricing.json", quote)
        report["canonical_model"] = quote.get("canonical_slug")
        request["extra_body"]["provider"].update(
            max_price=quote["provider_max_price"], allow_fallbacks=False
        )
        preview["extra_body"] = request["extra_body"]
        write("request.preview.json", preview)
        report["request_sha256"] = hashlib.sha256(
            json.dumps(request, sort_keys=True).encode()
        ).hexdigest()
        report["ledger"] = str(ledger_path.resolve())
        report["spending"] = record_spending(
            ledger_path,
            run_id,
            batch_id,
            config.model,
            quote["allowance_usd"],
            "reserve",
        )
        reserved = True
        report["status"] = "requesting"
        report["api_attempts"] = 1
        write("run.json", report)
        response = client.responses.create(**request, timeout=config.timeout)
        raw = response.model_dump(mode="json")
        cost = reported_cost(raw.get("usage"))
        write("response.json", raw)
        report.update(
            response_id=raw.get("id"),
            api_status=raw.get("status"),
            usage=raw.get("usage"),
            incomplete_details=raw.get("incomplete_details"),
            resolved_model=raw.get("model"),
            service_tier=raw.get("service_tier"),
        )
        text = getattr(response, "output_text", None)
        if text:
            (output_dir / "raw_output.txt").write_text(text, encoding="utf-8")
        if raw.get("status") != "completed":
            raise ValueError(
                f"Response did not complete: {raw.get('status')}; {raw.get('incomplete_details') or raw.get('error')}"
            )
        if not text:
            raise ValueError("No structured output (the response may be a refusal)")
        result = extraction_model(dsd).model_validate_json(text)
        write("observations.json", result.model_dump(mode="json"))
        if result.datasets:
            structure, data = statistical_messages(dsd, result)
            write("structure.sdmx.json", structure)
            write("data.sdmx.json", data)
        report["status"] = result.status
        report["observations"] = sum(len(d.observations) for d in result.datasets)
    except KeyboardInterrupt:
        report["status"] = "interrupted"
        raise
    except Exception as error:
        report.update(
            status="failed", error_type=type(error).__name__, error=str(error)
        )
    finally:
        if reserved:
            report["spending"] = record_spending(
                ledger_path, run_id, batch_id, config.model, cost, "settle"
            )
        report["seconds"] = round(time.perf_counter() - started, 3)
        write("run.json", report)
    return report


def main() -> None:
    """Prepare one PNG offline, or make one explicitly requested OpenRouter call."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--dsd", type=Path, default=_DEFAULT_DSD)
    parser.add_argument("--config", type=Path, default=_DEFAULT_CONFIG)
    parser.add_argument(
        "--batch-id", help="Experiment label used in the cumulative cost ledger"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--execute",
        action="store_true",
        help="Allow one API attempt under the cumulative $5 research budget",
    )
    mode.add_argument(
        "--dry-run", action="store_true", help="Prepare offline (the default)"
    )
    args = parser.parse_args()
    report = run_extraction(
        args.image,
        args.output_dir,
        args.dsd,
        args.config,
        args.execute,
        batch_id=args.batch_id,
    )
    print(json.dumps(report, ensure_ascii=False))
    if report["status"] in {"failed", "partial", "unsupported"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
