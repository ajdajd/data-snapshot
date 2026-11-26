# Data Snapshot structured data extraction — working notebook

Started: 2026-11-24 (Asia/Manila). This is the central record of the plan,
decisions, experiments, findings, and open questions. A possible future Paper 3
is motivation for preserving evidence, not a required output of this prototype.

## Current plan

**Decision — 2026-11-26:** the deliverable is tooling plus an interactive review
workflow for **one snapshot at a time**. Follow Approach 1: propose a
snapshot-specific data model, obtain user acceptance, extract the values, and
review them. A bespoke Streamlit app is the starting UI choice. Develop an
end-to-end example and use the next team sync for feedback and corrective action.

Aivin clarified that an LLM should suggest the DSD for a snapshot parsed with
Docling, then extract using an accepted structure. He also noted existing standard
fields/codelists and said formalizing the output can follow extraction. Treat the
early proposal as a readable **working data dictionary/statistical model**; full
SDMX structure encoding and code assignments can follow review. Establishing what
the values mean still comes before extracting them into that model.

The intended workflow is:

1. **Open PNG and preprocess.** Run Docling and retain its native output alongside
   the original image. Keep the image available as evidence throughout review.
2. **Propose a working model.** Use the image and Docling output to suggest the
   analytical components, identifying categories, measured results, units,
   qualifications and relationships needed for this snapshot. Preserve source
   labels and expose ambiguity instead of guessing.
3. **Review and accept the model.** Let the user edit directly or ask the LLM for
   a revision. Explain proposals in plain language, save revisions and record
   which model version was accepted.
4. **Extract observations.** Use the image, relevant Docling evidence and accepted
   model with OpenRouter Structured Outputs. Save long-format observations,
   evidence and unresolved content against that exact model version.
5. **Review extracted data.** Keep the image visible while the user checks and
   edits the results or requests a targeted model revision. Changing the accepted
   statistical model marks dependent extracted data as needing review again.
6. **Formalize and export.** Map appropriate concepts/codes, construct the formal
   DSD, validate the structure and reviewed observations, and export SDMX-JSON.
   CSV remains an optional later export. Provisional reviewed JSON must not be
   described as SDMX-compliant until this step succeeds.

**Standard fields and codelists:** reuse suitable SDMX concepts and verified
codes where their meaning matches the evidence. Do not require every snapshot to
contain REF_AREA or TIME_PERIOD, turn an unspecified date into a reporting period,
or invent a country/unit to fill a code. Preserve raw source labels and proposed
mappings separately. Generic shape/type/reference validation remains useful
throughout; final SDMX encoding is deferred, not all validation or interpretation.

**Starting UI:** a separate Streamlit reviewer with the image on the left and
Model, Data and Export stages on the right. Structured editors hold the current
working result; a compact assistant area explains or proposes revisions for the
user to apply. Include saved drafts/resume, versioned generated and reviewed
records, visible changes, unresolved issues and explicit acceptance of both model
and data. Use plain labels in the main UI; advanced views can expose JSON and
SDMX details. Follow the metadata reviewer's interaction patterns without a
runtime dependency on its models, forms or storage module.

**Next implementation milestones:**

1. Use the eight image-grounded cases in `review_design_examples.json` to exercise
   model proposal, direct editing, acceptance, extraction and data corrections.
   This design pack is now prepared; see the review-design section below.
2. Build the independent per-snapshot model-proposal/revision and accepted-model
   extraction path, saving inspectable JSON before a UI depends on it. Reuse the
   existing OpenRouter execution/accounting utilities; keep the old fixed-DSD
   pipeline as an experimental baseline. Proposal/revision and local
   draft/acceptance are now implemented and checked offline. A live proposal
   quality check and extraction against the accepted working model remain next.
3. Add the small Streamlit workspace around that path and demonstrate one complete
   review session. Exercise its controls against all eight design cases as it grows.
4. Show the workflow at the next team sync: proposed model, user correction,
   accepted revision, extracted values, review and the current export state.
   Gather feedback before investing in more interaction complexity. Finish formal
   SDMX export after extraction/review works, clearly labeling any interim JSON.

Luna medium remains the initial model reference from the completed extraction
comparison; its quality for snapshot-specific model proposals still needs to be
established. Docling is the preprocessing baseline in the intended workflow.
Its incremental value over image-only LLM input remains an experiment to conduct,
rather than an established quality improvement. RapidAI, custom frontend work and
PDF detection/cropping integration remain deferred.

**Discovery closed and saved:** all 210 development images were attempted;
209 records passed structural validation and one failed a repeated-ID
relationship rule. Retain the valid records and the failed raw response for later
use. Shared-DSD consolidation/design and the proposed 202-image coverage study are
parked; they are not prerequisites for this MVP. The seven-batch DSD strategy was
not activated. Detailed closeout, archive paths and costs are recorded below.

Current recorded workstream spending: **$1.96872847 / $5**; remaining
**$3.03127153**, with no outstanding reservations. The original dropped request
was written off on user instruction, as documented in the recovery record.

## Agreed scope and constraints

- Input: PNG images. Do not connect this prototype to the PDF detection/cropping
  workflow. Note PDF-only restrictions when evaluating other libraries.
- Primary output: SDMX-JSON. CSV is a possible later export, not the design target.
- Code must remain independent of `metadata_extraction` and `metadata_schema`.
- The initial extraction trials used the same 102 images selected for metadata
  extraction. The directory
  `/home/ajd/hf_datasets/data_snapshot_metadata_gold` contains metadata JSON only;
  all 102 filenames match PNGs in `/home/ajd/hf_datasets/data-snapshot/snapshots`.
  The gold metadata is not an inference input or numerical ground truth.
- The completed discovery used Paper 2's 210 development images. The associated
  202-image validation set remains unused in this workstream. The shared-DSD study
  is retained for later use; it is not the current delivery strategy.
- Propose a working model per snapshot and permit the components required by its
  evidence. A single shared DSD, or a fixed figure/table split, is not a constraint
  on the interactive workflow.
- Record model versions and their reasons for change; keep raw extractions,
  model-proposed revisions and human-reviewed records distinguishable.
- Do not invent missing dates, frequencies, units, category meanings, confidence
  levels, or values. Keep extraction corrections distinguishable from raw output.
- Use `uv` in `/home/ajd/data-snapshot`. Hand lengthy installations/downloads to
  the user; do not replace the existing runtime with an unbounded latest stack.

## Representation decisions

SDMX defines the standard building blocks. A Data Structure Definition (DSD)
specifies the dimensions, measures, attributes, and representations of a particular
family of statistical datasets. A DSD can be generated or adapted by the workflow;
it need not be supplied manually before every image.

Native extraction records visible text and structure: cells, headers, spans,
coordinates, and chart data. The statistical model follows from that evidence;
it assigns the meanings required to identify and interpret observations. It is
not a separate source of facts or another metadata extraction dependency.

For example, the income image shows Mean and Median as columns. Long observations
use `(income category, summary statistic) -> value`. A renderer could show the same
observations as a table or figure without changing their statistical structure.

### Model review and data review

The initial feasibility work separated automated extraction from a deferred review
workflow. The 2026-11-26 decision brings both into the deliverable, with two
distinct acceptance points: accept the snapshot's statistical model, then review
the extracted values and their associations. Keep the backend independently
testable while adding the UI that supports these interactions. There is no new
structured-data review app implemented yet. Discovery and the eight-case design
pack are saved; the proposal/revision and draft/acceptance backend is now ready
for the subsequent value-extraction and UI increments.

### Review design pack — 2026-11-26

Prepared `docs/data_extraction/review_design_examples.json` after visually
reopening all eight PNGs. It records each image path/hash, a working statistical
interpretation, an illustrative proposal defect, direct editing controls, an
equivalent assistant instruction, a data-correction scenario, source-visible
anchors, acceptance checks and unresolved questions. Six cases are the C1 core;
Shona and a hierarchical results-framework table add breadth. Existing Docling
`examples.json`, frozen discovery prompts and experimental DSD profiles are
unchanged.

These are **hand-authored design examples**, not new LLM outputs, accepted DSDs,
a full numerical gold set or the only valid statistical decomposition. Deliberate
proposal/value defects are UX exercises, not claims about saved model outputs.
The source images support the anchors; the proposed interpretation and interaction
need team/user feedback. The design pack does not consolidate the parked D2 study.

| Case ID | Model decision to exercise | Direct edit / data review |
| --- | --- | --- |
| `income` | Separate labor income from remittances; preserve mean/median and the remittance-excluded total. | Scope the male/age note to labor income, leaving remittance applicability unresolved. Correct an illustrative mistyped Agriculture mean to printed 5930. |
| `financing` | Preserve monetary scale and the IBRD/IDA component relationship. | Select the parent Total Financing for the of-which item. Retain 0.00 as zero and apply millions scale once. |
| `regression` | Coefficients, firm/survey counts and Yes model-specification content have different roles. | Add count kind with firms versus country surveys; retain each sector's context. Preserve 0.433** and its stated significance threshold without inventing a p-value or numeric standard error. |
| `education` | Two panels have different identifying fields, units and time qualifications. | Edit Panel B's percent unit and qualified period without changing Panel A. Preserve printed versus unlabelled enrollment values. |
| `trade` | A valid group-by-mode model exists although no bar result is printed. | Leave unit unspecified; choose printed-only or explicitly allow image estimates. Axis ticks cannot substitute for observed results. |
| `duration` | Spanish category text and uncertain interval boundaries matter. | Restore Toda la vida as a separate category; retain source labels if translations are added. Preserve the 99% displayed total without normalizing. |
| `shona` | Five irregular periods, population-based shares and whiskers of unknown meaning. | Remove invented quarterly frequency and 95% confidence wording. Geometry-derived points/bounds remain estimates; unexplained whiskers remain unexplained. |
| `results_framework` | Indicator hierarchy, per-indicator units, reporting roles and dates coexist. | Assign correct parent/unit to percentage children; retain Closing Period rather than assert Actual. Keep the cropped final indicator unresolved. |

#### Proposed workspace

One snapshot session, with its image always available on the left. On the right:
**Model**, **Data**, **Export**, plus an assistant area for the current stage.
Keep original Docling/model outputs available as references. Preserve independent
components within one snapshot; do not make users open a new session per panel.

The Model view consists of editable cards/tables:

| Card | User-facing fields and controls |
| --- | --- |
| Components | Name and “What does one result represent?”; add/separate components when their interpretation differs. |
| Identifying fields | Display name, meaning and source category labels; editable rows with stable internal identities. Retain raw labels separately from optional translations/display labels. |
| Results | Result name/meaning and number or categorical-text type. A numeric-only observation editor cannot preserve all regression content. |
| Units and scale | Source wording, interpreted unit/scale and Applies to component/result/indicator selectors. An unknown unit is an explicit state, not an invitation to guess. |
| Time and reporting roles | Raw source period/date, time basis, source-year wording and Baseline/Closing Period-type role as separate concepts. No forced regular frequency or observation date. |
| Qualifications | Text, source location, interpretation/source distinction and Applies to selectors. Scope to a component or selected categories instead of blanket image-wide inheritance. |
| Relationships | Child and parent item/indicator selectors; retain context across components without silently treating totals as ordinary peers. |
| Extraction policy | Printed values only by default; explicit opt-in to image estimates per component. Retain the method, limitations and unresolved uncertainty marks. |
| Questions | Source ambiguity, its affected content and resolution: leave unresolved, clarify from source, or add clearly marked user-provided context. |

Scope selectors use named components and category values; do not require the user
to write JSON paths or executable conditions. Shared context and component-level
overrides must be visible, with no silent overwrite. SDMX field IDs/codes can be
an advanced view later; they are not mandatory form labels for the first review.

For income, an illustrative scope correction is:

| Field | Proposed value | User's working edit |
| --- | --- | --- |
| Qualification | Male workers aged [14,35] | Same source wording |
| Applies to | Entire snapshot | Labor income component only |
| Remittance applicability | Silently inherited | Unresolved |
| Source | Note below table | Same image evidence; scope interpretation recorded separately |

The user can make this direct edit or ask the assistant for it. An assistant
response proposes a revision with visible differences; it does not overwrite the
accepted model automatically. Direct changes form the working draft; saving it
does not call the model. Preserve original evidence when recording user context.

The Data view displays each component's observations with meaningful identifiers,
numeric/categorical value, unit/scale, source text/location, printed/estimated
method and review/omission flags. A source-like pivot may aid comparison, while
the saved representation remains long format. Corrections create a reviewed
layer; source text and raw generated values remain intact. Do not recompute
source totals, normalize rounded shares or convert scale without an explicit
reviewed transformation and retained source values.

#### Acceptance and session behavior

1. **Save draft:** persist local working edits and questions for later resume;
   no LLM call or acceptance is implied.
2. **Ask for revision:** explicitly request a billable proposal; show differences
   and let the user apply it. Retain the existing cumulative spending guardrail.
3. **Accept model:** save an immutable accepted model version with image/evidence
   identity. Check valid types and references, unique identifiers and intelligible
   result/association definitions. Do not demand answers absent from the image.
4. **Extract values:** an explicit action using that accepted revision; record
   usage and retain the result's model-version link. Widget reruns must not repeat
   requests. A model edit creates a new draft and marks dependent data as needing
   review; old extractions are retained, not silently migrated or discarded.
5. **Save reviewed data:** preserve corrections, unresolved content and the review
   decision. Review acceptance is separate from extraction completeness: a person
   may review a partial extraction without claiming the whole image was recovered.
6. **Export:** reviewed interim JSON can retain a partial result and its omissions.
   Show SDMX formalization/export as pending until that implementation validates
   the actual structure and observations. JSON syntax validity is not SDMX
   compliance or proof of image accuracy.

In printed-only mode the trade and Shona cases have no exact numeric result
labels. Their models can still be accepted, while numerical extraction remains
explicitly incomplete. The education case has 16 printed results and 12 unlabelled
enrollment slots. For the results framework, seven indicators have both dates
and values visible (14 numeric results), while the final female-resilience label
is cropped before its dates/values. Save that indicator as incomplete rather than
inventing zero or claiming complete coverage.

