"""Run one controlled metadata-extraction calibration experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from data_snapshot.metadata_extraction import extract_metadata
from data_snapshot.metadata_extraction.extraction import _response_format
from data_snapshot.metadata_schema import DataSnapshotMetadata


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "notebooks" / "metadata_extraction" / "data" / "snapshots"
OUTPUT_DIR = PROJECT_ROOT / "notebooks" / "metadata_extraction" / "outputs"
CONFIG_PATH = (
    PROJECT_ROOT
    / "src"
    / "data_snapshot"
    / "metadata_extraction"
    / "config"
    / "default.json"
)
C5_CONFIG_DIR = PROJECT_ROOT / "notebooks" / "metadata_extraction" / "config"
BASELINE_RESULTS_PATH = OUTPUT_DIR / "calibration0_results.jsonl"
MAX_CUMULATIVE_COST_USD = 5.0
FLEX_INPUT_USD_PER_MILLION = 0.10
FLEX_CACHED_INPUT_USD_PER_MILLION = 0.01
FLEX_CACHE_WRITE_USD_PER_MILLION = 0.125
FLEX_OUTPUT_USD_PER_MILLION = 0.60

CALIBRATION_SNAPSHOTS = (
    ("prwp", "figure", "prwp/figure/document_11174028_figure_002.png"),
    ("prwp", "table", "prwp/table/document_11174028_table_007.png"),
    (
        "refugee",
        "figure",
        "refugee/figure/027_Jordan-Emergency-Food-Security-Project_figure_000.png",
    ),
    (
        "refugee",
        "table",
        "refugee/table/001_BOSIB-3f2311b3-9a20-44d3-b637-b3b2b3d21695_table_008.png",
    ),
    (
        "unhcr",
        "figure",
        "unhcr/figure/impact_lby_so_refugees_and_migrants_access_to_food_wash_shelter_november_2018_figure_007.png",
    ),
    (
        "unhcr",
        "table",
        "unhcr/table/rpublique_dmocratique_du_congo_-_points_saillants_de_protection_-_aot_2024_table_000.png",
    ),
)

EXPERIMENTS = {
    "c0r": {
        "label": "C0R",
        "treatment": "Unchanged repeat baseline",
        "output_stem": "calibration0_repeat",
    },
    "c1": {
        "label": "C1",
        "treatment": "OpenAI-compatible schema duplicated in the prompt",
        "output_stem": "calibration1",
    },
    "c1a": {
        "label": "C1A",
        "treatment": "Canonical Pydantic schema with examples duplicated in the prompt",
        "output_stem": "calibration1a",
    },
    "c2": {
        "label": "C2",
        "treatment": "OpenAI-compatible schema plus field-boundary rules",
        "output_stem": "calibration2",
    },
    "c3": {
        "label": "C3",
        "treatment": "C2 treatment plus curated boundary examples",
        "output_stem": "calibration3",
    },
    "c4": {
        "label": "C4",
        "treatment": "Confirmation repeat of C2",
        "output_stem": "calibration4",
    },
    "c5l": {
        "label": "C5L",
        "treatment": "C2 prompt at low reasoning effort",
        "output_stem": "calibration5_low",
        "config_path": C5_CONFIG_DIR / "c5_low.json",
    },
    "c5h": {
        "label": "C5H",
        "treatment": "C2 prompt at high reasoning effort",
        "output_stem": "calibration5_high",
        "config_path": C5_CONFIG_DIR / "c5_high.json",
    },
    "c5x": {
        "label": "C5X",
        "treatment": "C2 prompt at xhigh reasoning effort with 32k output budget",
        "output_stem": "calibration5_xhigh_32k",
        "config_path": C5_CONFIG_DIR / "c5_xhigh.json",
    },
}

BOUNDARY_GUIDANCE = """## Field-boundary guidance

- Preserve the complete visible title or caption in `title`. Also populate
  `document_label` when a visible Figure, Table, Annex, or Exhibit label is present.
- Use `source_text` only for exact visible wording. Never invent source wording for
  a value inferred from visual form or structure.
- Variables are measured concepts, indicators, or metrics. Dimensions classify,
  group, organize, or compare those measures. Do not duplicate a concept as both
  unless the image clearly gives it both roles.
- Coefficient, standard error, count, percentage, and confidence interval are
  statistical forms or qualifiers on the applicable variable; they are not
  standalone measured variables when the measured concept is identifiable.
- Use `category_groups` for explicit group headings and their contained categories.
  Use `panel_titles` only for explicit panels in a multi-panel snapshot, not ordinary
  section headings within one table.
- Express a visible comparative relationship as one comparison, such as
  `Baseline vs Closing Period`, rather than separate unrelated comparison items.
- Put derivation datasets and surveys in `provenance.sources`; put credited agents
  in `provenance.attributions`. Do not repeat a source statement in
  `interpretive_notes` when its meaning is fully represented elsewhere.
- Temporal coverage describes when the represented data apply, not publication or
  footer dates. Normalize visible dates only when the mapping is deterministic.
