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
BATCH1_DATA_ROOT = (
    PROJECT_ROOT / "notebooks" / "metadata_extraction" / "data" / "batch1"
)
GOLD_ROOT = PROJECT_ROOT / "notebooks" / "metadata_extraction" / "gold"
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
FLEX_PRICING_USD_PER_MILLION = {
    "gpt-5.6-luna": (0.10, 0.01, 0.125, 0.60),
    "gpt-5.6-terra": (1.00, 0.10, 1.25, 6.00),
    "gpt-5.6-sol": (2.00, 0.20, 2.50, 10.00),
}
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

TARGETED_CALIBRATION_SNAPSHOTS = (
    ("prwp", "figure", "prwp/figure/document_11958451_figure_004.png"),
    ("prwp", "figure", "prwp/figure/document_14861148_figure_004.png"),
    ("prwp", "table", "prwp/table/document_437268_table_005.png"),
    ("prwp", "table", "prwp/table/document_14861148_table_002.png"),
    ("refugee", "figure", "refugee/figure/189_multi-page_figure_001.png"),
    ("refugee", "figure", "refugee/figure/196_multi-page_figure_001.png"),
    ("refugee", "figure", "refugee/figure/197_multi-page_figure_000.png"),
    (
        "refugee",
        "table",
        "refugee/table/060_Yemen-Emergency-COVID-19-Project_table_003.png",
    ),
    (
        "unhcr",
        "figure",
        "unhcr/figure/education_underattack_updatesept23_figure_003.png",
    ),
    (
        "unhcr",
        "figure",
        "unhcr/figure/rbsa_population_data_analysis_sep_2022_figure_009.png",
    ),
    (
        "unhcr",
        "table",
        "unhcr/table/pays_cotiers_-_aperu-en_31_july_2022_v2_table_001.png",
    ),
    (
        "unhcr",
        "table",
        "unhcr/table/unhcr_global_report_2020_-_east_and_horn_of_africa_and_the_great_lakes_table_002.png",
    ),
)

AT_A_GLANCE_SNAPSHOT_PATHS = {
    "refugee/figure/189_multi-page_figure_001.png",
    "refugee/figure/196_multi-page_figure_001.png",
    "refugee/figure/197_multi-page_figure_000.png",
}
C8_FINALIZATION_SNAPSHOTS = tuple(
    snapshot
    for snapshot in TARGETED_CALIBRATION_SNAPSHOTS
    if snapshot[2] not in AT_A_GLANCE_SNAPSHOT_PATHS
)
GOLD_CALIBRATION_SNAPSHOTS = tuple(
    (
        path.relative_to(GOLD_ROOT).parts[0],
        path.relative_to(GOLD_ROOT).parts[1],
        path.relative_to(GOLD_ROOT).with_suffix(".png").as_posix(),
    )
    for path in sorted(GOLD_ROOT.rglob("*.json"))
)

C8_SYSTEM_GUIDANCE = (
    "Go through all fields in the schema one by one. Populate every field supported "
    "by visible evidence, and leave every unsupported field null."
)
C8A_SYSTEM_GUIDANCE = (
    "Populate every schema field supported by visible evidence. Success means that "
    "no supported field is omitted and every unsupported field is null."
)
C8B_SYSTEM_GUIDANCE = (
    "Before returning, re-scan the image against the entire schema and correct any "
    "omissions of fields supported by visible evidence. Leave every unsupported "
    "field null."
)
C8C_SYSTEM_GUIDANCE = (
    "Go through all fields in the schema one by one and populate every field "
    "supported by visible evidence. Leave every unsupported field null. Before "
    "returning, re-scan the image against the entire schema and correct any "
    "supported-field omissions. Do not add fields merely for completeness, but "
    "when visible evidence reasonably supports a field, prefer populating it rather "
    "than omitting it."
)
C9_ANTI_COPY_GUIDANCE = (
    "Examples are illustrative, not default values. Populate a field only when "
    "supported by visible evidence; never copy an example merely to complete the "
    "schema."
)
C12_STRUCTURAL_PLACEMENT_GUIDANCE = """## Structural-placement check

- When repeated groups use the same measure, represent the measure as a variable
  and the groups as categories of a dimension rather than repeated variables.
- For tables, assign `row` and `column` from the direction in which category values
  vary, not from the physical cell containing the dimension label.
- Use `axis_roles` for ordinary or shared chart axes. Use
  `multi_axis_assignments` only when distinct axes of the same dimension must be
  disambiguated.
- Populate `comparisons` only for an explicit contrast or named comparator, not
  for totals, cross-tabulation categories, or measures that merely appear together."""
