"""Check persistent budget accounting, including failures and tiered pricing."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from data_snapshot.structured_data_extraction.spending import (
    quote_request,
    request_input_bound,
    record_spending,
    reported_cost,
)


def test_reservations_settlement_and_running_batch_totals(tmp_path: Path) -> None:
    """Do not reset spend between runs or release unreported/failed-call charges."""
    ledger = tmp_path / "ledger.jsonl"
    reserve = record_spending(ledger, "r1", "B1", "m", "3", "reserve")
    assert reserve["remaining_usd"] == "2.00"
    with pytest.raises(ValueError, match="would be exceeded"):
        record_spending(ledger, "r2", "B2", "m", "3", "reserve")
    first = record_spending(ledger, "r1", "B1", "m", "0.02", "settle")
    assert first["running_total_usd"] == "0.02"
    record_spending(ledger, "r2", "B1", "m", "1", "reserve")
    second = record_spending(ledger, "r2", "B1", "m", "0.03", "settle")
    assert second["batch_cost_usd"] == "0.05"
    assert second["remaining_usd"] == "4.95"
    record_spending(ledger, "r3", "B2", "m", "1", "reserve")
    unknown = record_spending(ledger, "r3", "B2", "m", None, "settle")
    assert unknown["running_total_usd"] == "0.05"
    assert unknown["reserved_usd"] == "1" and unknown["remaining_usd"] == "3.95"
    reconciled = record_spending(ledger, "r3", "B2", "m", "0.01", "settle")
    assert reconciled["running_total_usd"] == "0.06"
    assert reconciled["batch_cost_usd"] == "0.01"
    assert reconciled["reserved_usd"] == "0"
    with pytest.raises(ValueError, match="unsettled"):
        record_spending(ledger, "r3", "B2", "m", "0.01", "settle")
    assert (
        json.loads(ledger.read_text().splitlines()[-1])["running_total_usd"] == "0.06"
    )


@pytest.mark.parametrize(
    "cost",
    [None, {}, {"cost": None}, {"cost": -1}, {"cost": "NaN"}, {"cost": "invalid"}],
)
def test_unknown_cost_is_not_zero(cost: dict | None) -> None:
    """Missing or malformed provider billing cannot release reserved funds."""
    assert reported_cost(cost) is None
    assert reported_cost({"cost": 0}) == "0"
    assert reported_cost({"cost": "0.00123"}) == "0.00123"


def test_quote_covers_long_context_cache_and_output_rates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Use worst published tiers and enforce provider price ceilings."""
    import data_snapshot.structured_data_extraction.spending as spending

    model = {
        "id": "test/model",
        "context_length": 1000,
        "architecture": {"input_modalities": ["image", "text"]},
        "supported_parameters": ["structured_outputs"],
        "pricing": {
            "prompt": "0.000001",
            "completion": "0.000002",
            "overrides": [
                {
                    "prompt": "0.000002",
                    "completion": "0.000003",
                    "input_cache_write": "0.000004",
                }
            ],
        },
    }
    monkeypatch.setattr(
        spending.httpx,
        "get",
        lambda *args, **kwargs: SimpleNamespace(
            raise_for_status=lambda: None, json=lambda: {"data": [model]}
        ),
    )
    quote = quote_request("test/model", 100)
    assert quote["allowance_usd"] == "0.004300"
    assert quote["provider_max_price"]["prompt"] == 4
    assert quote["provider_max_price"]["completion"] == 3
    with pytest.raises(ValueError, match="not found"):
        quote_request("test/unknown", 100)
    model["id"] = "openai/gpt-5.6-sol"
    model["context_length"] = 100000
    prepared = {
        "model": model["id"],
        "input": [{"content": [{"type": "input_text", "text": "test"}]}],
    }
    tighter = quote_request(model["id"], 100, prepared)
    assert tighter["input_bound"]["method"] == "request_bytes_and_patches"
    assert tighter["input_bound"]["input_tokens_bound"] < 5000
    assert float(tighter["allowance_usd"]) < 0.021


def test_request_bound_includes_png_and_entire_response_schema() -> None:
    """Exclude compressed image bytes from text while including all patch tokens."""
    import base64
    import struct

    header = (
        b"\x89PNG\r\n\x1a\n"
        + struct.pack(">I", 13)
        + b"IHDR"
        + struct.pack(">II", 1024, 1024)
    )
    request = {
        "model": "openai/gpt-5.6-sol",
        "input": [
            {
                "content": [
                    {"type": "input_text", "text": "Aé"},
                    {
                        "type": "input_image",
                        "image_url": "data:image/png;base64,"
                        + base64.b64encode(header).decode(),
                    },
                ]
            }
        ],
        "text": {"format": {"schema": {"description": "a" * 1000}}},
    }
    bound = request_input_bound(request)
    assert bound["image_tokens_bound"] == 1230
    assert bound["input_tokens_bound"] == bound["text_schema_bytes"] + 4096 + 1230
    assert bound["text_schema_bytes"] > 1000
    request["tools"] = []
    with pytest.raises(ValueError, match="without tools"):
        request_input_bound(request)
