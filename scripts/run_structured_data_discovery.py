"""Prepare offline or resume independent discovery on the 210 development PNGs."""

import argparse
import fcntl
import hashlib
import json
import logging
import time
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

from data_snapshot.structured_data_extraction.discovery import (
    prepare_discovery_request,
    run_discovery,
    validate_discovery,
)
from data_snapshot.structured_data_extraction.llm import (
    APISettings,
    _DEFAULT_CONFIG,
    _DEFAULT_LEDGER,
    _PACKAGE,
    _write_json,
)
from data_snapshot.structured_data_extraction.spending import request_input_bound

_REPO = Path(__file__).resolve().parents[1]
_SAMPLES = _REPO / "notebooks/schema_discovery/data/snapshots"
_GROUPS = {
    f"{corpus}/{kind}": 35
    for corpus in ("prwp", "refugee", "unhcr")
    for kind in ("figure", "table")
}
_LOG = logging.getLogger("discovery_batch")


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _contract_hash(request: dict[str, Any]) -> str:
    return _digest(
        json.dumps(
            {key: request[key] for key in ("input", "text")}, sort_keys=True
        ).encode()
    )


def _ledger_state(path: Path) -> tuple[bytes, dict[str, Any]]:
    # Read under the journal lock so a concurrent settlement cannot look truncated.
    with path.open("rb") as file:
        fcntl.flock(file, fcntl.LOCK_SH)
        content = file.read()
    state = {}
    for line in content.splitlines():
        row = json.loads(line)
        if Decimal(row["budget_usd"]) != Decimal("5.00"):
            raise ValueError("Spending ledger does not use the authorized $5 cap")
        state[row["run_id"]] = row
    return content, state


def prepare_manifest(output: Path) -> dict[str, Any]:
    """Freeze or verify all development inputs without accessing the network.

    Parameters
    ----------
    output : Path
        Experiment directory, protected by the caller's batch lock.

    Returns
    -------
    dict
        Frozen sample, instrument and spending-journal identities.

    Raises
    ------
    ValueError
        If the instrument, sample membership, image bytes or ledger prefix changed.
    """
    release = json.loads((_PACKAGE / "config/discovery_instrument.json").read_text())
    for name, digest in release["artifacts_sha256"].items():
        if _digest((_PACKAGE / name).read_bytes()) != digest:
            raise ValueError(f"Calibrated discovery instrument changed: {name}")
    if _digest(_DEFAULT_CONFIG.read_bytes()) != release["config_sha256"]:
        raise ValueError("Calibrated model settings changed")
    config = APISettings.model_validate_json(_DEFAULT_CONFIG.read_text())
    samples = []
    groups = Counter()
    images = sorted(_SAMPLES.glob("*/*.png"))
    _LOG.info(
        "Verifying instrument v%s and %s development PNGs",
        release["instrument_version"],
        len(images),
    )
    for index, image in enumerate(images, start=1):
        corpus = image.parent.name
        kind = image.stem.rsplit("_", 2)[-2]
        groups[f"{corpus}/{kind}"] += 1
        request = prepare_discovery_request(image, config)
        request_input_bound(request)
        samples.append(
            {
                "id": f"{corpus}__{image.stem}",
                "image": str(image.relative_to(_SAMPLES)),
                "image_sha256": _digest(image.read_bytes()),
                "contract_sha256": _contract_hash(request),
            }
        )
        if index % 35 == 0 or index == len(images):
            _LOG.info("Verified inputs %s/%s", index, len(images))
    if dict(groups) != _GROUPS:
        raise ValueError(f"Expected 35 figures/tables per corpus; found {dict(groups)}")
    identity = {
        "instrument": release,
        "sample_root": str(_SAMPLES.resolve()),
        "samples": samples,
    }
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if any(manifest[key] != value for key, value in identity.items()):
            raise ValueError(
                "Frozen prompts, settings, sample membership or image bytes changed"
            )
        for name, digest in release["artifacts_sha256"].items():
            if _digest((output / Path(name).name).read_bytes()) != digest:
                raise ValueError(f"Frozen instrument snapshot changed: {name}")
        if _digest((output / "config.json").read_bytes()) != release["config_sha256"]:
            raise ValueError("Frozen configuration snapshot changed")
        content, _ = _ledger_state(Path(manifest["ledger"]))
        if (
            _digest(content[: manifest["ledger_prefix_bytes"]])
            != manifest["ledger_prefix_sha256"]
        ):
            raise ValueError("Shared spending ledger was reset, truncated or rewritten")
        return manifest
    if any((output / name).exists() for name in ("runs", "summary.json")):
        raise ValueError("Existing results have no manifest; inspect before continuing")
    content, _ = _ledger_state(_DEFAULT_LEDGER)
    manifest = {
        **identity,
        "batch_id": output.name,
        "ledger": str(_DEFAULT_LEDGER.resolve()),
        "ledger_prefix_bytes": len(content),
        "ledger_prefix_sha256": _digest(content),
    }
    for name in release["artifacts_sha256"]:
        (output / Path(name).name).write_bytes((_PACKAGE / name).read_bytes())
    (output / "config.json").write_bytes(_DEFAULT_CONFIG.read_bytes())
    _write_json(manifest_path, manifest)
    return manifest


