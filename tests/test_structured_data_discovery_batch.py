"""Exercise resume, frozen inputs and cost uncertainty using no API calls."""

import fcntl
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import fitz
import pytest

from data_snapshot.structured_data_extraction.llm import APISettings, _write_json
from data_snapshot.structured_data_extraction.spending import record_spending


@pytest.fixture
def batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Load the CLI with six tiny PNGs and an isolated existing spending journal."""
    script = Path(__file__).parents[1] / "scripts/run_structured_data_discovery.py"
    spec = importlib.util.spec_from_file_location("discovery_batch_test", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    samples = tmp_path / "samples"
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 8, 8), False)
    pixmap.clear_with(255)
    for corpus in ("prwp", "refugee", "unhcr"):
        (samples / corpus).mkdir(parents=True)
        for kind in ("figure", "table"):
            (samples / corpus / f"doc_{kind}_000.png").write_bytes(
                pixmap.tobytes("png")
            )
    ledger = tmp_path / "spend.jsonl"
    record_spending(ledger, "earlier", "pilot", "model", "0.01", "reserve")
    record_spending(ledger, "earlier", "pilot", "model", "0.01", "settle")
    monkeypatch.setattr(module, "_SAMPLES", samples)
    monkeypatch.setattr(module, "_DEFAULT_LEDGER", ledger)
    monkeypatch.setattr(module, "_GROUPS", {key: 1 for key in module._GROUPS})
    return module


def fake_run(batch: ModuleType, calls: list[str], mode: str = "success") -> Any:
    """Build a one-shot fake that uses the real spending journal and result layout."""

    def run(image: Path, output: Path, **kwargs: Any) -> dict[str, Any]:
        calls.append(image.parent.name + "/" + image.name)
        request = batch.prepare_discovery_request(
            image, APISettings.model_validate_json(kwargs["config_path"].read_text())
        )
        output.mkdir(parents=True)
        report = {
            "image_sha256": batch._digest(image.read_bytes()),
            "contract_sha256": batch._contract_hash(request),
            "model": request["model"],
            "api_attempts": 0,
            "status": "failed",
            "error": "Synthetic failure",
        }
        if mode == "preflight" and len(calls) == 1:
            _write_json(output / "run.json", report)
            return report
        ledger = kwargs["ledger_path"]
        run_id = str(output.resolve())
        record_spending(
            ledger, run_id, kwargs["batch_id"], request["model"], "0.001", "reserve"
        )
        report.update(api_attempts=1, status="requesting")
        _write_json(output / "run.json", report)
        if mode == "unresolved" and len(calls) == 1:
            raise KeyboardInterrupt
        report["spending"] = record_spending(
            ledger, run_id, kwargs["batch_id"], request["model"], "0.001", "settle"
        )
        report["status"] = (
            "failed" if mode == "billed_failure" and len(calls) == 1 else "discovered"
        )
        if report["status"] == "discovered":
            record = {
                key: []
                for key in (
                    "analytical_units",
                    "relationships",
                    "ambiguities",
                    "other_analytical_content",
                )
            }
            _write_json(output / "discovery.json", record)
            _write_json(output / "raw_output.txt", record)
        _write_json(output / "run.json", report)
        return report

    return run


def test_preparation_is_offline_and_resume_skips_completed(
    tmp_path: Path, batch: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prepare without network, resume after an interruption, and never repeat calls."""
    calls = []
    runner = fake_run(batch, calls)
    output = tmp_path / "D2"
    monkeypatch.setattr(batch, "run_discovery", runner)
    assert batch.run_batch(output)["pending"] == 6
    assert calls == []

    def interrupted(image: Path, attempt: Path, **kwargs: Any) -> dict[str, Any]:
        if len(calls) == 2:
            raise KeyboardInterrupt
        return runner(image, attempt, **kwargs)

    monkeypatch.setattr(batch, "run_discovery", interrupted)
    with pytest.raises(KeyboardInterrupt):
        batch.run_batch(output, execute=True)
    assert json.loads((output / "summary.json").read_text())["discovered"] == 2
    monkeypatch.setattr(batch, "run_discovery", runner)
    summary = batch.run_batch(output, execute=True)
    assert summary["discovered"] == 6 and len(set(calls)) == len(calls) == 6
    assert summary["batch_cost_usd"] == "0.006"
    assert summary["running_total_usd"] == "0.016"
    batch.run_batch(output, execute=True)
    assert len(calls) == 6


