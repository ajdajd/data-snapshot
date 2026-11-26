# Data Snapshot reviewer MVP acceptance — 2026-11-26

The research MVP is complete: a user can upload one PNG, optionally run Docling,
generate and revise a data model, accept it, extract values, save corrections,
resume the session, approve the data and download an SDMX-JSON bundle. The next
task is improving the Data Model page UX. That redesign has not started.

## What was exercised

Six **new, isolated sessions** ran through the actual Streamlit handlers using
`scripts/run_mvp_app_checks.py` and Streamlit AppTest. Proposal, revision and
extraction actions made real OpenRouter calls using `openai/gpt-5.6-luna` with
the current medium-reasoning settings and shared $5 accounting guardrails.
Financing used local standard Docling; the other five exercised the image-only
path. Existing user sessions and earlier trial results were not changed.

Each journey covered upload, proposal, explicit acceptance, extraction, every
component/result view, a saved evidence-note edit, resume in a fresh app instance,
explicit data approval and the actual bytes supplied to the download button.
Numerical corrections, dirty-state guards, revision clearing and stale-result
blocking are also covered by offline tests. The live note edit deliberately kept
the extracted numbers intact for source comparison. A rerun of the finished
journeys skipped all six without further API calls.

AppTest runs the UI logic headlessly. This was **not a browser/visual test or a
human usability study**. Assistant review decisions in these test sessions are
labeled `MVP verification — assistant`.

## Results

All final bundles passed the official SDMX schemas, local DSD/concept/codelist
reference checks, SHA-256 checks and independent decoding back to the reviewed
observations, including scoped context and evidence.

| Core example | Final observations | DSDs/datasets | Source review and limits |
|---|---:|---:|---|
| Income and remittances | 16 printed | 2 | Mean/median values and row associations match. Revised population qualification to exclude remittances; kept unknown currency and uncertain remittance period. |
| Financing | 4 printed | 1 | `100, 100, 98, 0` match. USD-million scale retained; zero stays zero. |
| Regression | 20 printed | 4 | 14 coefficients, two `Yes` results and four firm/survey counts match. Preserved stars as evidence and their scoped significance note; did not invent numerical standard errors. |
| Education | 16 printed + 12 missing | 2 | Ten enrollment labels and six reading percentages match. Unlabelled enrollment slots remain missing under printed-only policy. Preserved separate 2017 and “2014 or latest available” context. |
| Trade modes | 24 estimated | 1 | Eight groups × three modes, all explicitly approximate. Qualitative geometry check only; no exact numerical ground truth. Mode-number/legend associations remain interpretations; unit/year remain unknown. |
| Residence duration, Spanish | 6 printed | 1 | Final `9, 4, 48, 30, 4, 4` match. Sum is 99 as printed; no normalization to 100. |

`complete` describes extraction against the accepted model, not verified
statistical meaning. Education remains `partial`. No corpus-wide accuracy score
or exact-match score for the estimated trade chart is assigned.

Two failures were retained and resolved:

- **Regression proposal:** the first call was billed but failed local validation
  because numeric sample-count results lacked unit coverage. A deliberate
  corrective proposal through the app separated coefficients, text specification
  and sample counts and supplied appropriate unit contexts. No silent retry.
- **Duration extraction:** the first call returned six missing values despite
  visible percentages. A model description saying values should not be extracted
  “at this stage” leaked from proposal into extraction. The extraction prompt now
  explicitly treats such wording as belonging to the earlier phase; the proposal
  prompt requests stage-neutral definitions. An explicit retest produced all six
  printed values. The first extraction and `duration_first_attempt.zip` remain.

## Export contract

The app's **Download SDMX-JSON bundle** control produces:

- `snapshot.png`: the source image.
- `structure.sdmx.json`: SDMX-JSON 2.1.0 structures, concepts and local codelists.
- `data.sdmx.json`: indexed observations linked to those DSDs.
- `reviewed.json`: the accepted model, reviewed observations, corrections,
  provenance, unknowns and omissions.
