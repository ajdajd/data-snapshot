"""Track the cumulative $5 OpenRouter research budget, including uncertain charges."""

import fcntl
import json
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import httpx

_LIMIT = Decimal("5.00")


def reported_cost(usage: dict[str, Any] | None) -> str | None:
    """Return a valid billed USD amount, or None when billing remains unknown.

    Parameters
    ----------
    usage : dict or None
        OpenRouter usage object, independent of extraction/validation success.

    Returns
    -------
    str or None
        Finite nonnegative charge. Missing or invalid billing retains allowance.
    """
    try:
        value = Decimal(str((usage or {}).get("cost")))
    except (InvalidOperation, ValueError):
        return None
    return str(value) if value.is_finite() and value >= 0 else None


def quote_request(model: str, max_output_tokens: int) -> dict[str, Any]:
    """Fetch public model pricing and reserve a conservative context-wide allowance.

    Parameters
    ----------
    model : str
        Exact OpenRouter model ID; automatic model selection is not used.
    max_output_tokens : int
        Explicit response token ceiling, including reasoning tokens.

    Returns
    -------
    dict
        Price snapshot, allowance, and provider rate ceilings. Uses the full
        context length for input instead of an unverified vision-token estimate.

    Raises
    ------
    ValueError
        If the model lacks supported image/structured output or usable pricing.
    httpx.HTTPError
        If the free catalogue lookup fails, before any generation is attempted.
    """
    response = httpx.get("https://openrouter.ai/api/v1/models", timeout=45)
    response.raise_for_status()
    entry = next((m for m in response.json()["data"] if m["id"] == model), None)
    if entry is None:
        raise ValueError(f"Model not found in OpenRouter catalogue: {model}")
    if (
        "image" not in entry["architecture"]["input_modalities"]
        or "structured_outputs" not in entry["supported_parameters"]
    ):
        raise ValueError("Model must support image input and structured outputs")
    pricing = entry["pricing"]
    tiers = [pricing, *pricing.get("overrides", [])]
    input_rate = max(
        Decimal(str(tier.get(field, 0)))
        for tier in tiers
        for field in (
            "prompt",
            "input_cache_read",
            "input_cache_write",
            "input_cache_write_1h",
        )
    )
    output_rate = max(
        Decimal(str(t.get("completion", pricing["completion"]))) for t in tiers
    )
    image_rate = max(Decimal(str(t.get("image", 0))) for t in tiers)
    request_rate = max(Decimal(str(t.get("request", 0))) for t in tiers)
    rates = [input_rate, output_rate, image_rate, request_rate]
    if any(not rate.is_finite() or rate < 0 for rate in rates):
        raise ValueError("Model prices must be finite and nonnegative")
    context = entry["context_length"]
    if not isinstance(context, int) or context <= 0:
        raise ValueError("Missing model context bound")
    allowance = (
        context * input_rate
        + max_output_tokens * output_rate
        + image_rate
        + request_rate
    )
    return {
        "model": model,
        "canonical_slug": entry.get("canonical_slug"),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source": "https://openrouter.ai/api/v1/models",
        "context_length": context,
        "pricing": pricing,
        "allowance_usd": str(allowance),
        "provider_max_price": {
            "prompt": float(input_rate * 1_000_000),
            "completion": float(output_rate * 1_000_000),
            "image": float(image_rate),
            "request": float(request_rate),
        },
    }


def record_spending(
    ledger_path: Path,
    run_id: str,
    batch_id: str,
    model: str,
    amount: str | None,
    event: str,
) -> dict[str, Any]:
    """Reserve or settle one call in an append-only, process-locked cost ledger.

    Parameters
    ----------
    ledger_path : Path
        Persistent journal shared by all calls in this workstream.
    run_id, batch_id, model : str
        Unique run path, human-readable experiment group, and requested model.
    amount : str or None
        USD allowance for reserve, or actual OpenRouter charge for settle.
        None on settlement retains the reservation as an unresolved charge.
    event : str
        Either reserve or settle. Failed calls with a billed cost also settle.

    Returns
    -------
    dict
        Call charge and running batch/workstream totals, including pending funds.

    Raises
    ------
    ValueError
        If the ledger is invalid, the call is duplicated, or the budget is too low.
    """
    if event not in {"reserve", "settle"}:
        raise ValueError("Unknown spending event")
    charge = Decimal(amount) if amount is not None else None
    if charge is not None and (not charge.is_finite() or charge < 0):
        raise ValueError("Cost must be finite and nonnegative")
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a+", encoding="utf-8") as file:
        fcntl.flock(file, fcntl.LOCK_EX)
        file.seek(0)
        entries = [json.loads(line) for line in file if line.strip()]
        state = {}
        for row in entries:
            if Decimal(row["budget_usd"]) != _LIMIT:
                raise ValueError("Ledger budget differs from the authorized $5 cap")
            state[row["run_id"]] = row
        accounted = sum(
            (Decimal(r["accounted_usd"]) for r in state.values()), Decimal(0)
        )
        if event == "reserve":
            if run_id in state or charge is None:
                raise ValueError("Run already reserved or allowance missing")
            if accounted + charge > _LIMIT:
                raise ValueError(
                    f"$5 budget would be exceeded: ${accounted} accounted + ${charge} allowance"
                )
        elif run_id not in state or state[run_id]["event"] not in {
            "reserve",
            "unresolved",
        }:
            raise ValueError("Settlement requires one unsettled reservation")
        if event == "settle" and charge is None:
            # An unknown charge is never counted as free; keep the full allowance.
            charge = Decimal(state[run_id]["accounted_usd"])
            event = "unresolved"
        row = {
            "time": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "run_id": run_id,
            "batch_id": batch_id,
            "model": model,
            "budget_usd": str(_LIMIT),
            "accounted_usd": str(charge),
        }
        state[run_id] = row
        billed = sum(
            (
                Decimal(r["accounted_usd"])
                for r in state.values()
                if r["event"] == "settle"
            ),
            Decimal(0),
        )
        pending = sum(
            (
                Decimal(r["accounted_usd"])
                for r in state.values()
                if r["event"] != "settle"
            ),
            Decimal(0),
        )
        batch_billed = sum(
            (
                Decimal(r["accounted_usd"])
                for r in state.values()
                if r["event"] == "settle" and r["batch_id"] == batch_id
            ),
            Decimal(0),
        )
        summary = {
            "budget_usd": str(_LIMIT),
            "batch_id": batch_id,
            "call_cost_usd": str(charge) if event == "settle" else None,
            "batch_cost_usd": str(batch_billed),
            "running_total_usd": str(billed),
            "reserved_usd": str(pending),
            "remaining_usd": str(_LIMIT - billed - pending),
            "cost_status": "reported" if event == "settle" else event,
        }
        file.write(json.dumps({**row, **summary}) + "\n")
        file.flush()
        os.fsync(file.fileno())
        return summary
