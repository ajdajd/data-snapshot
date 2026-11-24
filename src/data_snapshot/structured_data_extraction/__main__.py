"""Run independent local PNG extraction and optional SDMX transformation."""

import argparse
import hashlib
import json
import time
from importlib.metadata import version
from pathlib import Path

from PIL import Image

from .docling import extract_image
from .model import Profile, map_table, sdmx_messages


def main() -> None:
    """Extract PNGs and preserve failures and evidence in fresh output folders."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", type=Path, nargs="+")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", choices=["cpu", "cuda:0"], default="cpu")
    parser.add_argument(
        "--pipeline", choices=["standard", "granite", "chart"], default="standard"
    )
    parser.add_argument(
        "--profile", type=Path, help="Reviewed mapping; omit for native extraction only"
    )
    args = parser.parse_args()
    profile = (
        Profile.model_validate_json(args.profile.read_text()) if args.profile else None
    )
    if len({p.stem for p in args.images}) != len(args.images):
        parser.error("Image stems must be unique within a run")
    for path in args.images:
        with Image.open(path) as image:
            if image.format != "PNG":
                parser.error(f"Only PNG snapshots are supported: {path}")
            image.verify()
        if (args.output_dir / path.stem).exists():
            raise FileExistsError(args.output_dir / path.stem)
    failed = False
    for path in args.images:
        output = args.output_dir / path.stem
        output.mkdir(parents=True)
        report = {
            "image": str(path.resolve()),
            "image_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "pipeline": args.pipeline,
            "docling_version": version("docling"),
            "device": args.device,
            "profile": profile.model_dump() if profile else None,
            "max_new_tokens": (2048 if args.pipeline in {"granite", "chart"} else None),
            "chart_preset": (
                "granite_vision_v3_3" if args.pipeline == "chart" else None
            ),
            "chart_image_scale": 0.5 if args.pipeline == "chart" else None,
            "chart_cpu_offload": args.pipeline == "chart" and args.device == "cuda:0",
            "status": "started",
        }
        started = time.monotonic()
        try:
            native = extract_image(path, pipeline=args.pipeline, device=args.device)
            (output / "native.json").write_text(
                json.dumps(native, ensure_ascii=False, indent=2)
            )
            report.update(
                tables=len(native.get("tables", [])),
                pictures=len(native.get("pictures", [])),
            )
            if profile:
                dataset = map_table(native, profile, path)
                structure, data = sdmx_messages(dataset)
                for filename, content in (
                    ("observations.json", dataset.model_dump(mode="json")),
                    ("structure.sdmx.json", structure),
                    ("data.sdmx.json", data),
                ):
                    (output / filename).write_text(
                        json.dumps(
                            content, ensure_ascii=False, indent=2, allow_nan=False
                        )
                    )
                report["observations"] = len(dataset.observations)
            report["status"] = "success" if profile else "extracted_only"
        except KeyboardInterrupt:
            report.update(status="interrupted", error="Interrupted before completion")
            raise
        except Exception as error:
            failed = True
            report.update(status="failed", error=f"{type(error).__name__}: {error}")
        finally:
            report["seconds"] = round(time.monotonic() - started, 3)
            (output / "run.json").write_text(json.dumps(report, indent=2))
            print(json.dumps(report), flush=True)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
