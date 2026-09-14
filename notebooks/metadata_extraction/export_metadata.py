"""Export metadata objects from extraction JSONL to individual JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tqdm import tqdm


def export_metadata(input_path: str | Path, output_dir: str | Path) -> int:
    """Export every metadata object in a results JSONL file.

    Parameters
    ----------
    input_path : str | Path
        Extraction results JSONL file.
    output_dir : str | Path
        Root directory for source-specific metadata JSON files.

    Returns
    -------
    int
        Number of metadata files written.

    Raises
    ------
    ValueError
        If a JSONL record is invalid or lacks a required field.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    with input_path.open(encoding="utf-8") as file:
        total = sum(1 for _ in file)

    written = 0
    with input_path.open(encoding="utf-8") as file:
        lines = tqdm(file, total=total, desc="Exporting metadata", unit="snapshot")
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                parsed: Any = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on {input_path}:{line_number}") from exc
            if not isinstance(parsed, dict):
                raise ValueError(f"Invalid record on {input_path}:{line_number}")
            record: dict[str, Any] = parsed

            source = record.get("source")
            snapshot_file_name = record.get("snapshot_file_name")
            metadata = record.get("metadata")
            if (
                not isinstance(source, str)
                or not source
                or source in {".", ".."}
                or Path(source).name != source
            ):
                raise ValueError(f"Invalid source on {input_path}:{line_number}")
            if (
                not isinstance(snapshot_file_name, str)
                or not snapshot_file_name
                or Path(snapshot_file_name).name != snapshot_file_name
                or not Path(snapshot_file_name).stem
            ):
                raise ValueError(
                    f"Invalid snapshot_file_name on {input_path}:{line_number}"
                )
            if not isinstance(metadata, dict):
                raise ValueError(f"Invalid metadata on {input_path}:{line_number}")

            target_dir = output_dir / source
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / f"{Path(snapshot_file_name).stem}_metadata.json"
            target_path.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            written += 1

    return written


def main() -> None:
    """Run the JSONL-to-JSON exporter from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input_path", type=Path, help="Extraction results JSONL file")
    parser.add_argument("--output_dir", type=Path, help="Metadata output directory")
    args = parser.parse_args()
    written = export_metadata(args.input_path, args.output_dir)
    print(f"Exported {written} metadata files to {args.output_dir}")


if __name__ == "__main__":
    main()