- `manifest.json`: SDMX versions and SHA-256 hashes of the four payload files.

The encoder reuses `exchange.py`. One DSD/dataset per component/result preserves
numeric versus text types without coercion. Identifying fields become dimensions;
categories get LOCAL codes with source labels. Open text keys get source mappings,
null keys get a missing-key code and scalar results use a singleton technical
dimension. Context attributes retain accepted scope and knowledge status.
Evidence, printed/estimated/missing status and bounds are preserved. Relationships,
questions, full definitions and extraction omissions are retained in annotations.

These snapshot-specific structures use agency `LOCAL` and `meta.test=true`.
External-code harmonization and registry publication are not implemented.
Relationships are local annotations, not registry constraints. Unknown currencies,
source years and irregular wording are preserved rather than forced into external
standard codes. This produces valid exchange messages while retaining the
limits of the reviewed interpretation. There is no additional LLM call for export.

Export requires current accepted data model and reviewed data; drafts, unsaved
changes and stale results are blocked. Standalone `validate_bundle(bytes)` checks
the downloaded package without access to the original workspace or API.

## Issues to address after the MVP

1. **Data Model review is the first priority.** Important meanings, scopes and
   unresolved choices are scattered across editors. A person must understand what
   needs deciding before asking for a revision. Design a clear summary and focused
   questions, with direct forms under secondary advanced editing.
2. **Make extraction policy understandable.** Printed-only versus estimated
   values must be an informed decision, especially for trade and education.
   Missing values can be correct behavior under the selected policy.
3. **Improve proposal failure recovery.** Regression currently exposes technical
   validation feedback and required an expert revision instruction. Show the
   problem and a guided recovery without claiming an invalid proposal succeeded.
4. **Clarify approval scope and revision changes.** Data review displays one
   component/result slice at a time, but Save reviewed data approves the entire
   result set. Make that scope and unreviewed slices visible. LLM revision preview
   also needs a comprehensible comparison before applying it.
5. **Reduce technical friction.** Wide evidence grids, identifiers and nested
   selectors hinder ordinary review. Spanish labels need optional translation
   while retaining original source text. Explain unknown context and partial
   results without requiring SDMX knowledge.

These are recorded follow-ups, not implemented UX changes. The prompt-stage bug
was fixed because it prevented correct value extraction. Review does not currently
provide row creation, bounds editing, assistant-driven value correction,
authentication or a production multiuser workflow.

## Evidence, checks and spending

Artifacts are under
[`data/structured_data_trials/MVP_acceptance_20261126/`](../../data/structured_data_trials/MVP_acceptance_20261126/):
`journeys.json` locates all sessions, `journey.log.jsonl` records actions and running
costs, `acceptance_summary.json` records final counts/checksums, `spending.json`
contains the settlements, and six named ZIP files contain the actual downloads.
Each session retains requests, raw responses, schemas, hashes, proposals, accepted
revisions, generated values and correction history. Core PNG paths are listed in
[`review_design_examples.json`](review_design_examples.json).

| Verification batch | Calls | Cost USD |
|---|---:|---:|
| Proposal/revision, including failed first regression proposal | 9 | 0.02730851 |
| Value extraction, including both duration attempts | 7 | 0.02014980 |
| Total for this verification | 16 | **0.04745831** |

Starting cumulative spend: **$2.03631689**. Final cumulative spend:
**$2.08377520 / $5**, remaining **$2.91622480**, reserved **$0**. Global batch
totals also include previous work; the figures above isolate this verification
using the run-directory prefix. Each settlement records the running total.

**163 focused offline tests passed**, covering the reviewer journey, exporter,
model proposal/review, extraction, accounting, discovery/resume and the existing
metadata-reviewer smoke check. New export checks include text/scalar/open/null
keys, bounds, empty results, scoped context, missing versus zero, modified values,
invalid references/indexes, dropped observations, corrupt ZIP payloads and
unapproved/stale exports. Formatting and whitespace checks passed.
