You are evaluating the coverage of a frozen metadata schema against one held-out data snapshot.

The baseline is the **Data Snapshot Metadata Schema v1.1**. Treat it as authoritative and immutable during this task. You may identify evidence of a coverage gap, but you must not revise the schema or decide that a proposed field should be accepted.

A data snapshot is a self-contained table, chart, map, dashboard, composite figure, or other visual analytical object extracted from an institutional document.

## Evaluation procedure

1. Independently identify reusable metadata concepts explicitly evidenced by the snapshot or its source-document metadata.
2. Compare each concept with the definitions in v1.1.
3. Record one observation for each distinct reusable metadata concept needed to describe the snapshot.
4. Propose a candidate new field only when an in-scope observation has a weak fit or no fit.

Do not infer missing information, use external knowledge, or treat plausibility as evidence.

## Metadata boundary

Metadata describes the snapshot and supports identification, interpretation, organization, retrieval, provenance, or analytical reuse.

The following are outside the schema's scope and must not become candidate fields:

- extracted numerical values
- OCR text or table-cell contents
- chart or table reconstruction
- statistical outputs or model results
- visual formatting details with no descriptive value
- implementation or extraction-pipeline artifacts
- snapshot-specific values presented as field names

Document metadata is evidence only when it materially describes or contextualizes the snapshot. Do not copy the entire document record into the assessment.

## Fit status

Use exactly one status for every observation:

- `covered`: one or more existing fields represent the concept without material loss.
- `weak_fit`: an existing field is related, but using it would distort, omit, or conflate important semantics.
- `no_fit`: the concept is in scope and no existing field adequately represents it.
- `out_of_scope`: the observation is an extraction output or otherwise outside snapshot metadata.
- `uncertain`: the evidence or semantic interpretation is insufficient for a reliable decision.

For `covered` and `weak_fit`, identify the closest existing fields using their exact v1.1 names. A wording difference or synonym is not a new field.

## Evidence and candidate fields

Every observation must cite concise, explicit evidence and state whether it comes from the snapshot, document metadata, or both.

Candidate fields must:

- use a reusable `snake_case` name;
- be supported by one or more `weak_fit` or `no_fit` observations;
- explain why existing fields are insufficient;
- provide operational value for describing data snapshots; and
- remain proposals for later human adjudication.

Do not make an overall recommendation to revise v1.1 and do not claim schema saturation from a single snapshot.
