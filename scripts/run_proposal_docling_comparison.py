"""Resume frozen image-only versus image-plus-Docling initial proposal calls."""

import argparse
import hashlib
import json
from pathlib import Path

from data_snapshot.structured_data_extraction.llm import APISettings, _PACKAGE
from data_snapshot.structured_data_extraction.model_proposal import (
    prepare_model_request,
    run_model_proposal,
)
from data_snapshot.structured_data_extraction.working_model import WorkingModel


def contract_hash(request: dict) -> str:
    """Fingerprint the image, prompts and response schema independently of pricing.

    Parameters
    ----------
    request : dict
        Prepared Responses request.

    Returns
    -------
    str
        SHA-256 of the inference content and output contract.
    """
    return hashlib.sha256(
        json.dumps(
            {key: request[key] for key in ("input", "text")}, sort_keys=True
        ).encode()
    ).hexdigest()


def main() -> None:
    """Check frozen inputs, then prepare offline or execute each unattempted arm once."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_dir", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    root = args.experiment_dir
    manifest = json.loads((root / "manifest.json").read_text())
    config_path = root / "config.json"
    config = APISettings.model_validate_json(config_path.read_text())
    for name, expected in manifest["files"].items():
        path = config_path if name == "config.json" else _PACKAGE / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Frozen configuration or prompt changed: {name}")
    if (
        hashlib.sha256(
            json.dumps(WorkingModel.model_json_schema(), sort_keys=True).encode()
        ).hexdigest()
        != manifest["schema_sha256"]
    ):
        raise ValueError("Frozen proposal schema changed")
    runs = []
    for index, sample in enumerate(manifest["samples"]):
        image, native = Path(sample["image"]), Path(sample["native"])
        if hashlib.sha256(image.read_bytes()).hexdigest() != sample["image_sha256"]:
            raise ValueError("Frozen PNG changed")
        arms = ["image_only", "image_docling"]
        if index % 2:
            arms.reverse()
        for arm in arms:
            source = native if arm == "image_docling" else None
            request, _, identities = prepare_model_request(image, source, config)
            if contract_hash(request) != sample["contracts"][arm]:
                raise ValueError(f"Frozen request changed: {sample['id']}/{arm}")
            output = (
                root / ("runs" if args.execute else "prepared") / arm / sample["id"]
            )
            if output.exists():
                report = json.loads((output / "run.json").read_text())
                if any(report.get(key) != value for key, value in identities.items()):
                    raise ValueError("Saved attempt belongs to different evidence")
                if args.execute and report["status"] not in {"proposed", "failed"}:
                    raise ValueError(
                        "Previous attempt is unfinished; inspect before any new call"
                    )
            else:
                report = run_model_proposal(
                    image,
                    source,
                    output,
                    config_path,
                    execute=args.execute,
                    batch_id=manifest["batch_id"],
                )
            row = {"sample": sample["id"], "arm": arm, **report}
            runs.append(row)
            (root / ("runs.json" if args.execute else "prepared.json")).write_text(
                json.dumps(runs, indent=2) + "\n"
            )
            print(
                json.dumps(
                    {
                        key: row.get(key)
                        for key in (
                            "sample",
                            "arm",
                            "status",
                            "seconds",
                            "spending",
                            "error",
                        )
                    }
                ),
                flush=True,
            )
            if args.execute and (
                report.get("input_bound_exceeded")
                or report.get("spending", {}).get("cost_status") != "reported"
            ):
                raise RuntimeError(
                    "Stop: unsettled charge or spending bound needs inspection"
                )


if __name__ == "__main__":
    main()
