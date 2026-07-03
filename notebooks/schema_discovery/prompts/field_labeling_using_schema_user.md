# Data Snapshot Metadata Schema v1.1

{{SCHEMA_MARKDOWN}}

---

### not_in_schema

Definition:

A discovered metadata field that does not correspond to any canonical field in the Data Snapshot Metadata Schema v1.1.

This includes fields that were intentionally excluded from the schema because they primarily represent:

- extracted values rather than metadata
- statistical outputs or model results
- highly snapshot-specific concepts
- implementation artifacts
- concepts outside the scope of snapshot metadata

Examples:

data_values, indicator_value, measure_values, baseline_value, target_value, significance_notation, legend_values, confidence_interval, table_cells

---

Examples associated with each canonical field represent discovered metadata fields that were mapped to that concept during schema development.

They are illustrative rather than exhaustive.

Prefer semantic meaning over exact string matching.

If no canonical field adequately represents the discovered metadata field, assign:

**not_in_schema**


# Metadata Field Profile

metadata_field

{{metadata_field}}

top_description_values

{{top_description_values}}

top_observed_values

{{top_observed_values}}

Assign this discovered metadata field to exactly one canonical metadata concept from the schema.