- Geographic scope is the overall represented area. Use locations for additional
  named places and level for the level at which the data are reported.
- Preserve complete substantive notes that are not fully represented by another
  field. Do not extract numerical observations or reproduce table cells."""

CURATED_EXAMPLES = """## Generic boundary examples

1. A regression table names `Wages` as the dependent variable, lists `Age` and
   `Education` in rows, and uses `Coef` and `SE` columns. Represent `Wages` as an
   outcome variable and `Age` and `Education` as predictor variables. Attach
   coefficient and standard-error statistical forms to the applicable measured
   variables; do not create variables named `Coefficient` or `Standard error`.

2. A table groups district rows under visible province headings and reports `Count`
   and `%` columns. Represent the province headings and contained districts with a
   row dimension and `category_groups`. Represent count and percentage as the
   statistical forms or units of the applicable measure. Do not reproduce cell
   values.

3. For `Source: Survey Alpha and Agency Beta calculations`, use `Survey Alpha` in
   `provenance.sources` and `Agency Beta` in `provenance.attributions` with visible
   role `calculations`. Do not also copy the complete source line into
   `interpretive_notes` unless it contains additional substantive information.

4. If an image visually uses bars but never says `bar chart`, return
   `{"normalized_value": "bar_chart"}` without `source_text`. Source text is only
   exact wording displayed in the snapshot.