@pytest.mark.parametrize(
    "damage", ["image", "membership", "config", "ledger", "snapshot"]
)
def test_changed_frozen_inputs_stop_before_calls(
    tmp_path: Path, batch: ModuleType, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    """Refuse changed experiment inputs or a reset spending ledger on resume."""
    output = tmp_path / "D2"
    batch.run_batch(output)
    calls = []
    monkeypatch.setattr(batch, "run_discovery", fake_run(batch, calls))
    if damage == "image":
        image = next(batch._SAMPLES.glob("*/*.png"))
        image.write_bytes(image.read_bytes() + b"changed image bytes")
    elif damage == "membership":
        next(batch._SAMPLES.glob("*/*.png")).unlink()
    elif damage == "config":
        (output / "config.json").write_text("{}")
    elif damage == "snapshot":
        (output / "discovery_system.md").write_text("Changed instructions")
    else:
        batch._DEFAULT_LEDGER.write_text("")
    with pytest.raises(ValueError):
        batch.run_batch(output, execute=True)
    assert not calls


def test_known_billed_failure_is_retained_and_never_retried(
    tmp_path: Path, batch: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Continue other samples but report incomplete coverage and preserve the charge."""
    calls = []
    monkeypatch.setattr(
        batch, "run_discovery", fake_run(batch, calls, "billed_failure")
    )
    output = tmp_path / "D2"
    summary = batch.run_batch(output, execute=True)
    assert summary["failed"] == 1 and summary["discovered"] == 5
    assert summary["batch_cost_usd"] == "0.006"
    batch.run_batch(output, execute=True)
    assert len(calls) == 6


def test_unknown_charge_stops_resume_without_duplicate_request(
    tmp_path: Path, batch: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Treat an interrupted in-flight request as blocked until billing is reconciled."""
    calls = []
    monkeypatch.setattr(batch, "run_discovery", fake_run(batch, calls, "unresolved"))
    output = tmp_path / "D2"
    with pytest.raises(KeyboardInterrupt):
        batch.run_batch(output, execute=True)
    summary = batch.run_batch(output, execute=True)
    assert summary["blocked"] == 1 and summary["reserved_usd"] == "0.001"
    assert len(calls) == 1


def test_safe_preflight_failure_uses_new_attempt_on_resume(
    tmp_path: Path, batch: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Retry only a confirmed zero-API, unreserved attempt while retaining its log."""
    calls = []
    monkeypatch.setattr(batch, "run_discovery", fake_run(batch, calls, "preflight"))
    output = tmp_path / "D2"
    summary = batch.run_batch(output, execute=True)
    assert summary["pending"] == 6 and summary["batch_cost_usd"] == "0"
    summary = batch.run_batch(output, execute=True)
    assert summary["discovered"] == 6 and len(calls) == 7
    assert len(list((output / "runs").glob("*/attempt_002/run.json"))) == 1


def test_second_process_cannot_start_same_experiment(
    tmp_path: Path, batch: ModuleType
) -> None:
    """Prevent two processes from charging for the same pending image."""
    output = tmp_path / "D2"
    output.mkdir()
    with (output / ".runner.lock").open("a") as file:
        fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            batch.run_batch(output, execute=True)


def test_saved_result_tampering_stops_resume(
    tmp_path: Path, batch: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Do not silently accept edited results as completed discoveries."""
    calls = []
    monkeypatch.setattr(batch, "run_discovery", fake_run(batch, calls))
    output = tmp_path / "D2"
    batch.run_batch(output, execute=True)
    result = next((output / "runs").glob("*/attempt_001/discovery.json"))
    result.write_text("{}")
    with pytest.raises(ValueError, match="differs from saved raw output"):
        batch.run_batch(output, execute=True)
    assert len(calls) == 6


def test_input_change_during_execution_stops_before_next_call(
    tmp_path: Path, batch: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prevent a running process from mixing changed evidence into the frozen run."""
    calls = []
    runner = fake_run(batch, calls)

    def changing_input(image: Path, attempt: Path, **kwargs: Any) -> dict[str, Any]:
        report = runner(image, attempt, **kwargs)
        next_image = sorted(batch._SAMPLES.glob("*/*.png"))[1]
        next_image.write_bytes(next_image.read_bytes() + b"changed during run")
        return report

    monkeypatch.setattr(batch, "run_discovery", changing_input)
    with pytest.raises(ValueError, match="changed during execution"):
        batch.run_batch(tmp_path / "D2", execute=True)
    assert len(calls) == 1
