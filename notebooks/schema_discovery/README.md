# Data Snapshot Metadata Schema Discovery

Paper 2 research workflow for discovering, validating, and evolving a semantic
metadata schema for data snapshot images.

The data snapshot is the unit of analysis. Parent-document metadata may be
provided as context, but it is not part of the Data Snapshot Metadata Schema.

## Environment

```shell
uv sync --locked --extra notebooks --extra test
uv run --extra notebooks jupyter lab notebooks/schema_discovery
```

Set `OPENAI_API_KEY` in `.env` only when intentionally running API-backed
discovery or labeling cells. Analysis of existing outputs does not require a
live API call.

## Discovery workflow

The tracked notebook sequence records the original schema-development process:

| Stage | Notebooks |
|---|---|
| Broad discovery | `1.0-schema_discovery.ipynb`, `1.1-results_viewer.ipynb` |
| Dataset preparation and analysis | `1.2-snapshots_local_copy.ipynb`, `2.0-analysis.ipynb`, `2.1-eda_discovery_results.ipynb` |
| Field profiling and ontology induction | `3.0-initial_profiling.ipynb`, `3.1-induce_ontology.ipynb`, `3.2-ontology_result.ipynb` |
| Ontology-based adjudication | `4.0-field_labeling_using_ontology.ipynb`, `4.1-results_viewer.ipynb` |
| Canonical concept analysis | `5.0-canonical_field_frequency_analysis.ipynb`, `5.1-canonical_field_cooccurence_analysis.ipynb` |
| Schema-based coverage analysis | `6.0-field_labeling_using_schema.ipynb`, `6.1-results_viewer.ipynb` |
| Paper analysis | `7.0-eda_for_paper.ipynb` |

Prompts live in `prompts/`. The checked-in Markdown outputs are research
artifacts; large source data and most generated tabular outputs are gitignored.

## Validation and evolution

Schema validation is part of the Paper 2 workflow but retained in separate
directories so each executed study remains intact:

- [`../schema_validation1`](../schema_validation1) evaluates Schema v1.1 on a
  held-out corpus and includes the final adjudicated report.
- [`../schema_validation2`](../schema_validation2) performs the confirmatory
  Schema v1.1.1 assessment on the same held-out evidence.
- [`../schema_validation3`](../schema_validation3) repeats the confirmatory
  assessment for Schema v1.2.
- [`../schema_v1_2_representation_stress_test`](../schema_v1_2_representation_stress_test)
  preserves a broader exploratory instrument that was superseded as Validation
  3 and is not an active package.

Validation runners live under `src/data_snapshot/schema_validation1`,
`schema_validation2`, and `schema_validation3`. Their notebooks define the
inputs and execution configurations. Do not rerun live validation cells merely
to check the repository; use the offline tests instead.

```shell
uv run --extra test pytest \
    tests/test_schema_validation2.py \
    tests/test_schema_validation3.py
```

## Canonical outputs

The current maintained schema is implemented in
[`src/data_snapshot/metadata_schema`](../../src/data_snapshot/metadata_schema/README.md).
Generated versioned JSON Schemas, field references, design records, and change
reports live under `docs/schema_v1.2`, `docs/schema_v1.3`, and
`docs/schema_v1.4`.

The Paper 2 manuscript is maintained in
[`docs/schema-discovery_manuscript`](../../docs/schema-discovery_manuscript/README.md).