C13_STRUCTURAL_PLACEMENT_GUIDANCE = """## Structural-placement check

- Populate `presentation_roles` only for tables. Never assign `row` or `column`
  to dimensions in charts or other figures. For tables, assign `row` and `column`
  from the direction in which category values vary, not from the physical cell
  containing the dimension label.
- In charts, when repeated series apply the same measure to different groups,
  represent the measure as a variable and the groups as categories of a dimension.
  Do not apply this rule mechanically to tables; use the visible table structure
  and schema definitions.
- Use `axis_roles` for ordinary or shared chart axes. Use
  `multi_axis_assignments` only when distinct axes of the same dimension must be
  disambiguated.
- Populate `comparisons` only for an explicit contrast or named comparator, not
  for totals, cross-tabulation categories, or measures that merely appear together."""
C8_FINALIZATION_EXPERIMENTS = {"c8br", "c8c", "c8d", "c8dr", "c8e"}
C9_EXPERIMENTS = {"c9", "c9a", "c9b", "c9c"}
GOLD_EXPERIMENTS = {"c10", "c11", "c12", "c13", "c14", "c15"}
TARGETED_EXPERIMENTS = {
    "c7",
    "c7a",
    "c7b",
    "c8",
    "c8a",
    "c8b",
    *C8_FINALIZATION_EXPERIMENTS,
    *C9_EXPERIMENTS,
}

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
    "c7": {
        "label": "C7",
        "treatment": "First canonical example appended to each schema description",
        "output_stem": "calibration7",
        "schema_example_mode": "first",
    },
    "c7a": {
        "label": "C7A",
        "treatment": "All canonical examples appended to each schema description",
        "output_stem": "calibration7a",
        "schema_example_mode": "all",
    },
    "c7b": {
        "label": "C7B",
        "treatment": "All examples appended only to normalization descriptions",
        "output_stem": "calibration7b",
        "schema_example_mode": "normalization",
    },
    "c8": {
        "label": "C8",
        "treatment": "Direct field-by-field completeness instruction",
        "output_stem": "calibration8",
        "completeness_guidance": C8_SYSTEM_GUIDANCE,
    },
    "c8a": {
        "label": "C8A",
        "treatment": "Outcome-first completeness criterion",
        "output_stem": "calibration8a",
        "completeness_guidance": C8A_SYSTEM_GUIDANCE,
    },
    "c8b": {
        "label": "C8B",
        "treatment": "Final schema re-scan for supported-field omissions",
        "output_stem": "calibration8b",
        "completeness_guidance": C8B_SYSTEM_GUIDANCE,
    },
    "c8br": {
        "label": "C8BR",
        "treatment": "Control repeat of C8B on non-composite snapshots",
        "output_stem": "calibration8b_repeat",
        "completeness_guidance": C8B_SYSTEM_GUIDANCE,
    },
    "c8c": {
        "label": "C8C",
        "treatment": "Combined field traversal and final schema re-scan",
        "output_stem": "calibration8c",
        "completeness_guidance": C8C_SYSTEM_GUIDANCE,
    },
    "c8d": {
        "label": "C8D",
        "treatment": "C8C without user-prompt schema duplication",
        "output_stem": "calibration8d",
        "completeness_guidance": C8C_SYSTEM_GUIDANCE,
        "include_schema_reference": False,
    },
    "c8dr": {
        "label": "C8DR",
        "treatment": "Replication of C8D on non-composite snapshots",
        "output_stem": "calibration8d_repeat",
        "completeness_guidance": C8C_SYSTEM_GUIDANCE,
        "include_schema_reference": False,
    },
    "c8e": {
        "label": "C8E",
        "treatment": "C8B without user-prompt schema duplication",
        "output_stem": "calibration8e",
        "completeness_guidance": C8B_SYSTEM_GUIDANCE,
        "include_schema_reference": False,
    },
    "c9": {
        "label": "C9",
        "treatment": "Contemporaneous production control without examples",
        "output_stem": "calibration9",
        "completeness_guidance": C8B_SYSTEM_GUIDANCE,
        "include_schema_reference": False,
    },
    "c9a": {
        "label": "C9A",
        "treatment": "All canonical examples appended to schema descriptions",
        "output_stem": "calibration9a",
        "completeness_guidance": C8B_SYSTEM_GUIDANCE,
        "schema_example_mode": "all",
        "include_schema_reference": False,
    },
    "c9b": {
        "label": "C9B",
        "treatment": "All canonical examples plus anti-copy instruction",
        "output_stem": "calibration9b",
        "completeness_guidance": C8B_SYSTEM_GUIDANCE,
        "schema_example_mode": "all",
        "system_prompt_addendum": C9_ANTI_COPY_GUIDANCE,
        "include_schema_reference": False,
    },
    "c9c": {
        "label": "C9C",
        "treatment": "Targeted geographic-name and category-group examples",
        "output_stem": "calibration9c",
        "completeness_guidance": C8B_SYSTEM_GUIDANCE,
        "schema_example_mode": "c9_targeted",
        "include_schema_reference": False,
    },
    "c10": {
        "label": "C10",
        "treatment": "Schema v1.4 baseline with the unchanged C8E prompt",
        "output_stem": "calibration10",
        "completeness_guidance": C8B_SYSTEM_GUIDANCE,
        "include_schema_reference": False,
    },
    "c11": {
        "label": "C11",
        "treatment": "C10 with deterministic-enrichment fields deferred",
        "output_stem": "calibration11",
        "completeness_guidance": C8B_SYSTEM_GUIDANCE,
        "include_schema_reference": False,
        "extraction_profile": "defer_deterministic_enrichment",
    },
    "c12": {
        "label": "C12",
        "treatment": "C11 with targeted structural-placement guidance",
        "output_stem": "calibration12",
        "completeness_guidance": C8B_SYSTEM_GUIDANCE,
        "include_schema_reference": False,
        "extraction_profile": "defer_deterministic_enrichment",
        "user_prompt_addendum": C12_STRUCTURAL_PLACEMENT_GUIDANCE,
    },
    "c13": {
        "label": "C13",
        "treatment": "C10 with repaired structural-placement guidance",
        "output_stem": "calibration13",
        "completeness_guidance": C8B_SYSTEM_GUIDANCE,
        "include_schema_reference": False,
        "extraction_profile": "full",
        "user_prompt_addendum": C13_STRUCTURAL_PLACEMENT_GUIDANCE,
    },
    "c14": {
        "label": "C14",
        "treatment": "C10 with GPT-5.6 Terra at medium reasoning",
        "output_stem": "calibration14_terra",
        "config_path": C5_CONFIG_DIR / "c14_terra.json",
        "completeness_guidance": C8B_SYSTEM_GUIDANCE,
        "include_schema_reference": False,
        "extraction_profile": "full",
    },
    "c15": {
        "label": "C15",
        "treatment": "C10 with GPT-5.6 Sol at medium reasoning",
        "output_stem": "calibration15_sol",
        "config_path": C5_CONFIG_DIR / "c15_sol.json",
        "completeness_guidance": C8B_SYSTEM_GUIDANCE,
        "include_schema_reference": False,
        "extraction_profile": "full",
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


def estimate_flex_cost_usd(
    usage: dict[str, Any] | None, model: str = "gpt-5.6-luna"
) -> float:
    """Estimate one GPT-5.6 Flex request cost from token usage.

    Parameters
    ----------
    usage : dict[str, Any] | None
        Responses API usage data.
    model : str, optional
        GPT-5.6 model name used for the request.
    Returns
    -------
    float
        Estimated cost in US dollars, or zero when usage is unavailable.

    Raises
    ------
    ValueError
        If the model has no configured Flex pricing.
    """
    if usage is None:
        return 0.0
    pricing_model = next(
        (
            name
            for name in FLEX_PRICING_USD_PER_MILLION
            if model == name or model.startswith(f"{name}-")
        ),
        None,
    )
    if pricing_model is None:
        raise ValueError(f"No Flex pricing configured for model: {model}")
    input_rate, cached_rate, cache_write_rate, output_rate = (
        FLEX_PRICING_USD_PER_MILLION[pricing_model]
    )
    input_tokens = int(usage.get("input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    details = usage.get("input_tokens_details") or {}
    cached_tokens = int(details.get("cached_tokens", 0))
    cache_write_tokens = int(details.get("cache_write_tokens", 0))
    uncached_tokens = max(input_tokens - cached_tokens - cache_write_tokens, 0)
    return (
        uncached_tokens * input_rate
        + cached_tokens * cached_rate
        + cache_write_tokens * cache_write_rate
        + output_tokens * output_rate
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
    schema_example_mode = str(experiment.get("schema_example_mode", "none"))
    completeness_guidance = experiment.get("completeness_guidance")
    system_prompt_addendum = experiment.get("system_prompt_addendum")
    include_schema_reference = bool(experiment.get("include_schema_reference", True))
    extraction_profile = str(experiment.get("extraction_profile", "full"))
    data_root = (
        BATCH1_DATA_ROOT
        if experiment_name in TARGETED_EXPERIMENTS | GOLD_EXPERIMENTS
        else DATA_ROOT
    )
    if experiment_name in GOLD_EXPERIMENTS:
        snapshots = GOLD_CALIBRATION_SNAPSHOTS
    elif experiment_name in C8_FINALIZATION_EXPERIMENTS | C9_EXPERIMENTS:
        snapshots = C8_FINALIZATION_SNAPSHOTS
    elif experiment_name in TARGETED_EXPERIMENTS:
        snapshots = TARGETED_CALIBRATION_SNAPSHOTS
    else:
        snapshots = CALIBRATION_SNAPSHOTS
    baseline_results_path = (
        OUTPUT_DIR / "batch1_results.jsonl"
        if experiment_name in TARGETED_EXPERIMENTS | GOLD_EXPERIMENTS
        else BASELINE_RESULTS_PATH
    )
    _validate_inputs(config_path, data_root, snapshots, baseline_results_path)
    with config_path.open(encoding="utf-8") as file:
        config = json.load(file)
    configured_model = str(config["model"])
    reasoning_effort = str(config["reasoning"]["effort"])
    service_tier = str(config["service_tier"])
    if service_tier != "flex":
        raise ValueError(
            "Calibration runner supports only explicitly approved Flex runs."
        )
    estimate_flex_cost_usd({}, configured_model)
    prior_run_cost = _jsonl_cost(results_path) + _jsonl_cost(errors_path)
    completed_paths = _successful_paths(results_path)
    cumulative_cost = _cumulative_cost()

    print(f"Experiment: {label}")
    print(f"Treatment: {experiment['treatment']}")
    print(f"Model: {configured_model}")
    print(f"Reasoning effort: {reasoning_effort}")
    print(f"Service tier: {service_tier}")
    print(f"Prior experiment cost: ${prior_run_cost:.9f}")
    print(f"Cumulative cost: ${cumulative_cost:.9f}")
    print(f"Cost guardrail: ${MAX_CUMULATIVE_COST_USD:.2f}")
    print(f"Selected snapshots: {len(snapshots)}")
    print(f"User-prompt schema reference: {include_schema_reference}")
    print(f"Extraction profile: {extraction_profile}")
    if dry_run:
        print(f"Already completed: {len(completed_paths)}")
        print("DRY_RUN_OK")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    had_error = False
    for source, artifact_type, relative_path in snapshots:
        if relative_path in completed_paths:
            print(f"SKIP {relative_path}")
            continue
        if cumulative_cost >= MAX_CUMULATIVE_COST_USD:
            raise RuntimeError(
                "Cumulative calibration cost reached the $5.00 guardrail."
            )

        print(f"RUN {relative_path}", flush=True)
        result = extract_metadata(
            data_root / relative_path,
            config_path=config_path,
            user_prompt_addendum=prompt_addendum,
            system_prompt_addendum=system_prompt_addendum,
            completeness_guidance=completeness_guidance,
            schema_example_mode=schema_example_mode,
            include_schema_reference=include_schema_reference,
            extraction_profile=extraction_profile,
        )
        call_cost = estimate_flex_cost_usd(result.usage, configured_model)
        prior_run_cost += call_cost
        common = {
            "snapshot_path": relative_path,
            "snapshot_file_name": Path(relative_path).name,
            "source": source,
            "artifact_type": artifact_type,
            "schema_version": "1.4",
            "model": result.model,
            "response_id": result.response_id,
            "api_status": result.api_status,
            "elapsed_seconds": result.elapsed_seconds,
            "usage": result.usage,
            "estimated_cost_usd": round(call_cost, 9),
            "reasoning_effort": reasoning_effort,
            "service_tier": service_tier,
            "schema_example_mode": schema_example_mode,
            "include_schema_reference": include_schema_reference,
            "extraction_profile": extraction_profile,
            "completeness_guidance": completeness_guidance,
            "system_prompt_addendum": system_prompt_addendum,
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
    if experiment_name in GOLD_EXPERIMENTS:
        return EXPERIMENTS[experiment_name].get("user_prompt_addendum")
    if experiment_name == "c0r" or experiment_name in TARGETED_EXPERIMENTS:
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


def _validate_inputs(
    config_path: Path,
    data_root: Path,
    snapshots: tuple[tuple[str, str, str], ...],
    baseline_results_path: Path,
) -> None:
    """Verify the baseline, configuration, and selected images exist."""
    required_paths = [baseline_results_path, config_path]
    required_paths.extend(data_root / item[2] for item in snapshots)
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
            else estimate_flex_cost_usd(
                record.get("usage"), str(record.get("model", "gpt-5.6-luna"))
            )
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