def _sample_state(
    output: Path, sample: dict[str, Any], config: APISettings, ledger: dict[str, Any]
) -> dict[str, Any]:
    attempts = sorted((output / "runs" / sample["id"]).glob("attempt_*"))
    if not attempts:
        return {"id": sample["id"], "status": "pending", "attempts": 0}
    attempt = attempts[-1]
    result = {
        "id": sample["id"],
        "status": "blocked",
        "attempts": len(attempts),
        "output": str(attempt),
    }
    report_path = attempt / "run.json"
    if not report_path.exists():
        return {
            **result,
            "reason": "Attempt has no run report; inspect before resuming",
        }
    report = json.loads(report_path.read_text())
    if (
        report.get("image_sha256") != sample["image_sha256"]
        or report.get("contract_sha256") != sample["contract_sha256"]
        or report.get("model") != config.model
    ):
        raise ValueError(f"Attempt identity differs from frozen manifest: {attempt}")
    charge = ledger.get(str(attempt.resolve()))
    if report.get("input_bound_exceeded"):
        return {**result, "reason": "Input bound exceeded; audit before continuing"}
    if charge is not None and charge["event"] != "settle":
        return {**result, "reason": "Unresolved charge; reconcile before continuing"}
    if report.get("api_attempts") == 0 and charge is None:
        return {
            **result,
            "status": "pending",
            "reason": report.get("error", "No API attempt was made"),
        }
    if charge is None:
        return {**result, "reason": "API attempt has no settled ledger charge"}
    if report["status"] == "discovered":
        record = json.loads((attempt / "discovery.json").read_text())
        raw_record = json.loads((attempt / "raw_output.txt").read_text())
        if raw_record != record:
            raise ValueError(
                f"Discovery result differs from saved raw output: {attempt}"
            )
        schema = json.loads((output / "discovery_record.schema.json").read_text())
        validate_discovery(record, schema)
        return {**result, "status": "discovered"}
    return {
        **result,
        "status": "failed",
        "reason": report.get("error", report["status"]),
    }


