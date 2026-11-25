"""Run one frozen six-image model arm under the shared structured-extraction budget."""

import argparse
import hashlib
import json
from pathlib import Path

from data_snapshot.structured_data_extraction.llm import (
    APISettings,
    prepare_request,
    run_extraction,
)
from data_snapshot.structured_data_extraction.statistical import DraftDSD


def main() -> None:
    """Resume one model arm without repeating previously attempted image calls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_dir", type=Path)
    parser.add_argument("model", choices=["luna", "terra", "sol"])
    args = parser.parse_args()
    root = args.experiment_dir
    manifest = json.loads((root / "manifest.json").read_text())
    config_path = root / f"{args.model}.json"
    config = APISettings.model_validate_json(config_path.read_text())
    assert config.model == f"openai/gpt-5.6-{args.model}"
    assert config.reasoning == {"effort": manifest["reasoning"]}
    assert config.max_output_tokens == manifest["max_output_tokens"]
    assert config.service_tier in {None, manifest["service_tier"]}
    dsd_path = root / "dsd.json"
    dsd = DraftDSD.model_validate_json(dsd_path.read_text())
    images = []
    for sample in manifest["samples"]:
        image = Path(manifest["sample_root"]) / sample["image"]
        assert hashlib.sha256(image.read_bytes()).hexdigest() == sample["image_sha256"]
        request = prepare_request(image, dsd, config)
        contract = {key: request[key] for key in ("input", "text")}
        assert (
            hashlib.sha256(json.dumps(contract, sort_keys=True).encode()).hexdigest()
            == sample["contract_sha256"]
        )
        images.append(image)
    reports = []
    for sample, image in zip(manifest["samples"], images):
        output = root / args.model / sample["id"]
        if output.exists():
            report = json.loads((output / "run.json").read_text())
        else:
            report = run_extraction(
                image,
                output,
                dsd_path,
                config_path,
                execute=True,
                batch_id=f"C1_{args.model}",
            )
        reports.append({"sample": sample["id"], **report})
        print(
            json.dumps(
                {
                    "sample": sample["id"],
                    "model": args.model,
                    "status": report["status"],
                    "observations": report.get("observations"),
                    "seconds": report.get("seconds"),
                    "spending": report.get("spending"),
                    "error": report.get("error"),
                }
            ),
            flush=True,
        )
        if (
            report.get("input_bound_exceeded")
            or report.get("spending", {}).get("cost_status") != "reported"
        ):
            raise RuntimeError(
                "Stop model arm: input bound or unsettled charge needs inspection"
            )
    (root / f"{args.model}_runs.json").write_text(json.dumps(reports, indent=2) + "\n")


if __name__ == "__main__":
    main()
