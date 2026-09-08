You are evaluating the coverage and representational adequacy of a frozen metadata schema against one data snapshot.

The baseline is **Data Snapshot Metadata Schema v1.2**. Treat it as authoritative and frozen. Your task is only to assess whether it adequately represents the supplied data snapshot. Do not revise the schema or decide whether a candidate should be accepted.

A data snapshot is a self-contained table, chart, map, dashboard, composite figure, or other visual analytical object extracted from an institutional document.

## Core question

Given the schema, snapshot, and parent-document context, is there any critical or possibly critical reusable metadata information about the snapshot that the schema cannot adequately represent without material semantic or relational loss, and whose omission or inadequate representation would materially impair interpretability, discoverability, or both?

## Evaluation procedure

1. Consider the complete supplied v1.2 JSON Schema, but do not inventory covered information or extract a complete metadata record.
2. Identify only critical or possibly critical reusable snapshot metadata that may lack adequate representation.
3. For each candidate, identify the closest existing paths using exact v1.2 names. Use dot notation and `[]` for array items, such as `variables[].unit` or `dimensions[].category_groups[].categories`.
4. Compare a faithful representation of the evidenced metadata and its relationships with the best representation permitted by those paths.
5. Explain the concrete interpretability or discoverability impairment that could result from omission, distortion, or loss of the relationship.
6. Return `no_critical_gap_found` when no candidate meets the critical or possible thresholds.

A candidate may concern an absent concept, relationship or nesting structure, cardinality, normalization facility, exported constraint, or definition. Do not classify it into one of those categories and do not propose an implementation.

## Critical and possible gaps

A `critical` gap must meet all of the following conditions:

- explicit evidence supports the information;
- the information is reusable snapshot metadata;
- existing paths cannot preserve it without material semantic or relational loss; and
- its absence has a concrete material impact on interpretability, discoverability, or both.

A `possible` gap must still be plausible reusable snapshot metadata with a plausible material impact, but uncertainty remains about the evidence, existing-schema coverage, or materiality.

Do not report information that would merely be useful, convenient, specialized, desirable, or an additional search facet. Do not infer a particular application, interface, user group, search behavior, or workflow. Human review will determine whether each claimed gap is justified.

## Snapshot and document boundary

The snapshot is the object being described. Parent-document metadata is supplied as context and may clarify the snapshot's subject, meaning, provenance, or relationship to its source document.

A candidate must describe the snapshot, the data represented in it, or provenance explicitly attached to it. A fact that describes only the parent document is not a snapshot-schema gap. Parent-document URLs, identifiers, document types, publication dates, authorship, and general attribution belong to the linked document record unless the evidence establishes a distinct snapshot-level role.

For every candidate, explain why the information is metadata about this snapshot rather than only metadata about its parent document. Do not reproduce the document metadata record.

## Metadata boundary

The following are outside the schema's scope and must not become candidates:

- extracted numerical observations or values;
- OCR text or reconstructed table contents;
- statistical estimates, model results, or analytical outputs;
- snapshot-specific values presented as schema concepts;
- visual styling without descriptive significance;
- implementation or extraction-pipeline artifacts; and
- information inferred from plausibility or external knowledge.

An explicitly stated methodological, uncertainty, or provenance note may be metadata even when it contains a number. Evaluate the role of the information, not merely its textual form.

## Output consistency

- `no_critical_gap_found` requires an empty candidate array.
- `critical_gap_found` requires at least one `critical` candidate and may also include `possible` candidates.
- `possible_gap` requires one or more `possible` candidates and no `critical` candidates.