The team-sync walkthrough should demonstrate one ordinary scope correction, one
component-specific unit/period correction, and one unresolved/estimated-value
case, including save/reload and the distinction between model acceptance and data
review. This is a starting interaction design to revise from observed use.

#### Implementation implications

The next backend increment needs a per-snapshot working model supporting multiple
components, scoped context, row-specific units, numeric/categorical content and
evidence/uncertainty. The existing fixed-DSD numeric extractor remains useful as a
baseline; its single shared dimension/attribute contract cannot serve as the
working model for all eight examples unchanged. Reuse its execution, accounting
and validation patterns without changing the frozen experiment's meaning.

For the later Streamlit implementation, the official agent skills look relevant
for editable tables, chat, state and testing:
[CLI skills](https://docs.streamlit.io/develop/api-reference/cli/skills) and
[coding-agent guide](https://docs.streamlit.io/develop/concepts/ai-agents/coding-agents).
The lockfile pins Streamlit 1.63.0, but it is not installed in the current
environment. Enable the review extra while preserving the existing environment
extras, then verify the pinned CLI supports skills and install project-local
guidance. No environment update or skill installation was performed in this step.

Checks for the design pack: all eight source images were visually reopened;
case IDs, paths and image hashes are consistent; the six core paths match C1;
source anchors/correction scenarios were read against the images. No paid calls,
new Docling runs, application code or final SDMX schema were created. Current
recorded spend remains **$1.96872847 / $5**, remaining **$3.03127153**.

### Snapshot-model backend — 2026-11-26

Implemented the first backend increment for Approach 1, independently of metadata
extraction/schema/reviewer modules. It uses existing dependencies and does not
require an environment rebuild or Streamlit installation.

- `working_model.py`: strict Pydantic working-model contract. Supports multiple
  components, component-local key/category/result identities, preserved source
  labels and optional display labels, numeric/text result definitions, scoped
  context, relationships, questions and a printed-only/allow-estimates policy.
  This is a local review model before formal SDMX encoding, not a chosen DSD.
- `model_proposal.py`: prepares or executes one PNG-plus-Docling proposal or
  reviewer-instructed revision using separate system/user prompt files, Structured
  Outputs and the existing execution/spending guardrails. Defaults to offline.
- `model_review.py`: snapshots source evidence, saves human edits or explicitly
  applied proposals as local drafts, and records acceptance of a specific model
  version. All review-store operations are local and make no API calls.

**Evidence boundary:** the native Docling file must have a sibling extraction
`run.json` whose source image hash matches the PNG and whose conversion status is
successful. The request includes relevant document content, layout references,
cells and picture/chart metadata. Document name/origin metadata and embedded
image assets are excluded. The original image is the primary evidence; Docling
and prior-model text are not trusted instructions. Literal source placeholders
cannot be substituted into prompt instructions by the template renderer.

**Proposal boundary:** every output must pass the working-model contract before
`proposed_model.json` is written. Checks include unique local IDs, valid component/
result/category scopes, resolvable relationship references and explicit units for
numeric results, including unresolved units. Source, interpreted and user-provided
claims have distinct provenance requirements. An initial proposal without reviewer
instructions cannot enable image estimates or invent user-provided evidence.
Unknowns/questions can remain unresolved; no registry codes are required.

Proposal output is not accepted or applied automatically. Raw responses, schema,
settings, projected evidence, source/current-model hashes, instructions and usage
are retained. Invalid/incomplete results keep their billed costs, with no repair
or retry calls. The current Luna-medium settings and shared $5 journal remain in
use; existing fixed-DSD and discovery prompts/configuration were not changed.

**Review boundary:** a session snapshots the PNG, native JSON and extraction run
report and keeps versioned models plus acceptance history in `session.json`.
Writes are serialized under a file lock and atomically replace the state file.
Direct edits create a new draft; unchanged content is a no-op. Real changes clear
current acceptance while retaining previous revisions/acceptances. Applying an
LLM proposal checks its raw output, image/Docling hashes and starting draft hash;
a stale response cannot overwrite newer user edits. Saving/accepting also requires
the revision expected by the caller. Acceptance includes model/source hashes and
a reviewer label; that label is not an authentication mechanism. Only the current
`accepted_revision` pointer is approval for the current model.

CLI entry points:

```bash
uv run --no-sync python -m data_snapshot.structured_data_extraction.model_proposal --help
uv run --no-sync python -m data_snapshot.structured_data_extraction.model_review --help
```

The review CLI supports `init`, `save`, `apply`, `accept` and `show`. `show` can
export an editable model copy; `save` imports its changes as a new draft. Do not
edit session history, raw responses or provenance files to make a correction.
The module README contains source-matched income setup and review commands.

Added `tests/fixtures/working_models.json`, hand-authored schema stress fixtures
from all eight design cases. They exercise multiple panels, note scope, units by
category/indicator, categorical model status, category hierarchies and unresolved
uncertainty. They are not LLM-generated proposals or an independently adjudicated
semantic gold set.

Verification: **106 relevant tests passed** (33 new model/review cases plus the
73 existing extraction/discovery/accounting cases). This includes strict response
schema shape, all eight fixture models, invalid references and claim states,
matched Docling input, offline key/client isolation, literal-placeholder handling,
billed invalid proposals, direct scope edits, stale revision rejection, source/
history/proposal tampering, unknown-field acceptance and atomic-save failure.

Also exercised the real income PNG/native pair through both CLIs, without API
calls. Inspectable artifacts are in
`data/structured_data_trials/model_proposal_backend_20261126/`:

- `income_prepare/`: real request/evidence/schema snapshots; `status=prepared`,
  `api_attempts=0`.
- `income_session/`: local input snapshots and an empty review store; draft
  revision 0, no accepted model and no purported human acceptance.

Limits/next work: no live model-proposal quality trial, value extraction against
this working model, data-review store, Streamlit UI or final SDMX conversion has
been implemented in this increment. The validator checks structure/references and
the presence of unit context, not exhaustive scope coverage/conflicts or factual
image correctness; reviewer interpretation still matters. The eight models
demonstrate representability, not automatic extraction accuracy. Current recorded
spend remains **$1.96872847 / $5**, with **$3.03127153** remaining and no new paid
calls in this step.

### Discovery closeout — 2026-11-26

The user completed the discovery exercise and chose to retain it for later use
before proceeding with the snapshot-specific interactive approach. D2 attempted
all **210 images**, producing **209 structurally validated records** and **one
validation failure**, with no pending images or unsettled charges. Each corpus
contributed 35 figures and 35 tables; the failure is one refugee table.

The 209 valid records contain **396 analytical units, 2,271 image-local requirement
records, 757 relationships and 842 ambiguity records**. These counts are not a
canonical concept inventory or evidence of DSD coverage. The records have not
undergone a complete image-grounded semantic adjudication or consolidation.

Failed image:
`refugee/099_PAD2358-ARABIC-PAD-LebanonHealthResilienceArabicPAD_table_001.png`.
Its raw response repeats `u1` inside one relationship's `related_ids`. The original
response, failure report and billed usage are retained without repair, relabeling
as success or another API call.

Saved artifacts:

- `docs/data_extraction/discovery_20261126/records.jsonl`: all 209 valid records,
  unchanged in meaning, with image/request identifiers and source-attempt links.
- `docs/data_extraction/discovery_20261126/failures.json`: failed raw candidate,
  reason, input identity and original run report, explicitly unvalidated.
- `docs/data_extraction/discovery_20261126/summary.json`: counts, corpus/type
  breakdown, costs, disposition and accounting/review limits.
- `docs/data_extraction/discovery_20261126/manifest.json` and `archive.sha256`:
  archive-entry inventory and checksums.
- `data/structured_data_archives/discovery_20261126.zip`: portable local bundle of
  D1/D1b/D1c/D2 evidence, all 210 source PNGs, the shared spending journal, exported
  records and relevant code/configuration/tests/lockfile snapshots. This archive
  is under the gitignored data directory; the compact exports above are eligible
  for source control. No Git stash, commit, upload or deletion was performed.

Rechecked all frozen image/request identities, validated-record/raw-output
agreement, JSON schemas, ID/reference rules and billed-cost totals. The archive
excludes credentials and lock files and is checked against its per-file hashes.
Original experiment directories remain at
`data/structured_data_trials/D2_discovery_development_20261125/` and the preceding
pilot directories. The archive is for preservation, not a new runtime input or a
selected DSD/template library.

D2 recorded cost: **$1.00927379**. Workstream recorded total:
**$1.96872847 / $5**; remaining **$3.03127153**; outstanding reservations **$0**.
The user's write-off of the initial dropped call is preserved as such, not
reported as provider-verified zero billing. No API calls were made during
closeout. Consolidation, further shared-DSD development and the 202-image coverage
assessment are parked. Historical protocols and results below describe that
earlier workstream and do not override the current plan.

### Open-discovery instrument — 2026-11-25

The immediate next step is a small **development calibration pilot**, followed by
freezing the discovery instrument before the main 210-image run. This stage
discovers requirements for representing analytical data, rather than proposing
metadata fields or exhaustively transcribing every value.

Draft materials are separate from the existing DSD-conditioned extraction prompts:

- `src/data_snapshot/structured_data_extraction/prompts/discovery_system.md`
- `src/data_snapshot/structured_data_extraction/prompts/discovery_user.md`
- `src/data_snapshot/structured_data_extraction/schemas/discovery_record.schema.json`

Each request receives one PNG independently. It receives no candidate DSD,
experimental extraction profile, standard codelists, canonical concept inventory,
previous discovery records or parent-document metadata. Corpus/type labels and
filenames remain outside the model input. The existing standards research is
retained for consolidation and design after independent discovery.

The JSON envelope records analytical units, provisional requirements and their
function in each unit, source evidence, relationships, a few representative
observation examples, ambiguities and other analytical content needing attention.
Names and functions are open text, not selections from a statistical vocabulary.
Local IDs provide traceability only. Preserve rare distinctions; do not impose a
target number of requirements. Separate exact source text from interpretation,
and allow visual evidence without a text quote. Discovery does not require
digitizing unlabelled values or forcing spatial/categorical content into a cube.

Use the six C1 development images for the initial instrument pilot. Start with
Luna medium, the current extraction reference; the C1 comparison did not establish
its performance on open discovery. Check each pilot record against its source:

- Does it discover requirements rather than fill the experimental DSD's fields?
- Are distinct panels, qualifications and relationships accounted for?
- Are examples and interpretations supported by visible evidence?
- Are rare requirements and unresolved ambiguities retained?
- Are IDs unique and references resolvable, without unsupported assertions?

Revise the instrument if necessary, then freeze its prompts/schema and record
their hashes for the main run. Preserve image hashes, model/settings, raw outputs,
validation results and usage alongside each record. The eventual runner needs
local checks for ID uniqueness and reference integrity in addition to JSON Schema
validation; neither check establishes factual correctness.

After discovery, pool requirements with evidence links, consolidate their meanings
and relationships, and then compare them with existing DSD components. Human
review governs conceptual distinctions and the resulting representation. Batch
boundaries do not trigger automatic DSD changes. The 202 validation images are
reserved for assessing the subsequently frozen representation.

**Status:** independent discovery runner implemented and the initial six-image
pilot completed; see the pilot review below. The existing extraction CLI still
uses the experimental DSD and must not be treated as open discovery. Record the
updated running total after every paid batch, including pilots.

Offline checks passed: JSON Schema validity, strict object shapes, acceptance of
open candidate names and empty lists, and rejection of missing evidence and
unexpected fields. Synthetic fixtures tested format only, not discovery quality
or live-provider compatibility.

### Open-discovery pilot D1 — 2026-11-25

Implemented `python -m data_snapshot.structured_data_extraction.discovery` as a
separate task. It uses independent discovery prompts/schema and accepts a PNG,
fresh output directory, model configuration and batch ID. Its default is offline;
`--execute` permits one API attempt. Extraction and discovery share the existing
PNG request builder, one-attempt execution and persistent spending guardrail.
Neither discovery nor its request preparation loads a DSD. Discovery outputs are
requirements records, not SDMX observations.

Validation checks JSON shape, image-wide ID uniqueness, resolvable example and
relationship references, and distinct IDs within each relationship. Invalid
responses retain raw output and billed cost; there are no automatic repair calls.
All **61 relevant tests passed**, including the existing extraction, exchange and
spending tests and eight discovery cases. Black and whitespace checks passed.

D1 reused the six C1 development images: one figure and one table per corpus.
Model: **Luna medium**, default service tier, 12,000 output-token ceiling, one
independent call per image. The requests contained no DSD, prior discovery result,
filename or parent-document metadata. All six calls completed and passed schema
and reference validation: **seven analytical units and 44 provisional
requirements**. This is a count of image-local findings, not 44 canonical DSD
components or a coverage score.

| Image | Units / requirements | Source-image review |
| --- | --- | --- |
| PRWP trade-policy figure | 1 / 7 | Keeps region/mode pairing, scale, legend and numbered-mode note; records missing exact bar values and unresolved correspondence of mode numbers to legend labels. |
| PRWP TFP table | 1 / 8 | Keeps sector/term/result relationships, significance, dummy-variable inclusion, firm counts, survey counts and standard-error qualification. |
| Refugee education figure | 2 / 10 | Separates panels, sex/grade enrollment in thousands and country reading percentages; preserves distinct time qualifications and missing exact bar values. |
| Refugee financing table | 1 / 6 | Keeps US-dollar/millions scale, printed zero, precision and the indented “of which” relationship; invents no country, time or financing status. |
| UNHCR duration figure | 1 / 5 | Keeps Spanish duration labels and percentages, lifetime versus bounded-duration distinction and unknown referent country; source-year meaning stays unresolved. Analytical prose was also returned in Spanish. |
| UNHCR income table | 1 / 8 | Keeps mean/median, exclusion of remittances from total, labor-income population note and source basis; flags uncertain remittance applicability, unspecified currency and absent calendar month. |

Review was performed by the assistant against all six source images; these
records have not been independently human-adjudicated. The outputs discover
requirements instead of filling the experimental DSD's dimensions. Formatting,
visual association and provenance sometimes appear as separate requirements or
escape records; consolidation must decide their representation rather than
turning every candidate into a DSD component. Multilingual candidate names can be
reconciled at consolidation while retaining original wording and evidence.

**Instrument issue found:** evidence text sometimes joins distinct labels/cells
with invented separators or ellipses. Some `observed_examples` are constructed
descriptions instead of literal source text. The TFP standard-error quote also
normalizes source punctuation. These are evidence-fidelity issues even where the
underlying requirement is useful; schema validation cannot catch them. The income
record also shows that context links on representative examples need review:
the labor-income population requirement is retained but not linked uniformly to
every labor-income example. Discovery records are not final extracted datasets.

Revised the system prompt to require one contiguous source fragment per evidence
entry, separate entries for separate fragments, no inserted punctuation/ellipses
or spelling corrections, and literal-only `observed_examples`. Schema and
candidate vocabulary remain unchanged. A focused D1b check uses the two charts
with repeated joined quotes (PRWP trade and refugee education). Original D1
prompts, schema, requests, responses and fingerprints remain preserved.

D1 artifacts: `data/structured_data_trials/D1_discovery_pilot_20261125/`.
`manifest.json` freezes inputs/configuration and prompt/schema hashes;
`offline/` holds previews, `live/` raw responses and validated records, and
`runs.json` the reports. `run_pilot.py` verifies frozen inputs and resumes without
repeating attempted calls. A sandbox DNS failure during the initial free pricing
lookup made **zero generation attempts** and is retained separately under
`preflight_network_failure_01/`; the subsequent network-enabled run succeeded.

D1 billed **$0.02205570**, bringing the workstream total to **$0.94626322 / $5**;
remaining **$4.05373678**, with no unresolved reservations at batch completion.
The full 210-image discovery run has not started. D1b/D1c results and updated
running totals follow below.

**D1b: literal evidence check.** Both repeated chart calls completed and passed
schema/reference validation. The trade chart now quotes axis labels and legend
entries separately, and its constructed visual examples became empty lists.
The education chart likewise uses separate source fragments, preserves both
panels and their periods, and distinguishes printed enrollment examples from
unlabelled magnitudes. It yielded two units and 12 requirements versus D1's
two/10: local discovery granularity varies between calls and counts are not a
completeness score. The joined/elliptical quote issue was not observed in these
two follow-up records. This does not establish universal OCR fidelity.

D1b artifacts: `data/structured_data_trials/D1b_discovery_quote_check_20261125/`.
Billed **$0.00893466**; workstream total **$0.95519788 / $5**; remaining
**$4.04480212**, with no unresolved reservations at batch completion.

**D1c: context/result distinction.** D1b's trade chart inserted the source labels
`SAR`, `Cross border` and the axis tick `80` into `observation_examples`, explicitly
describing them as context rather than bar values. These belong in requirements
and evidence, not result examples. Clarified that observation examples must be
reported analytical results, numeric or categorical, and must remain empty when
no result values are printed. A single focused trade-chart call checks this
clarification; this is an instrument revision rather than a DSD revision.

The D1c call completed and passed schema/reference validation. Its observation
example list is empty, as intended, while requirements retain the categories,
scale, series associations, substantive note and unresolved mappings. The source
quotes remain separate or contiguous fragments; no exact bar values are invented.
The record splits the three series into separate candidate requirements, unlike
earlier runs: consolidation must reconcile this variation without treating every
series label as a new universal concept.

D1c artifacts: `data/structured_data_trials/D1c_discovery_context_check_20261125/`.
Billed **$0.00425680**; workstream total **$0.95945468 / $5**; remaining
**$4.04054532**, with no unresolved reservations at batch completion. Combined
D1/D1b/D1c cost: **$0.03524716 for nine generation calls**. The failed initial
pricing lookup incurred no generation charge.

**Decision:** use the revised discovery instrument **v0.1.0** for development.
`D1_discovery_pilot_20261125/review.json` records the decision, each batch's cost
and running total, and final prompt/schema/config hashes. D1c contains the final
material snapshots. No canonical concept inventory or DSD has been selected.
Do not mix the pilot's earlier prompt versions into a main run that claims a
single frozen instrument; generate all main-run records with the final version.

Revalidated all nine saved records and their request contracts, reconciled billed
costs against the shared journal, and confirmed no outstanding reservations.
Additionally, all six original C1 extraction request contracts remain unchanged
after sharing the execution code. The full discovery run, consolidation and
202-image representation-coverage assessment remain ahead; the pilot establishes
instrument usability rather than general DSD coverage or guaranteed completeness.

### Resumable development discovery D2

Prepared `scripts/run_structured_data_discovery.py` for the user to execute the
main **210-image** development discovery. Uses Luna medium and discovery
instrument v0.1.0, with 35 figures and 35 tables from each of PRWP, refugee and
UNHCR. This is independent open discovery; no DSD, standards inventory or prior
discovery record enters a model request. The 202 validation images are not inputs.
The six pilot images will receive fresh main-run records under the same final
instrument as all other development images.

`config/discovery_instrument.json` records the calibrated prompt/schema/settings
hashes. Preparation verifies the exact 210 PNGs, group counts, image hashes,
request fingerprints and supported input bounds, and snapshots the instrument.
Resuming verifies those identities again. Each pending call also checks its
request against the frozen contract before execution. Changed inputs/settings
stop the run rather than silently changing the discovery instrument.

Prepared output directory:
`data/structured_data_trials/D2_discovery_development_20261125/`.
Preparation made **no API calls**. Initial status: 210 pending, no failures or
blocked attempts, workstream spend **$0.95945468 / $5**, remaining **$4.04054532**.
The manifest anchors the existing shared spending journal by a prefix hash;
deleting, resetting or rewriting that history prevents resume.

Run or resume using the **same output directory**:

```bash
cd /home/ajd/data-snapshot
uv run --no-sync python -u scripts/run_structured_data_discovery.py \
  --output-dir data/structured_data_trials/D2_discovery_development_20261125 \
  --execute
```

Omit `--execute` to prepare/verify offline and refresh the progress summary.
The script appends UTC progress/error messages to `runner.log` automatically;
no `tee` is required. Monitor from another terminal:

```bash
tail -f /home/ajd/data-snapshot/data/structured_data_trials/D2_discovery_development_20261125/runner.log
```

`summary.json` is updated atomically after each attempt and at shutdown. It
contains completed/failed/pending/blocked counts, per-image paths/reasons, batch
cost, workstream running total, reservations and remaining funds. Logs also print
these totals after each attempt. Per-image artifacts live under
`runs/<image-id>/attempt_001/`, with raw API responses, text, validated
`discovery.json`, request/schema/settings snapshots, billing and failure reports.
Further attempt folders are created only for confirmed pre-API failures.

Resume behavior:

- Validate and skip completed records; preserve and skip known billed failures.
  Continue other pending images, without paid retries or automatic repair calls.
- Stop on a preflight failure; rerunning may retry it only when the report confirms
  zero API attempts and no ledger reservation. Preserve its previous attempt.
- Stop for unknown charges, missing attempt reports, unresolved reservations,
  exceeded input bounds, changed frozen evidence or edited results. A Ctrl+C or
  disconnection during an in-flight request may require billing reconciliation
  before resume; it never triggers an automatic duplicate paid request.
- Reject a second process on the same output directory. The existing per-call
  ledger lock and cumulative $5 cap remain active.

The process exits nonzero if an executed run ends incomplete or with failures;
the summary distinguishes failures from pending/blocked work. Report back
`summary.json` and relevant `runner.log` errors after running. Billed failures
need review and are not counted as successful coverage. Processing is sequential;
this script does not introduce DSD revision rounds or activate the previously
discussed seven-batch design.

Verification: **73 relevant tests passed**, including 12 batch cases covering
resume, duplicate prevention, changed inputs/results, ledger reset, known billed
failures, preflight recovery, uncertainty and locking. The actual 210-image
manifest was prepared and then verified again through the offline resume path;
all 210 remain pending and cumulative spending is unchanged. Black and whitespace
checks passed. No additional dependencies or downloads were needed.

### D2 dropped-call recovery — 2026-11-25

The first user-run request, PRWP `document_10002285_table_002.png`, returned HTTP
400, `Request path cannot be relayed`. The runner stopped with its $0.03029350
allowance unresolved, as designed. The user explicitly authorized ignoring the
dropped call and fixing the issue.

Non-generating, empty-body probes reached both API routes and returned normal
missing-input validation errors. The configured Responses path matches the
[official endpoint](https://openrouter.ai/docs/api/api-reference/responses/create-responses).
The failed request was retried once as `attempt_002` with an **identical request
hash**, including model, image, prompts, schema and provider ceilings. It completed
and passed discovery validation in 39.166 seconds. This points to a transient
routing rejection; no endpoint, prompt or instrument change was needed.

Released the original reservation through an append-only zero-dollar settlement
on the user's instruction. This is a **user-authorized write-off**, not a
provider-verified zero charge. Preserved the original failure report and recorded
the authorization, accounting adjustment and successful retry in
`D2_discovery_development_20261125/dropped_request_reconciliation.json` and the
runner log. No automatic paid-retry policy was added.

The diagnostic retry cost **$0.00533124**. D2 recorded batch cost:
**$0.00533124**; workstream recorded total: **$0.96478592 / $5**; remaining:
**$4.03521408**. Refreshed and checked summary: **one discovered, 209 pending,
zero failed/blocked images and zero outstanding reservations**. Resume the same
batch command; it skips the successful image. No other main-run calls were made
by the assistant during this recovery.

### DSD protocol and independent LLM path

The user agreed to combine reusable concepts from the candidate DSDs and develop
the Data Snapshots definition incrementally. Reuse the original **210 development
and 202 validation images**. These are the Paper 2 schema-study samples drawn
from Paper 1's corpus, rather than a separate Paper 1 schema split. Initial image
inspection is pre-research problem understanding; retain the original split.

Verified locally: 210 unique development filenames, 202 unique validation
filenames, and zero filename overlap. Their source directories are:

- Development: `notebooks/schema_discovery/data/snapshots/`.
- Validation: `notebooks/schema_validation1/data/snapshots/` (also reused by the
  subsequent metadata-schema validations).

The earlier proposed sequence below is retained as workstream history. The
artifact-first framework in the current plan and open-discovery protocol
supersedes its batch-by-batch refinement interpretation:

1. Review development images for the statistical structures they contain,
   including their dimensions, measures, units, qualifications and relationships.
   Start with small batches spanning all three corpora; record requirements and
   reasons for each design change rather than adding every possible field.
2. Select/adapt concepts and representations from the reviewed standards, then
   test whether the provisional DSD faithfully represents contrasting development
   artifacts. Resolve indicator/statistic distinctions, multiple breakdowns,
   reporting roles, missing context and composite components explicitly.
3. Freeze the DSD version and the coverage-assessment instructions, then assess
   representational coverage on all 202 validation images. Record full/partial/
   unsupported coverage and the reasons, by corpus and statistical structure.
   This is a fresh assessment of numerical/analytical content; the earlier metadata
   validation outcomes do not establish DSD coverage.
4. Keep LLM extraction correctness separate from DSD coverage. Compare candidate
   models and prompts on development examples using a fixed DSD and reviewed
   numerical/semantic references. Do not tune prompts/models on the 202 before
   their final assessment. If validation leads to revisions, version and report
   the changes; a revised assessment of that set is not a new held-out result.

The entire 210-image development review and 202-image coverage assessment have
not been conducted yet. They do not require paid extraction calls to begin.

The user requested an independent OpenRouter implementation in this R&D repo,
following `/home/ajd/data-snapshot-pipeline` as an implementation reference only.
Production integration remains a separate later exercise. New entry point:
`python -m data_snapshot.structured_data_extraction.llm`. It imports neither
metadata module, accepts one PNG, and has separate JSON settings and system/user
prompt files. It does not load Docling or GPU models. The `structured_llm` extra
requires only the already-used JSON Schema dependency in addition to base packages.

The default is **offline preparation**: it does not load dotenv, construct an API
client or send any request. It saves inspectable prompts/schema/settings with
image bytes omitted, the DSD/config snapshots, image/request hashes and a report.
An explicit `--execute` is required for the implemented future live path, which
uses OpenRouter's Responses endpoint and Structured Outputs. Automatic SDK retries,
automatic correction calls and model fallback are not enabled. Failure responses
retain available raw output, status and usage; incomplete/invalid output cannot
become a successful SDMX result. Partial and unsupported content are explicit.

`profiles/snapshot_indicators.json` is a **working design artifact**, LOCAL
`SNAPSHOT_OBSERVATIONS(0.1.0)`, not a selected/frozen general DSD. It combines
indicator/category/comparison concepts, statistical operation, population/sex/age,
reference area, source reporting period, observation role, units, model and term.
Attributes describe scale, bounds, confidence, significance, source status and
notes. Per-observation evidence records original number text, location and
printed-versus-estimated extraction. Source terminology remains uncoded; no claim
of compatibility with institutional indicator/code lists is made. `REPORTING_PERIOD`
is deliberately a string until time normalization is designed. Missing context
remains unknown. Multiple independent breakdowns, geographic hierarchies,
continuous coordinates and overlapping reporting-role distinctions remain design
questions for the development review.

The DSD configuration generates a strict response model. Python rejects missing/
extra fields, nonfinite or incorrectly typed numbers, duplicate full keys,
inconsistent completion status, and missing evidence for estimates. It serializes
validated observations and evidence through the same exchange writer as the
original Docling table example, validating against the official vendored SDMX-JSON
schemas. These checks establish software behavior, not image accuracy or domain
interoperability. See the module README for file details and an offline command.

**Cost decision:** the initial no-cost preparation phase was followed by explicit
authorization for the smoke test and a **$5 cumulative workstream budget** on
2026-11-25. Each batch must record its cost and running total. The user selected
Luna as the small, inexpensive working reference; a larger model comparison can
wait until a specific unresolved issue warrants it. See the spending ledger and
live smoke-test findings below.

Offline verification: prepared the real income PNG in
`data/structured_data_trials/llm_offline_income_20261125_01/`; `run.json` records
`execution_requested: false`, `status: prepared`, and `api_attempts: 0`. The API
key was not loaded. Original split filenames/counts are retained locally in
`data/dsd_review/20261125/sample_split.json`. The locked dependency update adds
only the `structured_llm` extra; all package versions remain unchanged.
The final focused check passed **42 tests** across the independent LLM and
existing Docling/table-mapping suites, including official SDMX schema validation,
numeric attributes, component annotations, partial results and preserved failure
evidence. Black formatting, `git diff --check`, and the locked dependency check
passed. Tests use injected fake Responses clients; none incurred API costs.

### OpenRouter budget, reference model and smoke test — 2026-11-25

Use the accounting/reporting pattern in
[`calibration_lab.md`](../../notebooks/metadata_extraction/calibration_lab.md),
with an independent ledger for structured extraction. The new **$5 budget starts
at zero for this workstream**; historical metadata-calibration spending is not
charged again. Do not reuse historical direct-OpenAI Flex prices for these calls.
[OpenRouter usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting)
returns billed `usage.cost`, which is retained with tokens, response ID and output.

Implemented in `structured_data_extraction/spending.py` and the independent LLM
runner. Every live call appends its reservation and final billing to
`data/structured_data_trials/openrouter_spend.jsonl`, under a process lock. Each
entry and `run.json` includes batch cost, running billed total, reserved funds and
remaining budget. `--batch-id` identifies the experiment. The ledger persists
across runs. Missing/invalid cost information retains the reservation rather than
counting a call as free; a reported charge is counted even if extraction fails.

Preflight snapshots the public model catalogue and reserves full-context input
plus the configured output ceiling using the highest relevant published rates,
including long-context and cache-write tiers. Provider price ceilings are sent
with the request. No call is sent when the allowance cannot fit the remaining
budget. This allowance is deliberately conservative and may block costlier models
until a tighter verified input bound is available; it is not a cost prediction.
SDK retries, correction calls and provider/model fallback remain disabled.

| Batch | Model/settings | Calls | Billed batch cost | Running total | Budget remaining |
|---|---|---:|---:|---:|---:|
| S0_income_luna | GPT-5.6 Luna, medium reasoning, default service tier, 12,000 output-token ceiling | 1 | $0.00556775 | $0.00556775 | $4.99443225 |

No other paid batch was run. Add a row and report the cumulative total after every
subsequent batch, including failed or inconclusive experiments.

**Reference decision:** use **`openai/gpt-5.6-luna`, medium reasoning**, as the
fixed working reference for DSD/extraction development. Its catalogue snapshot
identifies `openai/gpt-5.6-luna-20260709`. Reference means a stable model/settings
baseline for experiments; image-grounded human review supplies the correctness
reference. It does not mean that model output is gold or that Luna is proven best.

Sol was considered because metadata calibration C15 recovered more reviewed
content than Luna, while also introducing structural overfill. That is evidence
about a different task. The user preferred the smaller/cheaper Luna for this
workstream; no Sol call was made. Model/pricing snapshots are retained in
`data/structured_data_trials/model_review_20261125/models.json`. Current standard
short-context catalogue rates are Luna $0.20/$1.20 and Sol $4/$20 per million
input/output tokens; rates and tiers must be rechecked for any future experiment.
[Luna](https://openrouter.ai/openai/gpt-5.6-luna),
[Sol](https://openrouter.ai/openai/gpt-5.6-sol).

**S0 result:** the income PNG completed in **30.453 seconds**, returning 16
observations. All **16 numerical values and 16 category/Mean-or-Median associations**
match the manually transcribed source. Both SDMX-JSON exchange messages passed
the official vendored schemas. Currency and observation period remained unknown;
the ALCS 2013–14 wording was retained as source context rather than asserted as
the observation period. Afghanistan was retained from the visible title.

One material semantic issue remains: both remittance observations inherit the
male-workers/age-[14,35] restriction even though the note explicitly describes
labor income. This restriction is not established for remittances by the crop.
Therefore the model's `complete` result is **not fully semantically verified**.
The original output remains unchanged, with the review saved separately.

Usage: 4,814 input tokens (4,811 reported cache-write tokens), 3,637 output tokens
(334 reasoning tokens). OpenRouter reported **$0.00556775**, with no unresolved
reservation. The preflight allowance was $0.5466000 and was released on settlement.
This was default-tier OpenRouter processing, not the older Flex calibration path.

Artifacts: `data/structured_data_trials/llm_smoke_income_20261125_01/` contains
the request/config/DSD/pricing snapshots, raw response and output, observations,
SDMX structure/data, `run.json`, and `review.json`. This is one smoke test on a
development image, not a coverage assessment or a model-comparison experiment.
Verification after adding spending controls: **51 focused tests passed**, including
persistent batch totals, preflight budget refusal, unresolved-charge retention,
pricing tiers, existing extraction behavior and official SDMX schema validation.
Black and `git diff --check` passed. No additional paid calls were made by tests.

### C1 — controlled reference-model comparison (protocol, 2026-11-25)

The user authorized a Luna/Terra/Sol comparison before selecting the development
reference model. The proposed seven development batches are deferred. Compare
`openai/gpt-5.6-luna`, `openai/gpt-5.6-terra`, and `openai/gpt-5.6-sol`, all at
medium reasoning, default service tier, and the same 12,000-token output ceiling.
Use one first-pass call per image/model, six development images, 18 calls total.
No prompt/DSD tuning, automatic repair, retry or fallback during the comparison.
The earlier income smoke test is historical context, not a reused C1 result.

Purposive sample: one figure and one table from each corpus, all verified members
of the original 210-image development set. The six cases cover unlabelled grouped
trade-restrictiveness bars (`document_10455617_figure_003`), firm-level TFP
regressions (`document_6213782_table_001`), the two-panel enrollment/nonreading
figure (`054_Sudan-Basic-Education-Emergency-Support-Project_figure_001`), project
financing (`040_Iraq-COVID-19-Vaccination-Project_table_000`), Spanish residence
duration percentages (`acnur_anlisis-madre_de_dios_vf_figure_024`), and the existing
income table (`108733-revised-public-wb-unhcr-policy-brief-final_table_000`).

Before model calls, freeze image hashes, the DSD/config snapshots, request-contract
hashes, numerical references and interpretation rubric in
`data/structured_data_trials/C1_model_comparison_20261125/`. The image/prompt/schema
contract for each case must match across models. References are never model input.
The existing DSD/prompts are held unchanged, including known interpretation limits.

There are **60 printed numeric reference observations** and **36 unlabelled-bar
estimates**. Printed values require exact value/association matches. Geometry
references use predeclared absolute tolerances: 2 restrictiveness-axis units and
15 thousand pupils for unlabelled pyramid bars. These are approximate image
references, not raw-data truth. Report coverage and additions separately from
accuracy; omission of difficult values must not improve apparent accuracy.

The preregistered rubric has five interpretation checks per image (30 per model),
scored 1 / 0.5 / 0 for correct / partial / missing-or-wrong. It checks keys, units,
statistical forms, significance, footnote scope, demographic associations, source
versus observation periods, zero/missingness, printed/estimated status and
unsupported assertions. Distinguish explicit DSD limitations from model mistakes.
Review the image and output directly; a model is never another model's gold.

Budget preflight now supports these three GPT-5.6 tiers using a conservative
request-specific bound: UTF-8 bytes of request text/schema, a 4,096-token framing
allowance, and unresized 32-pixel patch coverage with the documented 1.2 image
multiplier plus rounding allowance. See
[OpenAI vision-token rules](https://developers.openai.com/api/docs/guides/images-vision).
Other model families retain full-context reservation. Image payload bytes are not
miscounted as text tokens. Actual input usage is checked against the bound; a
breach stops the arm for audit. Published worst-tier prices and provider rate
ceilings remain in force, with the same persistent $5 ledger. This avoids reserving
a million-token input for each small experimental request.

Run each model arm with `scripts/run_structured_data_comparison.py`; it verifies
the frozen contracts and resumes without repeating already attempted calls.
Record per-model batch cost and running workstream spend after each arm. A missing
settled charge stops the arm; budget insufficiency stops before generation.
Cost/latency are observed for this run and cache state, not controlled throughput
estimates. Prefer Luna unless a more expensive tier materially improves this
development assistance on reviewed evidence. One replicate per case is a pilot,
not a statistically precise ranking or a coverage validation.

#### C1 running cost ledger

| Arm | Calls | Billed arm cost | Running workstream total | Remaining from $5 |
|---|---:|---:|---:|---:|
| Luna medium | 6 | $0.03024877 | $0.03581652 | $4.96418348 |
| Terra medium | 6 | $0.30305300 | $0.33886952 | $4.66113048 |
| Sol medium | 6 | $0.58533800 | $0.92420752 | $4.07579248 |

The running total includes the earlier $0.00556775 smoke test. Luna returned five
`complete` and one `partial` extraction, with no schema/serialization failures.
All outputs remain original. One manual reference typo (Manufacturing/Foreign-owned
coefficient 0.423 -> 0.433) was corrected after enlarging the source PNG, with an
audit record in `reference_corrections.json`; model output was not changed.

#### C1 results and reference decision

All **18 API calls completed** and generated exchange files that passed the
vendored official SDMX-JSON schemas. There were no retries, fallbacks, truncated
responses or unsettled charges. The input/prompt/schema contract was verified
against the frozen hashes for every actual request. All three models consumed
exactly **33,239 input tokens** across the same six images. The largest output
was 7,212 tokens, below the common 12,000-token ceiling; the ceiling did not bind.

| Model (medium reasoning) | Printed values correctly captured / 60 | Bar estimates within tolerance / 36 | Interpretation rubric / 30 | Billed cost | Observed mean time/image |
|---|---:|---:|---:|---:|---:|
| Luna | 58 | 36 | 27.0 | $0.03024877 | 27.00 s |
| Terra | 60 | 36 | 29.0 | $0.30305300 | 27.28 s |
| Sol | 60 | 36 | 29.0 | $0.58533800 | 27.78 s |

The two missing Luna observations are the **51 and 35 country-survey counts** in
the regression table. It retained them in source-note text but did not represent
them as separate numerical observations. Its other 58 printed values and all
their reviewed associations are correct. None of the models produced a wrong
numeric value among the matched observations or an additional unmatched numerical
observation. Estimated chart values are within the predeclared tolerances; this
does not establish exact recovery of the source's unprinted raw data.

The interpretation rubric is a structured visual-review aid, not a statistical
accuracy estimate. This pilot's transcriptions and scores come from assistant
inspection of the images; independent human adjudication has not been performed.
Scores by case:

| Case | Luna / 5 | Terra / 5 | Sol / 5 |
|---|---:|---:|---:|
| PRWP grouped bars | 5 | 5 | 5 |
| PRWP regression | 4 | 5 | 5 |
| Refugee PAD education composite | 4.5 | 4.5 | 5 |
| Refugee PAD financing | 5 | 5 | 5 |
| UNHCR Spanish duration chart | 5 | 5 | 5 |
| UNHCR income table | 3.5 | 4.5 | 4 |

Material observations from direct image/output review:

- **Luna:** retains the source footnote but again overextends male-worker/
  age-[14,35] restrictions to remittances. It places `Monthly` in the reporting-
  period field, mixing frequency with observation time. Regression survey counts
  remain only in notes. Its omission record describes control entries generically
  as Yes/No rather than retaining the actual Yes values.
- **Terra:** separates firm and country-survey counts, preserves the Yes controls
  as explicit nonnumeric omissions, and scopes the male/age restriction correctly.
  It assigns `ALCS 2013-14` to reporting period: the source qualification remains
  visible, but source provenance and observation time are still mixed.
- **Sol:** also captures the survey counts and scopes demographics correctly.
  It expresses enrollment as `pupils` with `UNIT_MULT=3`, which is clearer than
  Luna/Terra's scale word `thousand` plus a separate multiplier of 3. However, it
  asserts `2013-14` as the income observation period without the source qualification.
  Neither larger model eliminates interpretation errors.
- **All three:** preserve explicit zeros, financing subsets, 1% significance
  notation, sector/term associations, Spanish duration bands and their unadjusted
  99% rounded sum. They avoid inventing a numeric standard error or an unspecified
  country for the financing crop. Their reported `partial` statuses reflect
  different caution about nonnumeric context, not API/schema failure.

The enrollment-unit deduction is for an unclear base counted unit, not an error
in the number read from the chart. The period deductions distinguish a measurement
frequency or a visibly source-qualified year (partial credit) from an unqualified
claim of observation time. Full check-level scores and notes are in
`interpretation_review.json`; numeric matches, omissions and method checks are in
`numeric_review.json`. No extraction was rewritten to agree with the review.

Observed costs are cache-dependent: Luna read 15,776 cached input tokens, compared
with 10,965 for each larger model. An illustrative all-uncached calculation using
ordinary short-context input/output list prices gives $0.03221620 / $0.31166200 /
$0.60255600 for Luna/Terra/Sol respectively. This illustration excludes actual
cache-write billing and is not the spending ledger. It leaves the same cost
ordering; Luna's warmer cache does not explain away the approximately 10x/19x
observed cost gap. Reasoning tokens were 2,475 / 2,498 / 4,270 respectively.
The small observed latency differences are not evidence of a general speed ranking.

**Decision: retain Luna medium as the routine development reference.** The larger
tiers show useful but limited structural improvements on this pilot, while all
require image-grounded review. Their approximately 10x/19x costs do not justify
replacing Luna for routine development at this point. Terra/Sol remain potential
diagnostic comparators for specific unresolved cases; no automatic escalation
workflow or additional paid run is introduced. This is a cost-benefit decision
from six purposively selected cases, not a claim that Luna is universally best.

The comparison itself cost **$0.91863977**. With S0, total workstream spend is
**$0.92420752 of $5**, with **$4.07579248 remaining** and no pending reservations.
All artifacts, frozen configs, raw responses, review scripts, fingerprints and
`comparison_summary.json` are retained in the C1 experiment directory. The larger
development-batch discussion remains deferred; none of those batches has run.

Next DSD/prompt refinements suggested by this comparison (not applied mid-run):
clarify base unit versus multiplier, source period versus observation period versus
frequency, footnote scope across different measures, and numerical counts embedded
inside explanatory cell text. Keep these representation questions distinct from
the choice of model. Software verification after the budget-bound update: **53
focused tests passed**, including request-size/patch accounting and billed failures
when an input bound is exceeded. Black and `git diff --check` also passed.

The gap after Docling includes assigning statistical roles and meanings,
selecting/adapting a DSD, mapping observations to it, and serialization/validation.
A DSD describes the structure; it does not itself correct extraction errors.

### Exchange version

Use **SDMX 3.1.0** and **SDMX-JSON 2.1.0**. Their version numbers describe different
specifications. [AI4Data's dissemination standards guide](https://worldbank.github.io/ai4data/cookbook/ai-ready-dissemination/standards/)
lists SDMX 3.1. The [official data schema](https://json.sdmx.org/2.1.0/sdmx-json-data-schema.json)
identifies that pairing. Metadata Editor's bundled JSON 2.0 schema concerns
reference metadata and is not an observation-data exchange requirement.

### Worked example: SDMX, the DSD, and the actual numbers

SDMX supplies the vocabulary and rules for statistical exchange. A DSD is a
specific statistical schema written using those rules. SDMX-JSON is one encoding
for exchanging the definitions and data. A dataset contains the observations.
The DSD is itself an SDMX object: it is not a competing standard or an extra
extraction model. See [SDMX overview](https://sdmx.org/about-sdmx/) and the
[DSD definition](https://fmrwiki.sdmx.io/12.3.0/information-model/SDMX-maintainables/DataOrMetadataStructureDefinition/).

Our verified income crop begins with these two rows:

| Income category | Mean | Median |
|---|---:|---:|
| Agriculture | 5930 | 4800 |
| Manufacturing | 7496 | 7000 |

Docling recovers cell text and table structure. Our reviewed mapping says the
first column supplies income categories, and the next two columns are summary
statistics. In long form, those same four observations become:

| CATEGORY | STATISTIC | OBS_VALUE |
|---|---|---:|
| Agriculture | Mean | 5930 |
| Agriculture | Median | 4800 |
| Manufacturing | Mean | 7496 |
| Manufacturing | Median | 7000 |

The corresponding **DSD** defines these fields:

| Component | SDMX role | Meaning | Current representation |
|---|---|---|---|
| CATEGORY | Dimension | Which income category? | String |
| STATISTIC | Dimension | Which summary statistic? | String |
| OBS_VALUE | Measure | What reported income/remittance amount? | Double |

`(CATEGORY, STATISTIC)` identifies an observation within this dataset. The
**data** supplies `Agriculture`, `Mean`, and `5930`. The DSD defines the fields and
their roles, rather than containing the list of measured numbers. Our current
DSD uses uncoded strings; it does not yet enumerate Mean/Median in a code list.
The mapping profile separately checks those expected headers. Standard code
lists can later make those representations more specific and interoperable.

The output files separate these concerns:

- [`native.json`](../../data/structured_data_trials/20261124_gpu_standard_01/108733-revised-public-wb-unhcr-policy-brief-final_table_000/native.json): Docling's extracted cells and document structure.
- [`observations.json`](../../data/structured_data_trials/20261124_gpu_standard_01/108733-revised-public-wb-unhcr-policy-brief-final_table_000/observations.json): our readable intermediate observations, their keys, original text and evidence references.
- [`structure.sdmx.json`](../../data/structured_data_trials/20261124_gpu_standard_01/108733-revised-public-wb-unhcr-policy-brief-final_table_000/structure.sdmx.json): the concept definitions and `LOCAL:INCOME_SUMMARY(0.1.0)` DSD, encoded in SDMX-JSON.
- [`data.sdmx.json`](../../data/structured_data_trials/20261124_gpu_standard_01/108733-revised-public-wb-unhcr-policy-brief-final_table_000/data.sdmx.json): all 16 observations, with a link to that DSD, encoded in SDMX-JSON.

For example, the last file encodes Agriculture/Mean as `"0:0": [5930.0]`.
Its dimension value lists say category index 0 means Agriculture and statistic
index 0 means Mean. These are compact indexes in this message, not permanent
category codes. The underlying observation is the first long-format row above.

The official **SDMX JSON Schema** checks the shape of an exchange message; our
**DSD** describes the statistical fields of this dataset. Passing the former
does not mean a number is correct or that we chose the right statistical model.

An existing DSD such as WDI can be reused when its dimensions and meanings fit.
It does not automatically express the income crop's Mean/Median distinction.
The current income profile is manually reviewed; automatic DSD selection,
inference and user confirmation are not implemented. Unknown currency and
ambiguous observation time remain unresolved rather than being invented.

## How Docling fits into this workflow

Docling is a document-conversion framework with supported models and engines,
configurable pipelines, and a common output representation (`DoclingDocument`).
It selects a format backend and pipeline through `DocumentConverter`; supported
components can be replaced without redesigning our downstream statistical model.
See the [architecture](https://docling-project.github.io/docling/concepts/architecture/)
and [model catalog](https://docling-project.github.io/docling/usage/model_catalog/).

Our standard pipeline combines Heron for layout detection, RapidOCR for reading
image text, and TableFormer for table structure. Heron identifies regions such as
tables and pictures; it does not itself recover the numerical series in a chart.
Our alternative VLM pipeline uses Granite-Docling-258M with a chart-to-table
prompt, then parses its generated output into the same document representation.
It is already a local generative-model experiment; the planned LLM work concerns
alternative models and statistical/SDMX interpretation, including remote APIs.

Docling also supports optional chart-extraction enrichment using separate models.
The initial trials did not enable that stage. The poor results from the small
Granite conversion model therefore do not establish the capability of every
Docling chart-extraction configuration. See [vision models](https://docling-project.github.io/docling/usage/vision_models/).

A shared output class does not guarantee equivalent detail or numerical accuracy
across models. Our interpretation and SDMX conversion remain application code
after Docling, rather than built-in Docling functionality.

## Standards review: candidate structures

Review existing structures before choosing what to adopt or extend. SDMX's
[DSD design guidelines](https://sdmx.org/wp-content/uploads/SDMx_Guidelines_for_DSDs_1.0.pdf)
recommend reuse of DSDs and code lists as the first guiding principle.

| Candidate | Relevance | Evidence and limitations |
|---|---|---|
| World Bank `WB:WDI(1.0)` | Compact economic/development-indicator model | Live definition retrieved: `FREQ`, `SERIES`, `REF_AREA`, `TIME_PERIOD`, `OBS_VALUE`, mandatory `UNIT_MULT`. Additional categories/statistics need mapping decisions. [DSD](https://api.worldbank.org/v2/sdmx/rest/datastructure/wb), [documentation](https://datahelpdesk.worldbank.org/knowledgebase/articles/1886701-sdmx-api-queries). |
| UNICEF `UNICEF:DSD_AGGREGATE(1.0)` | Cross-sector social indicators, uncertainty and provenance | Live definition retrieved: area, indicator, sex, time; units, bounds, sample size, footnotes and source attributes. [DSD](https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/datastructure/UNICEF/DSD_AGGREGATE/latest/?format=sdmx-json&references=none). |
| UNHCR Refugee Data Portal model | Displacement, protection, population groups and socioeconomic outcomes | Explicitly SDMX-aligned; location, population type, origin, nationality, age, sex and source concepts. A downloadable formal DSD has not been verified. [Model](https://refugeedata.unhcr.org/en/documentation/data-structure/data-model/). |
| OECD `OECD.DCD.FSD:DSD_CRS(1.7)` | Aid flows and development/humanitarian financing | Live definition retrieved: donor, recipient, sector, channel, modality, flow type, units, time and project attributes. [Explorer](https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.DCD.FSD&df%5Bds%5D=DcdDisseminateFinalDMZ&df%5Bid%5D=DSD_CRS%40DF_CRS&lc=en). |
| IMF `IMF:ECOFIN_DSD(1.0)` | Broad economic/financial dissemination through one relatively compact DSD | Live definition retrieved on 2026-11-25 using the correct structure ID, resolving the earlier 404: domain, area, indicator, counterpart area, frequency and time; substantial meaning is encoded in indicator codes. [DSD](https://sdmxcentral.imf.org/ws/public/sdmxapi/rest/datastructure/IMF/ECOFIN_DSD/1.0/?references=none), [IMF description](https://www.imf.org/-/media/files/news/seminars/2021/sdmx/siii-presentation-02-modeling-approaches-ecofin-dsd.pdf). |
| Global SDG DSD | Development indicators and disaggregation | Broad reference with explicit customization guidance; SDG codes should not be assigned to unrelated data. [DSD and guides](https://unstats.un.org/sdgs/iaeg-sdgs/sdmx-working-group/). |
| Global labour, education, national accounts, government finance and CPI DSDs | Domain-specific concepts and classifications | Reference candidates when an example needs those concepts. [Labour](https://sdmx.org/sdmx-for-labour/), [education](https://sdmx.org/sdmx-for-education/), [accounts/prices](https://sdmx.org/sdmx-data-structure-definitions-for-national-accounts-sdmx-na/). |
| SDMX cross-domain concepts and code lists | Common definitions for area, time, units, multipliers and status | Reusable building blocks, not a complete DSD. [Guidelines](https://sdmx.org/guidelines/). |

The initial comparison prioritized WDI and UNICEF for compact structure, UNHCR
for humanitarian meaning, and CRS for aid flows. The expanded review below adds
concrete domain structures and examines fit against actual artifacts. No
candidate has been adopted wholesale. Changed definitions need our own
identity/version; they must not be presented as unmodified global DSDs.

### Expanded DSD review and artifact inspection — 2026-11-25

Purpose: broaden the standards review before selecting a provisional DSD for the
image-first LLM MVP. This is a qualitative comparison, not a coverage-validation
study or a claim that any one existing DSD represents all Data Snapshots.

Evidence retained locally in `data/dsd_review/20261125/` (gitignored): downloaded
SDMX-ML definitions, registry inventories, source URLs, HTTP status codes and
parsed dimension/attribute inventories in `first_fetch.json`, `second_fetch.json`,
`third_fetch.json`, and `ilo_fetch.json`. Each DSD identified as retrieved below
returned HTTP 200 and was parsed as a full structure, rather than relying on an
institution's name or a registry listing. These downloads use SDMX 2.1 structure
syntax; adapting their concepts to our SDMX 3.1 / SDMX-JSON 2.1 prototype requires
an explicit representation and validation step.

#### What the papers and images establish

Reviewed the attached papers' task definitions, scope, methodology and relevant
examples. Paper 1, section 1.1 and Appendix A, explicitly includes financing
matrices, operational maps, dashboards, econometric tables and network diagrams.
A Data Snapshot is broader than a country/indicator/year table. Titles, legends,
panel associations and footnotes can be necessary evidence for an observation.

Paper 2, section 5.4 and Appendix G, separates metadata about the artifact from
the analytical content within it. Its schema describes identity, context,
structure and meaning; its validation does not establish coverage for extraction
of all numerical observations. We can use the papers and existing metadata to
choose examples without adding a runtime dependency on `metadata_extraction` or
`metadata_schema`.

The existing metadata-gold directory contains 102 records, 34 from each corpus.
An inventory of their visualization labels is saved in `artifact_inventory.json`.
Labels overlap: they include 51 tables, 23 bar charts, 14 line charts, 12
composites and 8 maps, plus other forms. These are metadata labels, not a new
visual adjudication or numerical ground truth.

Visually inspected 13 additional PNGs selected for variety, beyond the five
pipeline examples. Exact paths are retained in `visual_review_images.json`.
Paths in this table are relative to
`/home/ajd/hf_datasets/data-snapshot/snapshots`.

| PNG | Visible content and implications for statistical representation |
|---|---|
| `refugee/001_BOSIB-3f2311b3-9a20-44d3-b637-b3b2b3d21695_table_008.png` | Results framework with baseline and closing-period columns, dates, beneficiary counts and percentages for refugee/female subgroups. Preserve reporting role, indicator hierarchy and differing units. Whether closing-period values are targets requires interpretation; do not silently treat them as achieved outcomes. |
| `refugee/006_BOSIB-2c22668f-f4ba-42f5-a0d1-7949b7b8fe34_table_000.png` | Two project components with explicit US-dollar costs. Project component is the distinguishing category; no observation period appears in the crop. |
| `refugee/006_BOSIB-2c22668f-f4ba-42f5-a0d1-7949b7b8fe34_table_004.png` | Activity details and estimated direct beneficiaries. Text also includes road length, school count and pupils per school; these have different units and roles. Superscript footnote numbers must not become digits in a value. Do not assume beneficiary rows can be added without overlap. |
| `refugee/202_multi0page_table_004.png` | Project cost by component and procurement method, in US$ millions. The footnote defines parenthesized figures as Bank-loan/IDA-credit financing, not negative costs or standard errors. Totals and financing subsets must remain distinguishable. |
| `refugee/161_28046_table_013.png` | Consulting-assignment records mix descriptions, estimated costs, selection methods, review categories and submission dates. This is partly a record table; dates here are deadlines, not necessarily observation periods. Currency/scale is not given in this crop. |
| `refugee/202_multi0page_table_007.png` | Project budget and schedule: planned/actual columns, US$ thousands, duration in months and milestone dates. Blank actual cells are not zero. Distinguish date-valued content from the reference time of a numerical observation. |
| `refugee/196_multi-page_figure_002.png` | Cambodia project map uses repeated symbols by province and project type, with inset panels. Recovering counts would require reliable symbol interpretation/counting, not merely OCR. No counts were transcribed in this review. |
| `refugee/197_multi-page_figure_002.png` | Rwanda map shows roads, boundaries, parks and forests without an ordinary numerical indicator series. It remains a valid snapshot under Paper 1; do not manufacture numerical observations to fit a DSD. |
| `unhcr/68487_figure_002.png` | Composite with a registered-refugee total, demographic shares, residence shares and province counts displayed both as bars and map labels. Preserve component relationships and units; repeated map/bar displays are evidence for the same counts, not independent observations. Age thresholds are not supplied beside the age-group labels. |
| `unhcr/acnur_anlisis-madre_de_dios_vf_figure_012.png` | Spanish infographic gives travel-group count, person count and mean group size. Preserve the printed rounded mean; do not replace it with a recomputed ratio. No date appears in this crop. |
| `prwp/document_15348558_figure_008.png` | Scatterplot relates log GDP per capita to a banking-income ratio, with group symbols and a fitted curve. Individual point identities are not printed, legend wording is ambiguous, and the note refers to another figure. Distinguish estimated point coordinates from the fitted curve and do not invent countries or corrected legend meanings. |
| `prwp/document_12916918_figure_008.png` | Two panels show monthly petroleum price and percentage returns with detected breaks. Preserve panel, measure, transformation and event distinctions. Dense unlabelled curves do not supply exact numerical ground truth. |
| `prwp/document_11174028_figure_002.png` | Local polynomial smooth over a continuous residual axis, with a labelled 95% confidence band and estimation settings. The x-axis is not time. Representing it requires support for the x coordinate, fitted value and bounds; geometry-based values would be estimates. |

#### Additional structures verified

Versions below are the definitions returned on the review date, not a promise
that `latest` will remain unchanged. Candidate fit is our interpretation of their
components and the images, not a claim by the publishing institution.

| Candidate and primary definition | Components useful to us | Fit and limits |
|---|---|---|
| OECD Income Distribution, `OECD.WISE.INE:DSD_WISE_IDD(1.0)` — [DSD](https://sdmx.oecd.org/public/rest/datastructure/OECD.WISE.INE/DSD_WISE_IDD/latest/?references=none) | Measure, **statistical operation**, units, age, methodology, definition, poverty line, area and time; currency and price-base attributes. | Strong reference for the income table and poverty/distribution statistics. Its country/time and income-specific structure does not directly cover procurement or regression output. |
| ILO `ILO:IMF_ILOSTAT(1.0)` — [DSD](https://sdmx.ilo.org/rest/datastructure/ILO/IMF_ILOSTAT/1.0?references=none), [API guide](https://webapps.ilo.org/ilostat-files/Documents/SDMX_User_Guide.pdf) | Measure, sex, age and further labour classifications; units, source notes, observation status and upper/lower bounds. | Concrete labour reference for Shona-like examples. Population-group distinctions and mixed-length reporting periods still need explicit treatment. Do not assign standard labour codes without confirming the source definitions. |
| UNICEF Migration, `UNICEF:MIGRATION(1.0)` — [DSD](https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/datastructure/UNICEF/MIGRATION/1.0/?references=none) | Area, indicator, age, statistical population and time; units, source link, time-coverage/method and footnotes. | Useful for displacement/population statistics. Its dimensions do not include all demographic and residence distinctions visible in the composite. |
| UNICEF Migration Flows, `UNICEF:MG_FLOW(1.0)` — [DSD](https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/datastructure/UNICEF/MG_FLOW/1.0/?references=none) | Separate origin and destination areas, indicator, sex, age and time; units and source. | Useful when movement is genuinely an origin-to-destination flow. An intention-to-travel infographic is not automatically a measured migration flow. |
| UNICEF Social Protection, `UNICEF:SOC_PROTECTION(1.0)` — [DSD](https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/datastructure/UNICEF/SOC_PROTECTION/1.0/?references=none) | Area, indicator, sex, residence, wealth quintile, poverty threshold and time; units, source, time method and footnotes. | Useful social/welfare breakdowns, but project activity and baseline/target distinctions are not explicit dimensions. |
| UNICEF Child Poverty, `UNICEF:DSD_CHLD_POV(1.0)` — [DSD](https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/datastructure/UNICEF/DSD_CHLD_POV/1.0/?references=none) | Area, indicator, sex, residence and time; units, source, status and footnotes. | Compact thematic alternative. Its child-poverty scope is narrower than the corpus. |
| UNICEF Conflict, `UNICEF:PT_CONFLICT(1.0)` — [DSD](https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/datastructure/UNICEF/PT_CONFLICT/1.0/?references=none) | Area, parent area, administrative level, indicator, sex, age and time; mandatory unit attribute. | Useful reference for subnational hierarchy and population disaggregation, not a general representation of map geometry or all humanitarian content. |
| UNICEF Hazard Population, `UNICEF:HAZARD_POPULATION(1.0)` — [DSD](https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/datastructure/UNICEF/HAZARD_POPULATION/1.0/?references=none) | Parent-country identifier, area, administrative level, indicator, sex, age and time; units and region. | Useful for hazard-exposure statistics and local geography. Does not turn a context map into an indicator dataset. |
| UNESCO/UIS `UIS:UOE_NON_FINANCE(1.2)` — [DSD](https://registry.sdmx.org/ws/public/sdmxapi/rest/datastructure/UIS/UOE_NON_FINANCE/1.2/?references=none), [official guidance](https://sdmx.org/sdmx-for-education/) | Education level/type/field, grade, intensity, origin, mobility, statistical unit, sex, age and other dimensions. | Useful education terminology for schooling artifacts. Detailed UOE reporting structure is too specialized as the default for every snapshot. |
| OECD Short-Term Economic Statistics, `OECD.SDD.STES:DSD_STES(4.4)` — [DSD](https://sdmx.oecd.org/public/rest/datastructure/OECD.SDD.STES/DSD_STES/latest/?references=none) | Measure, units, activity, adjustment, transformation, time horizon, methodology, area, frequency and time. | Useful macroeconomic time-series reference. The transformation distinction is relevant to price versus return panels; direct code equivalence is not established. |
| IMF Government Finance Statistics, `IMF:GFS(1.0)` — [DSD](https://registry.sdmx.org/ws/public/sdmxapi/rest/datastructure/IMF/GFS/1.0/?references=none) | Sectors, counterpart area/sector, expenditure, units, currency, valuation, time and further classifications. | Useful fiscal concepts. A project's procurement-cost matrix is not automatically a government-accounts dataset. |

The OECD income DSD references
[`OECD:CL_STATISTICAL_OPERATION(1.0)`](https://sdmx.oecd.org/public/rest/codelist/OECD/CL_STATISTICAL_OPERATION/1.0/?references=none).
Downloaded codes explicitly include arithmetic/geometric/weighted mean, median,
count, standard deviation, standard error, lower/upper confidence bounds,
minimum/maximum and quantiles. This is a particularly useful reusable building
block for our Mean/Median table and research outputs. It does not itself define
regression-model, dependent-variable or regressor dimensions. A source label
"Mean" is not sufficient evidence for selecting weighted versus arithmetic mean.

The Global SDG DSD was also retrieved as `IAEG-SDGs:SDG(1.26)`, matching the
[official release page](https://unstats.un.org/sdgs/iaeg-sdgs/sdmx-working-group/)
(30 September 2026 release). It offers broad disaggregation, custom/composite
breakdowns, bounds, time coverage and source detail. Its published customization
guidance makes it a serious adaptation reference. Do not assign SDG indicator
codes to unrelated observations or assume its reporting-type codes mean our
project baseline/target distinction.

The IMF ECOFIN definition has now been retrieved successfully (see corrected
entry above). It is a compact broad economic scaffold, but an indicator code
carries much of the meaning; arbitrary categories and model-output distinctions
still require deliberate design. WDI remains a verified World Bank candidate.
No additional formal World Bank DSD was established for PIP or ASPIRE in this
review. UNHCR's published model is SDMX-aligned; a formal downloadable DSD remains
unverified. Lack of verification is not evidence that no such structure exists.

Retrieval limits: the Global Labour ZIP and the individual ILO employment DSD
request returned HTTP 403. The separate `ILO:IMF_ILOSTAT(1.0)` definition above
was retrieved successfully. A UNICEF.EMOPS structure request returned 404;
the humanitarian candidates listed above were retrieved under agency `UNICEF`.

#### Implications for the provisional DSD

1. **Keep structure separate from presentation.** A table and chart can encode
   the same observations. The strongest reason for a second DSD would be a
   different statistical family, such as model estimates versus indicator
   observations, rather than PNG figure versus PNG table.
2. **Compare a small set of base structures.** WDI, UNICEF aggregate, IMF ECOFIN
   and the Global SDG DSD are the broad scaffold candidates. OECD income/labour
   and the humanitarian structures provide domain concepts and code lists to
   reuse where the artifact supports their meanings. No base is selected yet.
3. **Allow multiple datasets from a composite.** Preserve the snapshot/component
   relationship in provenance. Do not force unrelated measures and units into a
   single series or duplicate values repeated in map and chart panels.
4. **Preserve analytical roles.** Mean/median, baseline/closing-period, planned/
   actual, overall/financed cost, fitted/raw series and coefficient/standard-error
   distinctions cannot be inferred from the numeric value alone. Some belong in
   keys when they distinguish observations; explanatory details can be attributes.
5. **Define the MVP boundary explicitly.** Numeric tables/charts and printed
   map/infographic statistics are plausible first targets. Context-only maps,
   network geometry and mixed record tables need an explicit unsupported/partial
   result until their representation is designed; they remain valid snapshots.
6. **Do not invent missing context to satisfy a borrowed structure.** Several
   crops omit dates or units, and some axes are continuous variables rather than
   time. SDMX does not universally require a time dimension; see the
   [SDMX glossary](https://sdmx.org/wp-content/uploads/SDMX_Glossary_Version_2_1_December_2020.htm).
   The Metadata Editor's
   [required Indicator ID / Time Period / Observation Value fields](https://worldbank.github.io/metadata-editor-docs/managing_data_structures.html)
   are application requirements, not proof that every SDMX DSD must have them.

Next concrete comparison: hand-represent a few already inspected artifacts under
the leading scaffold candidates, recording preserved distinctions, required
extensions and unsupported content. Include the existing income and regression
examples, one humanitarian composite, and one project results/financing table.
This is a small design exercise for the provisional MVP, not a substitute for
later independent coverage validation or an implemented LLM trial.

## Agreed five examples

Paths below are relative to `/home/ajd/hf_datasets/data-snapshot/snapshots`.
The machine-readable selection is in
[`examples.json`](../../src/data_snapshot/structured_data_extraction/examples.json).

| Example | PNG | Purpose |
|---|---|---|
| Income table | `unhcr/108733-revised-public-wb-unhcr-policy-brief-final_table_000.png` | Eight categories, Mean/Median; 16 printed values. |
| AI4Data guarantee chart | `prwp/document_10000660_figure_002.png` | Four printed values: HIGH/MUTUAL 15, HIGH/PUBLIC 7, LOW_MIDDLE/MUTUAL 7, LOW_MIDDLE/PUBLIC 17. |
| Refugee pie chart | `unhcr/68488_figure_006.png` | Sud-Kivu 9%, Nord-Kivu 91%; keep the separate total 35,416 and year 2018 distinct from shares. |
| Shona labour-force chart | `unhcr/policy_brief_on_shona_community_from_stateless_to_citizens_figure_000.png` | Two populations, two labour statuses, five mixed-length reporting periods, unlabelled numerical points and error bars of unspecified meaning. |
| Regression table | `prwp/document_11174028_table_007.png` | Nested headings, coefficients, standard errors, significance and grouped rows. |

## Implementation so far

The independent module is
[`structured_data_extraction`](../../src/data_snapshot/structured_data_extraction/README.md).
It has a PNG CLI, three local Docling pipelines (including dedicated chart
enrichment verified on one example), a reviewed income mapping profile,
long observations with native cell references, and matching structure/data SDMX
messages. Official schemas are vendored for offline validation. Native evidence
and errors are retained in fresh run folders; existing runs are not overwritten.

The initial `INCOME_SUMMARY` DSD is **local and experimental**, version `0.1.0`.
It has uncoded `CATEGORY` and `STATISTIC` dimensions and numeric `OBS_VALUE`. Its
purpose is to establish the end-to-end path, not to claim a generalized Data
Snapshots DSD or interoperability with WDI/UNICEF. No unsupported currency or
observation period is assigned to the income crop.

The first mapper accepts one rectangular numerical table with a single header
row and first-column row labels. It rejects ambiguous headers, merged cells,
missing cells, duplicate keys, significance notation and unit-bearing numbers.
Explicit blank cells/missing markers become null; zero remains zero. Chart
tables may appear in `pictures[].meta.tabular_chart.chart_data`, which is not
yet mapped automatically into SDMX observations.

## Environment and model setup

- WSL2; Intel i7-10750H; approximately 11 GiB RAM visible to WSL.
- NVIDIA GTX 1650 Ti, 4 GiB VRAM, compute capability 7.5.
- CUDA works; native BF16 does not. PyTorch's emulation-inclusive BF16 check
  returns true, which should not be confused with native hardware support.
- PyTorch `2.10.0+cu128`, Docling `2.140.0`, RapidOCR `3.10.0`, ONNX Runtime
  `1.23.2`; prefetched assets in `/home/ajd/.cache/docling/models`.
- Standard pipeline: Heron layout + TableFormer + English full-image RapidOCR.
  GPU mode accelerates layout/table models; ONNX OCR remains on CPU.
- VLM: **Granite-Docling-258M**, CPU/GPU FP32, no quantization or compilation,
  instruction `Convert chart to table.`. This is not Granite Vision 4B.
- Prefetched Granite revision: `982fe3b40f2fa73c365bdb1bcacf6c81b7184bfe`;
  Heron revision from fetch: `8f39ad3c0b4c58e9c2d2c84a38465abf757272d8`.
- Initial chart runs used 8192 output tokens. Future runs are capped at 2048;
  Docling treats length-limited output as incomplete and the prototype rejects it.
- The OpenCV distribution was present but its `cv2` import was missing after
  environment synchronization. Reinstalling `opencv-python-headless==4.13.0.92`
  repaired it. RapidOCR assets then downloaded successfully.
- Before rebuilding, some console launchers referenced the old
  `data-snapshot-annotation` checkout. Tools were invoked as Python modules
  through `uv run --no-sync python -m ...` to use the current environment.
- The user rebuilt `.venv` with `uv sync --locked --python 3.10 --extra
  structured_data --extra test` and reported that imports, CUDA and focused
  tests pass. The rebuilt Black launcher points to this checkout.
- Unlimited-OCR is deferred: its cached BF16 weights occupy 6.21 GiB before
  activations, exceeding this GPU's capacity. Offloading/quantization is untested.

## Trial log — 2026-11-24

Times include pipeline/model initialization. These are individual smoke tests,
not controlled throughput benchmarks. Peak CUDA figures below are PyTorch
allocated memory, not total GPU memory including context and other allocations.

| Example / pipeline | Device | Time | Findings |
|---|---|---:|---|
| Income / standard | CPU | 21.72 s | 16/16 manually transcribed values and their category/statistic associations agree. Long observations and both SDMX messages written and schema-validated. |
| Income / standard | CUDA FP32 | 15.96 s | Same 16 observations as CPU. Peak PyTorch allocated: 575.2 MiB. |
| Guarantee / Granite | CPU FP32 | 28.92 s | Incorrect result: labels flattened into a 2×4 chart table and last value `5` instead of `17`. Not exported to SDMX. |
| Guarantee / Granite | CUDA FP32 | 14.25 s | Identical incorrect cell contents to CPU. Peak PyTorch allocated: 1594.5 MiB. GPU helps runtime, not accuracy in this case. |
| Refugee pie / Granite | CPU FP32 | 34.09 s | Incorrect 2×4 output: mixes total, year and labels; values include `90.99%`, `0.0%`, `9.01%`, `9.99%`. Not exported. |
| Regression / standard | CPU | 29.92 s | Detected 22×5 table; nested headings and significance marks preserved in native cells. Numerical accuracy not fully scored; mapping deferred. |
| Shona / Granite | CPU FP32 | ~431 s before interruption | No complete native result. The initial 8192-token run was stopped after prolonged decoding. This does not establish that CPU execution is impossible. |
| Shona / Granite | CUDA FP32 | 90.97 s | Conversion completed, but its chart data is 0×0: no usable observations. No SDMX output produced. |
| Guarantee / standard | CPU | 15.77 s | One picture and no tables/chart metadata. OCR reads chart text, including the four data labels and axis ticks, without assigning them to series/category observations. |
| Refugee pie / standard | CPU | 4.42 s | One picture and no tables/chart metadata. OCR reads `91%`, but reads the other percentage as `%6`; no usable numerical series. |
| Shona / standard | CPU | 4.77 s | One picture and no tables/chart metadata. OCR recovers labels/ticks but does not estimate plotted values. |
| Guarantee / dedicated Chart2CSV (2026-11-25) | CPU BF16, image scale 0.5 | ~7 min (CLI: 437.51 s) | Correct 3×3 chart table: all four printed values and their category/series associations match. Peak process RSS 7.90 GiB. Single-example result; no SDMX mapping. |
| Refugee pie / dedicated Chart2CSV (2026-11-25) | CPU BF16, image scale 0.5 | ~6 min (CLI: 348.73 s) | Correct province/percentage pairs: Nord-Kivu 91%, Sud-Kivu 9%. Total/year stay in separate OCR text. Peak process RSS 7.85 GiB. |
| Guarantee / dedicated Chart2CSV with CPU offloading (2026-11-25) | CUDA FP16, image scale 0.5 | 263.16 s | Same four correct observations as CPU. Observed CLI speedup 1.66×; peak PyTorch allocated 1.59 GiB, reserved 1.69 GiB; peak process RSS 9.87 GiB. |
| Refugee pie / dedicated Chart2CSV with CPU offloading | CUDA FP16, image scale 0.5 | 258.52 s | Same two correct province/percentage pairs as CPU; 1.35× observed CLI speedup. Peak allocated CUDA 1.34 GiB; process RSS 10.42 GiB. |
| Shona / dedicated Chart2CSV with CPU offloading | CUDA FP16, image scale 0.5 | 510.14 s | Recovered four series over five periods (20 estimates), but numerical discrepancies remain and error bars are omitted. Peak allocated CUDA 2.53 GiB; process RSS 10.60 GiB. |
| Regression / standard | CUDA FP32 | 26.18 s | Same cell text/spans as prior CPU run. All 42 displayed numeric text cells match the PNG, including significance marks; statistical mapping remains pending. Peak allocated CUDA 0.56 GiB; process RSS 2.20 GiB. |

Evidence roots under `data/structured_data_trials/`:

- `20261124_standard_01`: first failed environment attempt (missing `cv2`).
- `20261124_standard_02`: verified CPU income extraction, observations and SDMX.
- `20261124_standard_03`: native regression extraction.
- `20261124_granite_01`: CPU guarantee-chart extraction.
- `20261124_granite_02`: CPU pie extraction and interrupted Shona attempt.
- `20261124_gpu_standard_01`: verified GPU income output.
- `20261124_gpu_granite_01`: GPU guarantee-chart extraction.
- `20261124_gpu_granite_02`: bounded GPU Shona rerun.
- `20261124_standard_charts_01`: standard-pipeline baseline on all three charts,
  in one process. Later images benefit from warm imports/caches; times are not
  comparable controlled benchmarks.
- `guarantee_chart_20261125_135646`: user-run dedicated CPU Chart2CSV result,
  original native JSON, run metadata, logs, GNU time resources and reviewed
  `comparison.json` with four exact observation matches.
- `refugee_pie_20261125_142540`: user-run dedicated CPU pie extraction, original
  evidence/resources and reviewed `comparison.json` with two exact percentage matches.
- `20261125_chart_offload_debug_01` and `_02`: retained GPU failure tracebacks used
  to diagnose functional attention and direct image-parameter hook problems.
- `20261125_chart_offload_debug_03`: successful corrected GPU/offload run, native
  result, exact comparison with CPU, runtime/RAM and peak PyTorch CUDA measurements.
- `remaining_gpu_20261125_150556`: user-run pie, Shona and regression GPU batch,
  each with native output, run metadata, console logs, resources and CUDA figures.
  Separate comparison/review files retain the verification and its limits.

These large/generated outputs are gitignored. The income test fixture is manually
transcribed from the source image and is independent of model predictions.

### Dedicated chart enrichment

Added `--pipeline chart`: standard conversion followed by picture classification
and `granite_vision_v3_3` Chart2CSV enrichment. Standard conversion supplies a
picture without the small VLM's existing incorrect chart data, which would cause
the enrichment stage to skip chart-to-table generation. The picture classifier
must recognize bar, pie or line chart for the stage to process it.

The dedicated model is
[`ibm-granite/granite-vision-3.3-2b-chart2csv-preview`](https://huggingface.co/ibm-granite/granite-vision-3.3-2b-chart2csv-preview),
pinned by installed Docling to revision
`6e1fbaae4604ecc85f4f371416d82154ca49ad67`. Its published
[weight files](https://huggingface.co/ibm-granite/granite-vision-3.3-2b-chart2csv-preview/tree/main)
total approximately 6.15 GB. The newer default
[Granite Vision 4.1 4B](https://huggingface.co/ibm-granite/granite-vision-4.1-4b/tree/main)
has approximately 7.99 GB of weight files. Neither is a full-GPU fit on this
4 GiB card at the published 16-bit precision, before runtime allocations.

The tested smaller-model configuration is CPU BF16, no quantization or
compilation, image scale 0.5, capped at 2048 generated tokens. This reduces weight
RAM relative to FP32. The completed guarantee-chart trial took approximately
seven minutes and peaked at 7.90 GiB process RSS; these figures are not bounds
for other images. This CPU lacks native BF16 acceleration. The user completed
the additional download. Download
command:

```bash
uv run --no-sync docling-tools models download \
  picture_classifier granite_chart_extraction_v3_3
```

Local safetensors-header inspection confirms 3,076,068,416 stored parameters,
all BF16, totaling 6,152,136,832 bytes (5.73 GiB) before runtime allocations.
The model's "2B" name does not describe its full stored parameter count.

The original configuration rejected chart CUDA runs. An experimental CPU-offload
path initially failed; after CPU accuracy was established and the user authorized
further GPU work, the corrected path matched all four bar-chart observations.
The CLI checks for prefetched model
directories. See the [usage guide](../../src/data_snapshot/structured_data_extraction/README.md#dedicated-chart-extraction)
for the first guarantee-chart command and expected four associations.

Source inspection found that chart enrichment parses generated text without
checking its finish reason; a token-limited or malformed result may coexist with
conversion success. Raw chart output therefore remains unverified. Empty,
truncated and inaccurate numerical extractions must be reviewed; no automatic
chart-to-SDMX export was added.

### Single-snapshot accuracy check — 2026-11-25

Scope: establish whether dedicated Chart2CSV improves one known incorrect
extraction before implementing further hardware optimizations or expanding the
sample. Use `prwp/document_10000660_figure_002.png`, the guarantee chart. The
initial small Granite model returned a 2×4 table:

```text
PUBLIC | MUTUAL | HIGH | LOW_MIDDLE
15     | 7      | 7    | 5
```

This flattens the two axes and misreads the printed `17`. The manually reviewed
targets, read directly from the original PNG, are:

| Guarantee type | Series | Printed value |
|---|---|---:|
| MUTUAL | HIGH | 15 |
| MUTUAL | LOW_MIDDLE | 7 |
| PUBLIC | HIGH | 7 |
| PUBLIC | LOW_MIDDLE | 17 |

The comparison must check all four category/series/value associations, not just
the presence of the numbers. Expected observations are stored separately in
`data/structured_data_trials/20261125_chart_cpu_01/expected.json`; they are never
passed to the model. Only this snapshot is being evaluated in this step.

Previous attempts are retained, without treating execution failures as numerical
accuracy measurements:

- `20261124_chart_enrichment_01`: CPU BF16 at original rendering scale; interrupted
  after approximately 11 minutes without a complete extraction. Peak process RSS
  6,346,524 KiB (6.05 GiB). No usable native chart table.
- `20261124_chart_offload_01`: experimental FP16 GPU execution with CPU offloading,
  half-size rendering; failed with `RuntimeError: Pipeline StandardPdfPipeline
  failed` after 49.99 seconds in the CLI. No native chart table. This was not a
  successful GPU feasibility or accuracy result; further work is deferred.

The CPU-only trial `20261125_chart_cpu_01` used the existing
`--pipeline chart --device cpu` configuration: BF16, image scale 0.5, 2048-token
cap, no quantization, compilation or CPU/GPU offloading. It was interrupted at
the user's request to hand execution to their terminal; no complete extraction
was produced. Logs, periodic stack traces and `/usr/bin/time -v` resource capture
are retained. A fresh terminal run will use the same single snapshot/configuration.
The original PNG remains unchanged. Any result applies to this rendering and
single example; it is not a benchmark across charts.

#### Completed terminal run and review

The user completed the run in
`data/structured_data_trials/guarantee_chart_20261125_135646`. The native chart
table at `pictures[0].meta.tabular_chart.chart_data` contains:

| Category | HIGH | LOW_MIDDLE |
|---|---:|---:|
| MUTUAL | 15 | 7 |
| PUBLIC | 7 | 17 |

**Result: 4/4 exact category/series/value matches, with no corrections applied.**
The first row is marked as column headers and MUTUAL/PUBLIC as row headers.
This corrects both the flattened axes and the misread `17` in the earlier small
Granite-Docling output. The original image SHA-256 matches the run metadata.

Verification combined a fresh visual check of the PNG and an assert-based
comparison against the independently recorded `expected.json`. It checked the
3×3 shape, nine unique unmerged cells, header labels, all four observation keys
and exact numeric values. The native file was read without alteration.

- Conversion status: `extracted_only` (native conversion completed; review is
  recorded separately rather than rewriting the inference run's status).
- Picture classification: `bar_chart`, confidence 0.99945. This confidence
  concerns the chart type, not the correctness of the extracted numbers.
- VLM generation: 27 tokens in 397.71 seconds, well below the 2048-token cap.
- CLI duration: 437.513 seconds; Docling conversion log: 433.31 seconds.
- GNU time wall duration: 419.41 seconds; its timing differs from the CLI/log.
  Retain both measurements and summarize as approximately seven minutes.
- GNU time maximum RSS: 8,288,412 KiB = 7.90 GiB; exit status 0.
- Embedded chart image: 588×346 pixels, DPI 36, consistent with image scale 0.5.

Artifacts:

- [Reviewed comparison](../../data/structured_data_trials/guarantee_chart_20261125_135646/comparison.json).
- [Native extraction](../../data/structured_data_trials/guarantee_chart_20261125_135646/document_10000660_figure_002/native.json).
- [Run metadata](../../data/structured_data_trials/guarantee_chart_20261125_135646/document_10000660_figure_002/run.json).
- [Console log](../../data/structured_data_trials/guarantee_chart_20261125_135646/console.log).
- [Resource measurements](../../data/structured_data_trials/guarantee_chart_20261125_135646/resources.txt).

Interpretation: dedicated chart enrichment demonstrates a clear improvement for
this labelled grouped bar chart. This result alone does not establish performance
on other chart types or the dataset generally. Subsequent pie/GPU checks are
recorded below; no automatic chart mapping or SDMX export was performed in this review.

#### Second CPU example: refugee pie chart

The user ran `unhcr/68488_figure_006.png` with the same CPU BF16, scale 0.5,
2048-token configuration. Review of the original PNG and native chart table found:

| Category | Percentage |
|---|---:|
| Nord-Kivu | 91% |
| Sud-Kivu | 9% |

**2/2 exact province/percentage matches, without corrections.** The source image
hash matches run metadata; the 3×2 table has six unique unmerged cells with
Category/Percentage headers. The year (`en2018`) and total (`35,416`) remain
separate OCR text blocks, rather than being mixed into the chart series. They
have not been mapped into statistical observations. Raw OCR still contains the
incorrect `%6` text block; the verified chart result comes from enrichment.

- CLI duration: 348.732 seconds; generation: 301.53 seconds for 29 tokens.
- GNU time wall duration: 326.85 seconds; as with the bar trial, retain both
  timing sources and use approximately six minutes in summaries.
- Peak process RSS: 8,229,632 KiB = 7.85 GiB; exit status 0.
- Classifier: `pie_chart`, confidence 0.999959; this is not value-level confidence.
- [Reviewed comparison](../../data/structured_data_trials/refugee_pie_20261125_142540/comparison.json).
- [Native extraction](../../data/structured_data_trials/refugee_pie_20261125_142540/68488_figure_006/native.json).
- [Run metadata](../../data/structured_data_trials/refugee_pie_20261125_142540/68488_figure_006/run.json).
- [Resources](../../data/structured_data_trials/refugee_pie_20261125_142540/resources.txt).

This is a second verified labelled-chart example, not a dataset-wide accuracy
estimate. No pie-to-SDMX mapping or additional inference was performed to review it.

### GPU acceleration assessment — 2026-11-25

After the verified 4/4 CPU result, the user reopened GPU acceleration as a
feasibility question. Direct full-model FP16 loading still exceeds 4 GiB VRAM:
the stored weights alone occupy 5.73 GiB, before activations and the KV cache.

The smallest next experiment is to diagnose the existing CPU-offload path.
Accelerate is installed and the adapter exists, but the first run recorded only
the generic `Pipeline StandardPdfPipeline failed` error. Capture the underlying
exception and traceback before estimating the fix; do not treat this as proven
GPU compatibility. Keep the same image, prompt, scale 0.5 and token cap, then
compare all four keyed values with the CPU baseline and measure runtime/VRAM/RAM.
See [Accelerate CPU offload](https://huggingface.co/docs/accelerate/package_reference/big_modeling#accelerate.cpu_offload).

If transfers or offload compatibility are prohibitive, 4-bit quantization is a
separate candidate. It requires an additional dependency and model/hardware
compatibility checks, and may change extraction results. A fit and speedup are
not guaranteed. See [Transformers bitsandbytes](https://huggingface.co/docs/transformers/quantization/bitsandbytes).

This assessment did not modify pipeline code, install dependencies or run another
inference. Difficulty remains a contained compatibility/memory investigation;
the existing generic error is insufficient to promise a one-line fix or speedup.

#### CPU offloading investigation (authorized subsequently)

The user authorized trying CPU offloading after the CPU accuracy checks. The
pipeline now records chained tracebacks in failed `run.json` files so underlying
model errors survive Docling's generic pipeline exception.

- `20261125_chart_offload_debug_01`: reproduced the error. `MultiheadAttention`
  uses its `out_proj` weights through functional attention without calling that
  child module, so ordinary offload hooks leave those weights on `meta`.
- `20261125_chart_offload_debug_02`: preloading `MultiheadAttention` fixed the
  first issue, then exposed `LlavaNextModel.image_newline` being on `meta` during
  image-feature assembly. Transformers calls the image encoder before the
  parent's normal forward hook runs.
- The revised setup keeps the small `image_newline` parameter resident on the
  execution device, offloads the vision/projector/language/output components
  separately, and preloads functional attention's child weights. Model weights
  use FP16 on this GPU; CPU OCR/layout/classification remain unchanged.
- A small real attention regression test exercises both direct parameter access
  and functional child-weight access over two calls. It runs offload hooks on CPU
  with a simulated GPU adapter boundary; it does not substitute for a live GPU test.
- `20261125_chart_offload_debug_03`: completed successfully on the same bar chart,
  with the same prompt, image scale and token cap as the verified CPU run.

No quantization or new dependency installation was introduced for these fixes.

#### Verified GPU/offload result

The resulting 3×3 chart table is identical to the reviewed CPU table: MUTUAL has
HIGH 15 and LOW_MIDDLE 7; PUBLIC has HIGH 7 and LOW_MIDDLE 17. The source image
hash, headers and all four keyed values match. No correction was applied to the
native result. The inference run remains `extracted_only`; its separate comparison
records the successful numerical review.

| Measurement | CPU BF16 | GPU FP16 with CPU offloading |
|---|---:|---:|
| Exact keyed observation matches | 4/4 | 4/4 |
| CLI duration | 437.513 s | 263.156 s |
| Model generation duration | 397.71 s | 177.80 s |
| Generated tokens | 27 | 27 |
| Peak process RSS | 7.90 GiB | 9.87 GiB |
| Peak PyTorch CUDA allocated | — | 1.59 GiB |
| Peak PyTorch CUDA reserved | — | 1.69 GiB |

Observed speedup: 1.66× for the full CLI run and 2.24× for generation. These are
individual smoke tests, not a controlled throughput benchmark. The GPU run
includes explicit model initialization and CPU BF16-to-FP16 loading; offline
tests overlapped part of initialization, so its startup is not a clean isolated
measurement. GNU time reported 254.86 seconds versus CLI 263.156 seconds; both
are retained. PyTorch figures exclude some CUDA context/driver memory. A sampled
`nvidia-smi` reading during generation was 597 MiB total GPU memory and 24%
utilization, not a peak measurement.

The tradeoff is increased RAM use: process maximum RSS was 10,348,192 KiB
(9.87 GiB). This is substantial for this WSL instance and is not a RAM bound for
other images. Large cropped figures, more tokens or other concurrent workloads
may behave differently. The adapter's component graph is specific to the pinned
Granite Vision LlavaNext implementation and should be rechecked after upgrades.
Subsequent GPU/offload pie and Shona checks are recorded below.

- [Reviewed comparison](../../data/structured_data_trials/20261125_chart_offload_debug_03/comparison.json).
- [Native extraction](../../data/structured_data_trials/20261125_chart_offload_debug_03/document_10000660_figure_002/native.json).
- [Run metadata](../../data/structured_data_trials/20261125_chart_offload_debug_03/document_10000660_figure_002/run.json).
- [Peak CUDA measurements](../../data/structured_data_trials/20261125_chart_offload_debug_03/cuda_memory.json).
- [Runtime/RAM measurements](../../data/structured_data_trials/20261125_chart_offload_debug_03/resources.txt).

### Remaining GPU batch review — 2026-11-25

All three user-run jobs completed conversion and exited successfully. Their
inference status remains `extracted_only`; the following review separately
assesses numerical content. Source PNG hashes match all three run reports.
No new inference, extraction corrections or pipeline changes were performed
for this review.

| Sample | CLI duration | Peak CUDA allocated / reserved | Peak process RSS | Review |
|---|---:|---:|---:|---|
| Refugee pie | 258.521 s | 1.34 / 1.43 GiB | 10.42 GiB | 2/2 exact province/percentage matches; same chart table as reviewed CPU output. |
| Shona | 510.138 s | 2.53 / 2.63 GiB | 10.60 GiB | Structure recovered; numerical estimates need review. |
| Regression | 26.178 s | 0.56 / 0.68 GiB | 2.20 GiB | 42/42 printed numeric text cells match; interpretation/mapping pending. |

GPU measurements are PyTorch figures, excluding some driver/context memory.
GNU time wall durations were 251.87, 488.22 and 32.58 seconds respectively;
retain these alongside the CLI values rather than silently treating them as
identical clocks. Chart runs remain RAM-intensive for this approximately 11 GiB
WSL instance; these successful cases do not establish resource bounds.

#### Pie: verified on GPU too

The 3×2 table is identical to the reviewed CPU result: Nord-Kivu `91%`, Sud-Kivu
`9%`. Both the labels and percentage strings match. Total `35,416` and `en2018`
remain separate text; raw OCR still misreads another block as `%6`, whereas
the chart enrichment has the correct `9%`. Generation produced 29 tokens in
159.71 seconds, below the token cap. Observed speedup is 1.35× for the CLI and
1.89× for generation versus the earlier individual CPU run, not a controlled
throughput benchmark.

[Pie comparison](../../data/structured_data_trials/remaining_gpu_20261125_150556/refugee_pie/comparison.json)
records the source hash, exact CPU-table agreement, values and resource figures.

#### Shona: useful structure, unreliable numerical estimates

The dedicated model produced a 6×5 chart table, a substantial improvement over
the earlier small VLM's empty chart data. It preserves both populations, both
employment statuses and all five irregular time intervals, with 20 estimated
percentages:

| Date | Urban Nationals employed | Urban Nationals unemployed | Shona employed | Shona unemployed |
|---|---:|---:|---:|---:|
| May-Jun '20 | 40% | 15% | 20% | 20% |
| Jul-Sep '20 | 45% | 20% | 15% | 55% |
| Oct-Nov '20 | 50% | 25% | 20% | 30% |
| Jan-Mar '21 | 55% | 15% | 25% | 20% |
| Apr-Jun '21 | 70% | 10% | 50% | 15% |

These are **raw model estimates**, not verified exact source values. Visual
review identifies a clear error: Shona employment in Oct-Nov 2020 is plotted
around 30%, but the extraction says 20%. Shona unemployment in Jan-Mar 2021 is
around 25-26%, but the extraction says 20%. Other points are coarsely rounded;
every output is a multiple of five percentage points. Error bars are missing,
and their statistical meaning/confidence level is unspecified in the crop.

Because the chart prints no data labels, this is a qualitative comparison with
geometry, not a ground-truth numeric score. No exact-match count is assigned.
Generation produced 138 tokens in 410.91 seconds, below the cap. This is a
completed but partially incorrect extraction, not an empty/truncated result.

[Shona review](../../data/structured_data_trials/remaining_gpu_20261125_150556/shona/review.json)
retains the raw table, concrete discrepancies and limits of the visual check.

#### Regression: numerical transcription verified, mapping still needed

The standard GPU pipeline recovered the same 22×5 table cell texts and spans as
the prior CPU run. A fresh manual transcription from the original image checked
all **42 displayed numeric text cells** at their row/column positions, including
signs, decimal precision, commas and significance marks; all matched. Source
blanks were checked separately. This count includes coefficients, standard
errors, sample counts, fit statistics and estimated effects; it is not a count
of homogeneous SDMX observations.

Nested group labels (One lag/Two lags, prior year/two years ago, Early/Late
onset) still require explicit interpretation. Native `One lag` spans one column,
while `Two lags` spans two; mapping must associate both Coef and SE with each
model explicitly. Stars are preserved in the cells where the image prints them;
their meaning depends on the external table notes and must not be invented or
silently reassigned. No generic table-to-SDMX mapping has been applied.

[Regression comparison](../../data/structured_data_trials/remaining_gpu_20261125_150556/regression/comparison.json)
contains all 42 manually reviewed cell strings and positions, CPU equivalence
and the remaining interpretation issues.

#### Initial five-sample set: current conclusion

| Sample | Extraction evidence | SDMX status |
|---|---|---|
| Income | 16/16 reviewed values/associations; CPU and GPU agree | Complete first example using experimental local income DSD |
| Guarantee | 4/4 reviewed values/associations; dedicated CPU and GPU agree | Native chart data; statistical mapping pending |
| Refugee pie | 2/2 reviewed province percentages; dedicated CPU and GPU agree | Native chart data; separate total/year not mapped |
| Shona | Four series/five periods recovered; estimated values contain errors; error bars absent | Needs numerical review and statistical mapping |
| Regression | 42/42 printed numeric text cells match; CPU/GPU table cells agree | Needs nested statistical interpretation/mapping |

The extraction screen of the initial five images is complete. It shows strong
results for the reviewed printed values, plus a concrete remaining failure on
unlabelled chart geometry. Do not aggregate the cell counts into a dataset-wide
accuracy score or describe all five as completed SDMX datasets.

## Checks and interpretation

- 19 focused offline tests pass: observation associations, official-schema
  validation, indexed-data decoding, missing versus zero, ambiguous numbers,
  malformed structures, pipeline/device forwarding, immutable runs, interruption,
  chart CPU/BF16 configuration, unavailable-CUDA rejection, preserved failure
  tracebacks and repeated component-offload calls with direct parameter and
  functional attention child-weight access.
- The focused suite plus existing metadata-schema tests pass (111 tests).
- Live assertions verified the bar chart on CPU and GPU/offload (4/4 each), and
  the pie on CPU and GPU/offload (2/2 each), plus regression's 42 printed numeric
  text cells and its CPU/GPU cell equivalence. Shona's structural checks and
  numerical limitations are recorded separately. Native files were not altered.
- `uv lock --check --offline` passes. The new `structured_data` extra reuses the
  pinned Docling stack and declares its TF-ID dependency conflict explicitly.
- A wheel build includes both official schemas, the income mapping profile and
  the five-example manifest.

Schema validity establishes representation, not numerical truth. Likewise,
Docling conversion success means a document was produced, not that chart values
or statistical meanings are correct. Native-only runs use `extracted_only`;
they are never labelled verified numerical datasets.

## Next actions and open questions

The user completed the remaining checks in the initial five-image set from WSL:
refugee pie and Shona with `--pipeline chart --device cuda:0`, then regression
with `--pipeline standard --device cuda:0`. Outputs and review are recorded above.
The example manifest now selects `chart` for the three chart images; `granite`
remains available for reproducing the earlier small-model baseline.

1. Incorporate Aivin's clarification when received; DSD candidate review can
   proceed using the actual five examples in the meantime.
2. Select/adapt a provisional MVP DSD from the reviewed WDI, UNICEF, global SDG
   and UNHCR-aligned concepts. Record scope and extensions; no shared DSD has
   been adopted. A downloadable formal UNHCR DSD has not been verified.
3. Build an image-first LLM prototype, preserving independence from the metadata
   extraction module, with Python validation and SDMX serialization.
4. Evaluate the LLM on the reviewed examples, including Shona's known numerical
   failures and regression's nested statistical roles. Treat Docling preprocessing
   as a paired comparison, rather than a presumed requirement. No quantization,
   RapidAI integration or review UI is planned for this step.

Unresolved: the eventual shared DSD; standard-code mapping; units absent from
crops; time intervals that are not regular frequencies; confidence/error-bar
interpretation; regression-table semantics; and correction review policy.
