# PNG structured data extraction prototype

Independent of `metadata_extraction` and `metadata_schema`. Input is a PNG;
native extraction is Docling JSON. A reviewed table mapping can additionally
produce long observations, a local DSD, and SDMX-JSON 2.1.0 data. A separate
OpenRouter entry point prepares image-first LLM extraction offline by default.

**Current direction (2026-11-26):** tooling plus an interactive workflow for one
snapshot at a time: PNG/Docling evidence -> LLM working-model proposal -> user
acceptance -> extraction -> data review -> formal SDMX structure/code mapping and
export. A separate Streamlit app is planned. The working-model proposal and local
draft/acceptance backend is implemented below; the UI and extraction against the
new accepted model remain to be added. The fixed-DSD CLI remains an experimental
baseline.
SDMX concepts and codelists can guide appropriate mappings without forcing absent
information into the snapshot. Final encoding can follow reviewed extraction;
interpreting the statistical meaning and validating provisional records still
happen earlier. CSV, RapidAI and PDF-workflow integration remain deferred.

The central [plan and experiment notebook](../../../docs/data_extraction/working_notebook.md)
records decisions, candidate DSDs, hardware checks and live findings.

## Snapshot model proposal and acceptance

`working_model.py` defines the editable interpretation before formal SDMX coding:
multiple components; component-local identifying fields and original category
labels; numeric or text result definitions; scoped units, time and qualifications;
relationships; and questions that can remain unresolved. A context scope selects
a component, optional result fields, and optional categories. Numeric results
need a unit context even when its value is unknown. This is not a general or
accepted SDMX DSD, and contains no extracted observation dataset.

The proposal entry point uses **PNG + matching native Docling JSON**. The native
file must have its sibling local-extractor `run.json`, whose image hash and
successful conversion status are checked. The model receives document content
with references, cells and chart metadata preserved; document-name/origin metadata
and embedded page-image assets are excluded. The PNG is the primary evidence and
Docling content is explicitly untrusted preprocessing. This module reads existing
Docling results; it does not launch Docling or download models.

Create a fresh review session from the verified income example:

```bash
review_session_dir="data/structured_data_trials/model_review_income_01"

uv run --no-sync python -m data_snapshot.structured_data_extraction.model_review init \
  /home/ajd/hf_datasets/data-snapshot/snapshots/unhcr/108733-revised-public-wb-unhcr-policy-brief-final_table_000.png \
  --docling data/structured_data_trials/20261124_standard_02/108733-revised-public-wb-unhcr-policy-brief-final_table_000/native.json \
  --session-dir "$review_session_dir"

uv run --no-sync python -m data_snapshot.structured_data_extraction.model_proposal \
  "$review_session_dir/input.png" --docling "$review_session_dir/native.json" \
  --output-dir data/structured_data_trials/income_model_prepare_01
```

That proposal command is **offline by default**: no dotenv, client or network.
It writes the request preview, projected Docling evidence, input hashes,
model-response schema, settings and revision inputs. It does not invent a model
response or accept a draft. For a billable proposal, use a **fresh output path**
and add `--execute`; the existing cumulative $5 ledger and no-retry behavior apply.
A successful call additionally saves `response.json`, `raw_output.txt`, and
`proposed_model.json`. Validation failures preserve raw output and billed cost.

After a successful executed proposal, apply it as a draft and explicitly accept
that draft (replace the proposal path with the actual successful output):

```bash
uv run --no-sync python -m data_snapshot.structured_data_extraction.model_review apply \
  --session-dir "$review_session_dir" \
  --proposal-dir data/structured_data_trials/income_model_proposal_01 \
  --expected-revision 0 --reviewer Aj

uv run --no-sync python -m data_snapshot.structured_data_extraction.model_review accept \
  --session-dir "$review_session_dir" --expected-revision 1 --reviewer Aj
```