5. Use `panel_titles` for explicit headings such as `(A) Urban` and `(B) Rural` in
   a multi-panel figure. Do not treat an ordinary section heading inside one table
   as a panel title."""


def estimate_flex_cost_usd(usage: dict[str, Any] | None) -> float:
    """Estimate one GPT-5.6 Luna Flex request cost from token usage.

    Parameters
    ----------
    usage : dict[str, Any] | None
        Responses API usage data.

    Returns
    -------
    float
        Estimated cost in US dollars, or zero when usage is unavailable.
    """
    if usage is None:
        return 0.0
    input_tokens = int(usage.get("input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    details = usage.get("input_tokens_details") or {}
    cached_tokens = int(details.get("cached_tokens", 0))
    cache_write_tokens = int(details.get("cache_write_tokens", 0))
    uncached_tokens = max(input_tokens - cached_tokens - cache_write_tokens, 0)
    return (
        uncached_tokens * FLEX_INPUT_USD_PER_MILLION
        + cached_tokens * FLEX_CACHED_INPUT_USD_PER_MILLION
        + cache_write_tokens * FLEX_CACHE_WRITE_USD_PER_MILLION
        + output_tokens * FLEX_OUTPUT_USD_PER_MILLION
    ) / 1_000_000


def run_calibration(experiment_name: str, *, dry_run: bool = False) -> int:
    """Run or validate one configured calibration experiment.

    Parameters
    ----------
    experiment_name : str
        Lowercase experiment name from ``EXPERIMENTS``.
    dry_run : bool, optional
        Validate inputs and report the run plan without making API calls.

    Returns
    -------
    int
        Process exit status: zero for success and one for any extraction error.

    Raises
    ------
    FileNotFoundError
        If the baseline results or a selected snapshot is missing.
    RuntimeError
        If the cumulative API cost has reached the approved guardrail.
    """
    experiment = EXPERIMENTS[experiment_name]
    label = experiment["label"]
    output_stem = experiment["output_stem"]
    config_path = Path(experiment.get("config_path", CONFIG_PATH))
    results_path = OUTPUT_DIR / f"{output_stem}_results.jsonl"
    errors_path = OUTPUT_DIR / f"{output_stem}_errors.jsonl"
    prompt_addendum = _prompt_addendum(experiment_name)
    _validate_inputs(config_path)
    with config_path.open(encoding="utf-8") as file:
        reasoning_effort = json.load(file)["reasoning"]["effort"]
    prior_run_cost = _jsonl_cost(results_path) + _jsonl_cost(errors_path)
    completed_paths = _successful_paths(results_path)
    cumulative_cost = _cumulative_cost()

    print(f"Experiment: {label}")
    print(f"Treatment: {experiment['treatment']}")
    print(f"Reasoning effort: {reasoning_effort}")
    print(f"Prior experiment cost: ${prior_run_cost:.9f}")
    print(f"Cumulative cost: ${cumulative_cost:.9f}")
    print(f"Cost guardrail: ${MAX_CUMULATIVE_COST_USD:.2f}")
    print(f"Selected snapshots: {len(CALIBRATION_SNAPSHOTS)}")
    if dry_run:
        print(f"Already completed: {len(completed_paths)}")
        print("DRY_RUN_OK")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    had_error = False
    for source, artifact_type, relative_path in CALIBRATION_SNAPSHOTS:
        if relative_path in completed_paths:
            print(f"SKIP {relative_path}")
            continue
        if cumulative_cost >= MAX_CUMULATIVE_COST_USD:
            raise RuntimeError(
                "Cumulative calibration cost reached the $5.00 guardrail."
            )

        print(f"RUN {relative_path}", flush=True)
        result = extract_metadata(
            DATA_ROOT / relative_path,
            config_path=config_path,
            user_prompt_addendum=prompt_addendum,
        )
        call_cost = estimate_flex_cost_usd(result.usage)
        prior_run_cost += call_cost
        common = {
            "snapshot_path": relative_path,
            "snapshot_file_name": Path(relative_path).name,
            "source": source,
            "artifact_type": artifact_type,
            "schema_version": "1.3",
            "model": result.model,
            "response_id": result.response_id,
            "api_status": result.api_status,
            "elapsed_seconds": result.elapsed_seconds,
            "usage": result.usage,
            "estimated_cost_usd": round(call_cost, 9),
            "reasoning_effort": reasoning_effort,
        }
        if result.metadata is not None:
            _append_jsonl(
                results_path,
                {
                    **common,
                    "experiment": label,
                    "treatment": experiment["treatment"],
                    "metadata": result.metadata.model_dump(
                        mode="json", exclude_none=True
                    ),
                },
            )
            completed_paths.add(relative_path)
            print(f"OK ${call_cost:.9f} {relative_path}", flush=True)
        else:
            had_error = True
            _append_jsonl(
                errors_path,
                {
                    **common,
                    "experiment": label,
                    "treatment": experiment["treatment"],
                    "error_type": result.error_type,
                    "error": result.error,
                    "raw_output": result.raw_output,
                },
            )
            print(f"ERROR ${call_cost:.9f} {relative_path}", flush=True)

        cumulative_cost += call_cost
        print(f"CUMULATIVE ${cumulative_cost:.9f}", flush=True)
        if cumulative_cost >= MAX_CUMULATIVE_COST_USD:
            raise RuntimeError(
                "Cumulative calibration cost reached the $5.00 guardrail."
            )

    print(f"EXPERIMENT_COST ${prior_run_cost:.9f}")
    print(f"CUMULATIVE_COST ${cumulative_cost:.9f}")
    return int(had_error)


def _prompt_addendum(experiment_name: str) -> str | None:
    """Build the prompt treatment for an experiment."""
    if experiment_name == "c0r":
        return None
    guidance: str | None = None
    if experiment_name in {"c1", "c2", "c3", "c4", "c5l", "c5h", "c5x"}:
        schema = _response_format()["schema"]
        heading = "Model-facing Schema v1.3 reference"
        if experiment_name in {"c2", "c3", "c4", "c5l", "c5h", "c5x"}:
            guidance = BOUNDARY_GUIDANCE
        if experiment_name == "c3":
            guidance = f"{guidance}\n\n{CURATED_EXAMPLES}"
    elif experiment_name == "c1a":
        schema = DataSnapshotMetadata.model_json_schema(mode="validation")
        heading = "Canonical Pydantic Schema v1.3 reference, including examples"
    else:
        raise ValueError(f"Unknown calibration experiment: {experiment_name}")
    schema_reference = (
        f"## {heading}\n\n"
        "Use this schema as field-level extraction guidance. The API response "
        "format remains the authoritative output contract.\n\n"
        f"```json\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n```"
    )
    return f"{guidance}\n\n{schema_reference}" if guidance else schema_reference


def _validate_inputs(config_path: Path) -> None:
    """Verify the baseline, configuration, and selected images exist."""
    required_paths = [BASELINE_RESULTS_PATH, config_path]
    required_paths.extend(DATA_ROOT / item[2] for item in CALIBRATION_SNAPSHOTS)
    missing_paths = [path for path in required_paths if not path.is_file()]
    if missing_paths:
        formatted = "\n".join(str(path) for path in missing_paths)
        raise FileNotFoundError(
            f"Required calibration inputs are missing:\n{formatted}"
        )


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    """Append one JSON record to a JSONL file."""
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read JSON objects from a JSONL file when it exists."""
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def _jsonl_cost(path: Path) -> float:
    """Sum recorded or estimated Flex costs in a JSONL file."""
    total = 0.0
    for record in _read_jsonl(path):
        recorded_cost = record.get("estimated_cost_usd")
        total += (
            float(recorded_cost)
            if recorded_cost is not None
            else estimate_flex_cost_usd(record.get("usage"))
        )
    return total


def _cumulative_cost() -> float:
    """Sum all calibration costs currently recorded in the output directory."""
    return sum(
        _jsonl_cost(path)
        for pattern in ("calibration*_results.jsonl", "calibration*_errors.jsonl")
        for path in OUTPUT_DIR.glob(pattern)
    )


def _successful_paths(path: Path) -> set[str]:
    """Return snapshot paths already present in a results JSONL file."""
    return {
        str(record["snapshot_path"])
        for record in _read_jsonl(path)
        if record.get("metadata") is not None
    }


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment", choices=tuple(EXPERIMENTS))
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate inputs without calling the API",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = _parse_args()
    raise SystemExit(run_calibration(arguments.experiment, dry_run=arguments.dry_run))
