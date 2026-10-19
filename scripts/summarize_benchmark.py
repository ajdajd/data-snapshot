"""Write paper-style Markdown tables from completed benchmark JSON reports."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

MODELS = {
    "tfid": "TF-ID-Large",
    "doclayoutyolo": "DocLayout-YOLO",
    "yolo11": "YOLOv11 medium",
    "yolo26": "YOLOv26 medium",
}
SOURCES = {"unhcr": "UNHCR / ReliefWeb", "prwp": "PRWP", "refugee": "Refugee PADs"}
METRICS = {
    "Precision": "precision",
    "Recall": "recall",
    "IoU": "mean_iou",
    "Area Precision": "mean_area_precision",
    "Area Recall": "mean_area_recall",
}


def main(argv: Sequence[str] | None = None) -> None:
    """Load available source and corpus reports and write four metric tables.

    Parameters
    ----------
    argv : Sequence[str] | None
        Optional arguments for testing. Uses process arguments when ``None``.

    Raises
    ------
    ValueError
        If a report contains mismatched documents or no reports are available.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Default: <output-root>/report.md.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--docling-root",
        type=Path,
        help="Additional benchmark root containing docling_heron/reports/.",
    )
    args = parser.parse_args(argv)
    models = dict(MODELS)
    if args.docling_root is not None:
        models["docling_heron"] = "Docling Heron"
    reports: dict[str, dict[str, Any]] = {}
    for model in models:
        reports[model] = {}
        for source in ("corpus", *SOURCES):
            relative = (
                Path("corpus.json")
                if source == "corpus"
                else Path("sources") / f"{source}.json"
            )
            root = args.docling_root if model == "docling_heron" else args.output_root
            path = root / model / "reports" / relative
            if not path.is_file():
                continue
            report = json.loads(path.read_text(encoding="utf-8"))
            if report.get("documents_mismatch") != {"only_gt": [], "only_pred": []}:
                raise ValueError(f"Document mismatch in report: {path}")
            reports[model][source] = report["metrics"]["0.5"]["per_class"]
    if not any(reports.values()):
        raise ValueError(f"No benchmark reports found under: {args.output_root}")

    lines = [
        "# Benchmark comparison",
        "",
        "Results from the JSON reports in this directory. Evaluation IoU threshold: **0.5**. Spatial metrics are means over matched detections. Overall metrics come from the pooled corpus report, not averages of source scores.",
        "",
        "Blank cells mean not run; N/A means a metric is undefined. Bold marks the best displayed available value, including ties at three decimal places. Compare identical document selections and account for differences in rendering and preprocessing.",
        "",
    ]
    if args.docling_root is not None:
        lines.extend(
            [
                "Docling uses its native PDF backend, OCR, layout postprocessing, and "
                "reading order; the existing baseline uses PyMuPDF. This compares "
                "complete pipelines, not layout models under identical rendering. "
                "Only figure/table bounds are evaluated; native caption/footnote "
                "links remain separate, and crops are not expanded to include them.",
                "",
            ]
        )
    for split in (False, True):
        for label in ("Figure", "Table"):
            suffix = "by corpus" if split else "overall"
            lines.extend([f"## {label} {suffix}", ""])
            columns = (["Corpus"] if split else []) + [
                "Category",
                "Metric",
                *models.values(),
            ]
            lines.append("| " + " | ".join(columns) + " |")
            lines.append("|" + "---|" * (3 if split else 2) + "---:|" * len(models))
            for source in SOURCES if split else ("corpus",):
                for title, key in METRICS.items():
                    values = [
                        (
                            reports[model][source][label][key]
                            if source in reports[model]
                            else None
                        )
                        for model in models
                    ]
                    best = max(
                        (round(value, 3) for value in values if value is not None),
                        default=None,
                    )
                    cells = [SOURCES[source]] if split else []
                    category = (
                        "Detection"
                        if key in {"precision", "recall"}
                        else "Spatial Accuracy"
                    )
                    cells.extend([category, title])
                    for model, value in zip(models, values):
                        cell = (
                            ("N/A" if source in reports[model] else "")
                            if value is None
                            else f"{value:.3f}"
                        )
                        cells.append(
                            f"**{cell}**"
                            if value is not None and round(value, 3) == best
                            else cell
                        )
                    lines.append("| " + " | ".join(cells) + " |")
            lines.append("")

    output = args.output or args.output_root / "report.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w" if args.overwrite else "x", encoding="utf-8") as file:
        file.write("\n".join(lines))
    print(f"Wrote Markdown report: {output}")


if __name__ == "__main__":
    main()
