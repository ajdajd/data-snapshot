# Internal comparison: v1.1.2 and v1.2

Status: Internal manuscript-development reference; not intended for inclusion
in the paper

## Purpose

This document records how the approved flat v1.1.2 fields correspond to the
later machine-readable v1.2 schema. It prevents later manuscript edits from
mistaking a v1.2 structural decision for a feature of the paper schema.

The v1.1.2 decisions are grounded in the standards crosswalk, artifact
evidence, and human adjudication recorded in
`standards_alignment_findings.md`. The v1.2 outcome is used here only as a
consistency check.

## Field correspondence

| v1.1.2 field | v1.2 representation | Relationship |
|---|---|---|
| `title` | `title` | Same application-facing field |
| `document_label` | `document_label` | Same application-facing field |
| `subject_domains` | `subject_domains[]` controlled terms | Same concept; v1.2 adds structured normalization |
| `subject_summary` | `subject_summary` | Same application-facing field |
| `panel_titles` | `panel_titles[]` | Same flat ordered collection |
| `variable_names` | `variables[].name` | v1.2 groups each variable with its qualifiers |
| `category_dimensions` | `dimensions[].name` | v1.2 represents dimensions as objects |
| `category_labels` | `dimensions[].categories` and `dimensions[].category_groups` | v1.2 preserves the dimension relationship and one explicit grouping level |
| `population_group` | `population_group` controlled term | Same concept; v1.2 adds structured normalization |
| `time_period` | `temporal_coverage.period` | v1.2 preserves source text and supports normalized bounds, relation, and precision |
| `temporal_granularity` | `temporal_coverage.granularity` | v1.2 combines source text with normalized values and optional codes |
| `geographic_scope` | `geographic_coverage.scope` | v1.2 uses a structured place representation |
| `geographic_entities` | `geographic_coverage.locations[]` | v1.2 represents named locations as objects |
| `geographic_level` | `geographic_coverage.level` | Same concept in a structured geographic context |
| `geographic_roles` | `geographic_coverage.locations[].role` | v1.2 associates each role with its location |
| `location_types` | `geographic_coverage.locations[].type` | v1.2 associates each type with its location |
| `units_of_measure` | `variables[].unit` | v1.2 associates each unit with its variable and supports codes and multipliers |
| `currencies` | `variables[].currency` | v1.2 associates each currency with its variable and supports ISO codes |
| `statistical_forms` | `variables[].statistical_forms` | v1.2 associates each form with its variable and supports normalized terms |
| `comparisons` | `comparisons[]` | Same flat source-grounded collection |
| `row_dimensions` | `dimensions[].presentation_roles` containing `row` | v1.2 associates the role with its dimension |
| `column_dimensions` | `dimensions[].presentation_roles` containing `column` | v1.2 associates the role with its dimension |
| `visualization_types` | `visualization_types[]` controlled terms | Same concept; v1.2 adds normalized terms |
| `data_sources` | `provenance.sources[]` | v1.2 groups derivation sources under provenance and adds identifiers |
| `attributions` | `provenance.attributions[]` | v1.2 represents credited agents and roles separately |
| `source_document_title` | Not represented in the v1.2 snapshot model | Internal version-boundary difference |
| `languages` | `languages[]` | v1.2 separates source-visible labels from BCP 47 tags |
| `interpretive_notes` | `interpretive_notes[]` | Same flat collection |
| `project_name` | `project.name` | v1.2 groups project context |
| `project_identifiers` | `project.identifiers[]` | v1.2 supports scheme, issuer, and URI qualifiers |
| `project_components` | `project.components[]` | v1.2 represents components as entity references |
| `intervention_types` | `intervention_types[]` controlled terms | Same concept; v1.2 adds optional normalization |
| `financing_measures` | `financing.measures[]` | v1.2 groups financing context and adds controlled-term structure |
| `funders` | `financing.funders[]` | v1.2 represents funders as entity references |
| `financing_instruments` | `financing.instruments[]` | v1.2 supports controlled terms and exact external codes |
| `analysis_methods` | `analysis_methods[]` controlled terms | Same concept; v1.2 adds optional identifiers and normalization |
| `data_collection_methods` | `data_collection_methods[]` controlled terms | Same concept; v1.2 adds optional DDI-compatible normalization |

## Additional v1.2 structures

The v1.2 representation adds structures that have no direct flat v1.1.2
field:

- reusable controlled terms containing source text, normalized values, codes,
  schemes, and authoritative URIs;
- qualified identifiers with optional scheme, issuer, and URI;
- structured temporal bounds, temporal relation, and precision;
- standard country, subdivision, regional, currency, language, and unit codes;
- variable analytical and axis roles;
- explicit assignments for distinct axes in multi-axis visualizations;
- nonrecursive category groups; and
- machine-enforceable types, cardinalities, vocabularies, and validators.

## Human-decision boundary

The principal divergence is representational. v1.1.2 accepts standards-informed
terminology and semantic distinctions but retains flat fields for direct
inspection. v1.2 operationalizes many of the same concepts through nested,
typed, and validated structures. The differences should not be described as
missing-field evidence against v1.1.2 or as features already evaluated during
the paper's schema-validation exercises.