**Direct editing:** export an editable copy, edit that copy, and save a new draft.
Do not edit the protected session history or the raw generated proposal:

```bash
uv run --no-sync python -m data_snapshot.structured_data_extraction.model_review show \
  --session-dir "$review_session_dir" --model-output "$review_session_dir/edit.json"

# Edit edit.json, for example the population qualification's applies_to scope.
uv run --no-sync python -m data_snapshot.structured_data_extraction.model_review save \
  --session-dir "$review_session_dir" --model "$review_session_dir/edit.json" \
  --expected-revision 1 --reviewer Aj --note "Scope the note to labor income only"
```

Use the draft revision printed by each command for subsequent edits/acceptance.
An unchanged model is a no-op; an actual change creates a new revision, clears
current acceptance, and retains previous revisions and acceptance records.
Source labels and optional display labels are separate. Unknown fields and
unresolved questions do not require fabricated answers before model acceptance.

**LLM revision:** export the current draft, pass it as `--current-model` with an
explicit `--instruction`, and use a fresh proposal output directory. It prepares
offline unless `--execute` is added. Inspect the result before `apply`; it never
replaces a session draft automatically. Applying checks the proposal's image,
Docling and current-model fingerprints, so a late model response cannot overwrite
newer user edits. A changed source or edited raw proposal also stops import.

`model_review` actions are local and make no API calls. Sessions snapshot the PNG,
native Docling JSON and source run report; `session.json` is written under an
exclusive file lock with atomic replacement. Acceptance records include the
model and source hashes and a reviewer label. The reviewer label is not an
authentication system. Only `accepted_revision` authorizes the **current** model;
historical acceptance records are not current approval after an edit.

Tests use hand-authored models for all eight design cases, fake billed responses
and temporary sessions. They verify shape, references, scope integrity, review
history, source matching and atomic-save failure behavior. They do not establish
LLM proposal quality, exhaustive context-rule coverage or factual correctness.
There is no Streamlit UI or accepted-working-model value extractor yet. Do not
pass this working-model JSON to the legacy fixed-DSD extractor or call it
SDMX-compliant. Those are subsequent integration steps.

## OpenRouter workflow — offline preparation first

The independent implementation follows the production repository's pattern of
JSON settings, system/user prompt files, an OpenAI-compatible Responses client,
and strict local validation. It imports neither metadata module and does not
require Docling or GPU models. Its lightweight optional extra is `structured_llm`;
the current `structured_data`/test environment already contains its dependencies.
No environment rebuild is needed for this change.

Prepare a smoke test without reading `.env`, constructing a client or making
network/API calls:

```bash
uv run --no-sync python -m data_snapshot.structured_data_extraction.llm \
  /home/ajd/hf_datasets/data-snapshot/snapshots/unhcr/108733-revised-public-wb-unhcr-policy-brief-final_table_000.png \
  --dry-run --output-dir data/structured_data_trials/llm_income_prepare_01
```

The directory must be fresh. The default is also offline when `--dry-run` is
omitted. Files are `request.preview.json` (prompts/schema/settings with image
bytes omitted), `config.json`, `dsd.json`, and `run.json` (image and request hashes,
model, DSD version, status and attempt count). The preview is for inspection,
not a directly replayable API request. Local file paths are recorded in the run
report but not supplied as model evidence.

The default settings are in `config/openrouter.json`; override with `--config`.
The agreed working reference is `openai/gpt-5.6-luna` at medium reasoning.
This is a fixed experimental baseline, not numerical or semantic ground truth.
The CLI requires `--execute` for any API attempt; it then loads
`OPENROUTER_API_KEY` from the environment/`.env`. There is one request, with SDK
automatic retries disabled, and no automatic repair, model or provider fallback.