def summarize(output: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Persist progress and current batch/workstream costs without modifying billing.

    Parameters
    ----------
    output : Path
        Experiment output directory.
    manifest : dict
        Frozen experiment manifest.

    Returns
    -------
    dict
        Image statuses, counts and spending, saved atomically as summary.json.
    """
    _, ledger = _ledger_state(Path(manifest["ledger"]))
    config = APISettings.model_validate_json((output / "config.json").read_text())
    images = [
        _sample_state(output, sample, config, ledger) for sample in manifest["samples"]
    ]
    billed = sum(
        (
            Decimal(row["accounted_usd"])
            for row in ledger.values()
            if row["event"] == "settle"
        ),
        Decimal(0),
    )
    reserved = sum(
        (
            Decimal(row["accounted_usd"])
            for row in ledger.values()
            if row["event"] != "settle"
        ),
        Decimal(0),
    )
    batch_cost = sum(
        (
            Decimal(row["accounted_usd"])
            for row in ledger.values()
            if row["event"] == "settle" and row["batch_id"] == manifest["batch_id"]
        ),
        Decimal(0),
    )
    summary = {
        "batch_id": manifest["batch_id"],
        "total": len(images),
        **{
            status: sum(item["status"] == status for item in images)
            for status in ("discovered", "failed", "pending", "blocked")
        },
        "batch_cost_usd": str(batch_cost),
        "running_total_usd": str(billed),
        "reserved_usd": str(reserved),
        "remaining_usd": str(Decimal("5.00") - billed - reserved),
        "images": images,
    }
    _write_json(output / "summary.tmp.json", summary)
    (output / "summary.tmp.json").replace(output / "summary.json")
    _LOG.info(
        "%s",
        json.dumps({key: value for key, value in summary.items() if key != "images"}),
    )
    return summary


def run_batch(output: Path, execute: bool = False) -> dict[str, Any]:
    """Verify, prepare or resume the frozen development run under an exclusive lock.

    Parameters
    ----------
    output : Path
        Persistent experiment directory; reuse the same path to resume.
    execute : bool, optional
        Permit pending one-shot calls. False performs offline preparation only.

    Returns
    -------
    dict
        Final progress and cumulative spending summary.

    Raises
    ------
    BlockingIOError
        If another process holds this experiment's lock.
    ValueError
        If the frozen instrument, inputs or saved results fail verification.
    """
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with (output / ".runner.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        manifest = prepare_manifest(output)
        summary = summarize(output, manifest)
        if not execute:
            return summary
        try:
            for sample, state in zip(manifest["samples"], summary["images"]):
                if summary["blocked"] or Decimal(summary["reserved_usd"]) != 0:
                    _LOG.error(
                        "Stopped: unresolved attempt or spending reservation needs review"
                    )
                    break
                if state["status"] != "pending":
                    _LOG.info("Skip %s: %s", sample["id"], state["status"])
                    continue
                config_bytes = (output / "config.json").read_bytes()
                if _digest(config_bytes) != manifest["instrument"]["config_sha256"]:
                    raise ValueError("Frozen model settings changed during execution")
                image = Path(manifest["sample_root"]) / sample["image"]
                request = prepare_discovery_request(
                    image, APISettings.model_validate_json(config_bytes)
                )
                if _contract_hash(request) != sample["contract_sha256"]:
                    raise ValueError(
                        f"Image or discovery instrument changed during execution: {sample['id']}"
                    )
                attempt = (
                    output
                    / "runs"
                    / sample["id"]
                    / f"attempt_{state['attempts'] + 1:03d}"
                )
                _LOG.info("Start %s (%s)", sample["id"], attempt.name)
                report = run_discovery(
                    image,
                    attempt,
                    config_path=output / "config.json",
                    execute=True,
                    ledger_path=Path(manifest["ledger"]),
                    batch_id=manifest["batch_id"],
                )
                _LOG.info(
                    "Result %s: %s; %s",
                    sample["id"],
                    report["status"],
                    report.get("error", ""),
                )
                summary = summarize(output, manifest)
                if report["api_attempts"] == 0:
                    _LOG.error(
                        "Stopped before API attempt; fix preflight issue and rerun to resume"
                    )
                    break
        finally:
            summary = summarize(output, manifest)
        return summary


def main() -> None:
    """Prepare offline by default, or resume with --execute; append UTC logs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ"
    )
    formatter.converter = time.gmtime
    for handler in (
        logging.StreamHandler(),
        logging.FileHandler(args.output_dir / "runner.log"),
    ):
        handler.setFormatter(formatter)
        _LOG.addHandler(handler)
    _LOG.setLevel(logging.INFO)
    try:
        summary = run_batch(args.output_dir, args.execute)
    except KeyboardInterrupt:
        _LOG.warning(
            "Interrupted. Reuse this output directory to resume; inspect summary.json for unresolved charges."
        )
        raise SystemExit(130)
    except Exception:
        _LOG.exception("Runner stopped; existing results were preserved")
        raise SystemExit(1)
    print(json.dumps({key: value for key, value in summary.items() if key != "images"}))
    if args.execute and summary["discovered"] != summary["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