The live path is PNG + DSD -> model-produced long observations -> Python
validation -> SDMX-JSON. It requests strict Structured Outputs and compatible
provider routing, following the
[OpenRouter documentation](https://openrouter.ai/docs/guides/features/structured-outputs).
The authorized income smoke test completed on 2026-11-25: all 16 values and their
Mean/Median associations match the image, and both exchange schemas validate.
A population-qualifier error remains on the remittance observations; see the notebook.

### Independent open discovery

For DSD development, discover representation requirements before choosing a
statistical structure. This task uses separate prompts and a recording schema;
it supplies neither the experimental DSD nor prior discovery results to the model.

```bash
uv run --no-sync python -m data_snapshot.structured_data_extraction.discovery \
  /absolute/path/to/snapshot.png \
  --output-dir data/structured_data_trials/discovery_example
```

The default prepares offline without loading an API key. Add `--execute` to allow
one OpenRouter attempt under the same cumulative $5 spending ledger, and use
`--batch-id` to group its costs. `--config` selects the model/settings file.
Existing output directories cannot be overwritten or retried in place.

The output is `discovery.json`, not SDMX: image-grounded analytical units,
provisional requirements/functions, evidence, relationships, representative
observations and ambiguities. Validation checks the recording schema, unique IDs
and resolvable references. Review against the image is still needed to establish
accuracy and completeness. Raw responses, schema/settings snapshots, request
fingerprints, usage and billed costs are preserved. Consolidation and standards
alignment happen later, after independent discovery. The working notebook records
the six-image pilot and the subsequent development/validation plan.

The discovery exercise is now **closed and saved for later use**: all 210 images
were attempted, 209 records validated, and one structural failure is preserved.
Compact exports and their summary/inventory are in
`docs/data_extraction/discovery_20261126/`; a portable local archive is at
`data/structured_data_archives/discovery_20261126.zip`. Shared-DSD consolidation
and the associated 202-image coverage study are parked. See the current plan in
the working notebook before starting further discovery calls. The following
batch command is retained for reproducibility.

For the frozen 210-image development run, use the resumable batch script:

```bash
uv run --no-sync python -u scripts/run_structured_data_discovery.py \
  --output-dir data/structured_data_trials/D2_discovery_development_20261125 \
  --execute
```

Reuse that exact output directory to resume. Omit `--execute` for offline
preparation/status. The runner appends `runner.log` and updates `summary.json`
with progress, failures and cumulative spending. It skips completed and known
billed attempts, preserves all responses, and stops on uncertain charges or
changed frozen inputs. See `docs/data_extraction/working_notebook.md` for recovery
behavior and the experiment record. No additional environment sync is required.

### Spending guardrail

The user authorized a **$5 cumulative budget** for this workstream. Every live
request shares `data/structured_data_trials/openrouter_spend.jsonl`. Its entries
record the batch cost, running total, outstanding reservations and remaining funds.
`run.json` also records the spending summary. Use `--batch-id` to group calls into
an experiment; its default is the output directory name. The journal uses a process
lock and flushes reservations before any generation request.

Preflight fetches the public model catalogue (no generation charge) and snapshots
prices in `pricing.json`. For the three GPT-5.6 tiers, the input allowance uses
text/schema UTF-8 bytes, a 4,096-token framing allowance, and documented PNG patch
coverage with a 1.2 multiplier and rounding allowance. Other models retain a
full-context reservation. The output ceiling and worst published price tiers,
including cache writes, determine the reserved cost. Provider price ceilings are
sent with the request. A call that cannot fit the remaining budget is refused.
This conservative allowance is not an expected-cost estimate. An actual input
count exceeding the bound marks the run as failed and stops a comparison arm
for audit; its charge remains counted. See the
[image-token rules](https://developers.openai.com/api/docs/guides/images-vision).

After a response, OpenRouter's actual `usage.cost` replaces the reservation,
including when extraction validation fails. Missing/invalid billing retains the
allowance as unresolved; it is never counted as zero. The ledger is persistent
across runs and batches. Do not delete/reset it during this budget period. The
budget applies to this workflow's generation charges, separately from prior
metadata-calibration experiments. See
[OpenRouter usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting)
and [provider price ceilings](https://openrouter.ai/docs/guides/routing/provider-selection).

The first smoke test cost $0.00556775. The subsequent six-image Luna/Terra/Sol
comparison cost $0.91863977, bringing total spend to **$0.92420752**, leaving
**$4.07579248**. These are billed generation charges, not historical Flex estimates.
The comparison supports keeping Luna medium as the routine development reference:
Luna captured 58/60 printed observations and both larger tiers 60/60; all three
recovered the 36 chart estimates within tolerance. Interpretation differences
remain. Full scores and examples are in the working notebook.

On a completed response it preserves `response.json`, `raw_output.txt`, and
`observations.json`; numerical datasets additionally produce `structure.sdmx.json`
and `data.sdmx.json`. Validation rejects missing/extra fields, nonfinite numbers,
string/boolean numbers, duplicate complete keys, inconsistent status, and missing
evidence for estimates. Truncated, refused, invalid and failed responses retain
available evidence and never become a successful SDMX result. Partial extractions
retain their usable observations, identify omissions, and exit nonzero. Unsupported
images produce an explicit result without fabricated SDMX observations. Inspect
`run.json` and `observations.json` alongside exchange files for omissions and
completion status; schema validation does not verify image accuracy.
SDMX dataset annotations of local type `DATA_SNAPSHOT_COMPONENT` also retain
component ID/title and image-level extraction status, omissions and notes.

### Provisional DSD, not a frozen design

`profiles/snapshot_indicators.json` is the editable LOCAL
`SNAPSHOT_OBSERVATIONS(0.1.0)` draft; override it with `--dsd`. Its exact dimension
and attribute definitions generate both the response schema and the SDMX DSD.
The model cannot introduce new dimensions. It can return multiple component
datasets using the same DSD, with image-local evidence on each observation.

The initial draft combines indicator/category/comparison structure, statistical
operation, population/sex/age, reference area, source reporting period, reporting
role, units and model/term distinctions. Attributes cover scale, bounds, stated
confidence, significance, source observation status and interpretive notes.
Python adds printed/estimated method, original number text, location and an
extraction qualification as observation attributes.

This draft borrows concepts from the reviewed standards; it has not adopted their
code lists or established interoperability with those datasets. Dimensions remain
uncoded strings. Null key values serialize as the local `_UNKNOWN` marker;
`_NOT_APPLICABLE` is a different local literal with an explicit meaning in the
draft. Neither is an official universal SDMX code. `REPORTING_PERIOD` deliberately
preserves source text and is not yet a normalized SDMX `TIME_PERIOD`. No country,
currency or date is filled in merely to satisfy a borrowed structure.

Known design questions include multiple independent category breakdowns, geographic
hierarchies, continuous x coordinates, and simultaneous reporting-role distinctions
such as planned/actual and overall/financed amounts. These must be checked on the
development images; the current generic fields are not evidence that every case
is covered. Record an omission when a key cannot represent a distinction faithfully.

DSD design will reuse Paper 2's 210 development images and 202 validation images
from Paper 1's corpus. Develop and revise on the 210, freeze a version, then assess
representational coverage on the 202. LLM extraction accuracy, model selection and
cost comparison are separate experiments; validation images should not be used
for prompt/model tuning before the final assessment.

## Environment

From the repository root, using Python 3.10 and the pinned `uv` environment:

```bash
uv sync --locked --extra structured_data --extra test
uv run --no-sync docling-tools models download \
  layout tableformer rapidocr granitedocling \
  --rapidocr-backend-lang onnxruntime:en
```

Models are prefetched in `~/.cache/docling/models`. The prototype uses that
artifact directory explicitly. Pipelines default to CPU; use `--device cuda:0`
for the verified GPU paths. Granite uses FP32 on both devices,
without quantization or compilation, for compatibility with the GTX 1650 Ti.
The standard pipeline performs full-image RapidOCR and TableFormer recognition.
The Granite pipeline uses the small `granite_docling` preset with the documented
`Convert chart to table.` instruction. It is distinct from the larger Granite
Vision chart-enrichment models.

The standard GPU pipeline accelerates layout and table recognition while keeping
ONNX OCR on CPU. The small Granite GPU model fits on the GTX 1650 Ti in the
guarantee-chart smoke test; this does not establish a memory bound for all images.

New Granite runs have a 2048-token output limit. Docling marks output that reaches
the generation limit as incomplete; the CLI refuses to transform such a result.
The initial chart trials used the preset's 8192-token limit. Interrupted runs are
recorded explicitly rather than being reported as successful extraction.

### Dedicated chart extraction

`--pipeline chart` adds picture classification and dedicated Chart2CSV enrichment
to the standard pipeline. It uses the smaller `granite_vision_v3_3` preset,
distinct from both Granite-Docling-258M and the current default Granite Vision 4B.
No new Python dependencies or environment synchronization are needed.

Download the additional models once:

```bash
uv run --no-sync docling-tools models download \
  picture_classifier granite_chart_extraction_v3_3
```

The chart weights alone are approximately 6.15 GB on disk. They exceed this
machine's 4 GiB GPU even at 16-bit precision. This configuration therefore uses
CPU BF16 to reduce RAM requirements, without quantization or compilation.
The CPU lacks native BF16 acceleration. The first verified guarantee-chart run
used image scale 0.5, took approximately seven minutes, and peaked at 7.90 GiB
process RSS; all four values and category/series associations matched the image.
See the working notebook for the result and its single-example limitations.
The corrected GPU/CPU-offload path also matched all four bar-chart observations.
It took 263.16 seconds versus 437.51 seconds on CPU in individual smoke tests
(about 1.7× faster), with peak PyTorch allocation of 1.59 GiB and peak process
RSS of 9.87 GiB. CUDA context/driver memory is additional to PyTorch's figures.
The pie example matched both percentages on CPU and GPU/offload. The Shona GPU
run recovered 20 estimates but contains numerical errors and omits error bars.
The regression table's 42 printed numeric cell strings match the image, but its
statistical interpretation/mapping remains pending. See the notebook for the
five-example review. Peak process RSS reached 10.60 GiB in the Shona offload run.

For chart GPU execution, layout/OCR/classification stay on CPU. The chart model
uses FP16, retains its small image-feature parameter on GPU, and streams its
larger components from CPU using Accelerate. Functional attention requires
preloading its child weights. This adapter depends on the pinned LlavaNext/Docling
implementation and must be checked after upgrades. No quantization is used.

After downloading, run the first example in a fresh output directory:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
uv run --no-sync python -m data_snapshot.structured_data_extraction \
  /home/ajd/hf_datasets/data-snapshot/snapshots/prwp/document_10000660_figure_002.png \
  --pipeline chart --device cpu \
  --output-dir data/structured_data_trials/guarantee_chart_enrichment_01
```

To use the tested GPU/offload path, select `--device cuda:0` and a fresh output
directory, for example:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
uv run --no-sync python -m data_snapshot.structured_data_extraction \
  /home/ajd/hf_datasets/data-snapshot/snapshots/prwp/document_10000660_figure_002.png \
  --pipeline chart --device cuda:0 \
  --output-dir data/structured_data_trials/guarantee_chart_gpu_01
```

Inspect `native.json` for picture classification and
`pictures[].meta.tabular_chart.chart_data`. Expected chart associations are
HIGH/MUTUAL 15, HIGH/PUBLIC 7, LOW_MIDDLE/MUTUAL 7, LOW_MIDDLE/PUBLIC 17.
Classification can prevent extraction if the picture is not recognized as a
supported chart. The enrichment stage also skips chart data already present;
using standard conversion avoids reusing the small VLM's incorrect chart table.

Chart generation is capped at 2048 tokens. Unlike full-page VLM conversion,
the installed enrichment code does not propagate the generation finish reason
into conversion status. Treat native chart output as unverified, including
possible truncation; this path has no automatic chart-to-SDMX mapping.

## First end-to-end example

The income profile supplies the interpretation of the axes and expected column
headings; it contains no expected numerical observations. It does not supply
currency or time information that is absent or ambiguous in the crop.

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
uv run --no-sync python -m data_snapshot.structured_data_extraction \
  /home/ajd/hf_datasets/data-snapshot/snapshots/unhcr/108733-revised-public-wb-unhcr-policy-brief-final_table_000.png \
  --output-dir data/structured_data_trials/income \
  --profile src/data_snapshot/structured_data_extraction/profiles/income.json
```

Each image gets a subdirectory containing:

- `native.json`: the untouched Docling document.
- `observations.json`: long observations, profile, source image and native cell references.
- `structure.sdmx.json`: local concept scheme and DSD, with string dimensions.
- `data.sdmx.json`: indexed observation data referencing the accompanying structure.
- `run.json`: input hash, runtime version, pipeline, elapsed time, and outcome.

Output directories must be fresh; existing runs are never overwritten. A mapping
failure retains the native extraction and error report, exits nonzero, and does
not produce an SDMX success artifact. `extracted_only` means native extraction
completed, not that its observations have been verified.

## Other agreed examples

`examples.json` records all five images and the purpose of each trial. Select a
fresh output directory for each trial. Omit `--profile` to inspect extraction
before deciding how to interpret it. For example:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
uv run --no-sync python -m data_snapshot.structured_data_extraction \
  /home/ajd/hf_datasets/data-snapshot/snapshots/prwp/document_10000660_figure_002.png \
  --pipeline granite --output-dir data/structured_data_trials/guarantee
```

Charts can store recovered tables under
`pictures[].meta.tabular_chart.chart_data`, rather than `tables[]`. Preserve
that evidence and review it. The first mapper deliberately only accepts one
rectangular table with a single header row and row labels in the first column.
It rejects merged headers, missing cells, duplicate observation keys, significance
marks, parentheses and unit-bearing numbers. Explicit empty cells and missing
markers become null, never zero. It does not infer a DSD for an arbitrary chart
or regression table and does not silently correct model output.

## SDMX status and design decisions

The local `INCOME_SUMMARY` DSD is an experimental definition at version `0.1.0`.
It is not the WDI, UNICEF or SDG DSD. `CATEGORY` and `STATISTIC` express the
observed income-table axes; `OBS_VALUE` is its numerical measure. The dimensions
are uncoded strings to preserve displayed labels during the first trial. Adopting
standard code lists and a shared general structure remains a subsequent design
decision, informed by the WDI/UNICEF/UNHCR review.

Both exchange messages are checked against vendored official schemas for
SDMX-JSON 2.1.0 / SDMX 3.1.0. The mapper checks table shape, expected headings,
finite values and unique complete keys before serialization. Message dimensions,
positions, values and concept references are generated from that same model.
This bounded validation does not replace a general SDMX registry validator,
establish domain-level interoperability, or prove numerical accuracy.

Original sources for the unmodified schemas:

- https://json.sdmx.org/2.1.0/sdmx-json-data-schema.json
- https://json.sdmx.org/2.1.0/sdmx-json-structure-schema.json

## Checks

```bash
uv run --no-sync python -m pytest -q tests/test_structured_data_extraction.py
uv run --no-sync python -m pytest -q tests/test_structured_data_llm.py
```

The income test values were manually transcribed from the PNG, independently of
Docling. These tests check transformation and serialization; live extraction
must additionally be compared with the image. The new CLI retains fresh run
directories so failed trials remain available for review.
