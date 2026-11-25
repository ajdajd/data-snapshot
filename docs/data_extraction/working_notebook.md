# Data Snapshot structured data extraction — working notebook

Started: 2026-11-24 (Asia/Manila). This is the central record of the plan,
decisions, experiments, findings, and open questions. A possible future Paper 3
is motivation for preserving evidence, not a required output of this prototype.

## Current plan

Build a complete local Docling example before expanding to other stacks:

1. Accept a PNG already saved on disk.
2. Extract its contents with Docling, preserving native JSON.
3. Interpret the extracted structure and map it to long statistical observations.
4. Describe those observations using a local DSD informed by existing standards.
5. Generate SDMX-JSON and validate its representation and the mapped observations.
6. Compare the values and associations against the image; keep failures as evidence.

The first success case is the monthly-income table. After that, compare the
remaining agreed examples to identify which extraction and mapping problems need
attention. Consult Aivin once tangible outputs are available; no message has been
sent. After dedicated chart enrichment has been tested, use the examples to
clarify what he meant by the data model and the scope of a separate review workflow.

Later experiments, in order:

- An image plus native extraction supplied to an LLM for model interpretation,
  conversion, and evidence-backed extraction corrections. Use Structured Outputs
  through OpenRouter/OpenAI, then the same SDMX serialization and validation.
- RapidAI extraction with stack-specific mapping into the common statistical model.
- A pure LLM image-to-statistical-data path, compared using the same examples.

These alternatives are deferred until the Docling path produces reviewable results.

## Agreed scope and constraints

- Input: PNG images. Do not connect this prototype to the PDF detection/cropping
  workflow. Note PDF-only restrictions when evaluating other libraries.
- Primary output: SDMX-JSON. CSV is a possible later export, not the design target.
- Code must remain independent of `metadata_extraction` and `metadata_schema`.
- Start from the same 102 images selected for metadata extraction. The directory
  `/home/ajd/hf_datasets/data_snapshot_metadata_gold` contains metadata JSON only;
  all 102 filenames match PNGs in `/home/ajd/hf_datasets/data-snapshot/snapshots`.
  The gold metadata is not an inference input or numerical ground truth.
- Aim for one shared DSD, or at most two if the examples justify it. Separate
  figure/table extraction code does not itself require separate statistical DSDs.
- Develop the definition incrementally, version changes, and record their reasons.
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

### Extraction and review are separate workflows

User clarification: build extraction first and defer the user-confirmation/review
workflow. Extraction is the automated path from PNG through native extraction,
statistical interpretation/mapping, long observations and SDMX output. Calling it
mechanical does not imply that it is error-free or that statistical interpretation
is solved; uncertain cases still need explicit failure or review flags.

The later review workflow may involve checking source images, correcting values
and their associations, resolving uncertain statistical meanings, and approving
results. It may need a UI, but its design and scope are not decided. Do not make
an interactive confirmation step a prerequisite for this extraction prototype.
Confirm the intended separation with Aivin alongside the meaning of data model.

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
It is already a local generative-model experiment; the deferred LLM work concerns
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
| IMF ECOFIN | Broad economic/financial dissemination through one relatively compact DSD | Domain, area, indicator, counterpart area, frequency and time; substantial meaning is encoded in indicator codes. Documentation reviewed; attempted live DSD request returned 404. [IMF description](https://www.imf.org/-/media/files/news/seminars/2021/sdmx/siii-presentation-02-modeling-approaches-ecofin-dsd.pdf). |
| Global SDG DSD | Development indicators and disaggregation | Broad reference with explicit customization guidance; SDG codes should not be assigned to unrelated data. [DSD and guides](https://unstats.un.org/sdgs/iaeg-sdgs/sdmx-working-group/). |
| Global labour, education, national accounts, government finance and CPI DSDs | Domain-specific concepts and classifications | Reference candidates when an example needs those concepts. [Labour](https://sdmx.org/sdmx-for-labour/), [education](https://sdmx.org/sdmx-for-education/), [accounts/prices](https://sdmx.org/sdmx-data-structure-definitions-for-national-accounts-sdmx-na/). |
| SDMX cross-domain concepts and code lists | Common definitions for area, time, units, multipliers and status | Reusable building blocks, not a complete DSD. [Guidelines](https://sdmx.org/guidelines/). |

Initial priority: compare WDI and UNICEF for compact structure, UNHCR for
humanitarian meaning, and CRS when reaching funding examples. No candidate has
yet been adopted wholesale. Changed definitions need our own identity/version;
they must not be presented as unmodified global DSDs.

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
GPU/offload execution has not been checked on the pie or Shona images yet.

- [Reviewed comparison](../../data/structured_data_trials/20261125_chart_offload_debug_03/comparison.json).
- [Native extraction](../../data/structured_data_trials/20261125_chart_offload_debug_03/document_10000660_figure_002/native.json).
- [Run metadata](../../data/structured_data_trials/20261125_chart_offload_debug_03/document_10000660_figure_002/run.json).
- [Peak CUDA measurements](../../data/structured_data_trials/20261125_chart_offload_debug_03/cuda_memory.json).
- [Runtime/RAM measurements](../../data/structured_data_trials/20261125_chart_offload_debug_03/resources.txt).

## Checks and interpretation

- 19 focused offline tests pass: observation associations, official-schema
  validation, indexed-data decoding, missing versus zero, ambiguous numbers,
  malformed structures, pipeline/device forwarding, immutable runs, interruption,
  chart CPU/BF16 configuration, unavailable-CUDA rejection, preserved failure
  tracebacks and repeated component-offload calls with direct parameter and
  functional attention child-weight access.
- The focused suite plus existing metadata-schema tests pass (111 tests).
- Live assertions verified the bar chart on CPU and GPU/offload (4/4 each), and
  the pie on CPU (2/2), without altering the native extraction files.
- `uv lock --check --offline` passes. The new `structured_data` extra reuses the
  pinned Docling stack and declares its TF-ID dependency conflict explicitly.
- A wheel build includes both official schemas, the income mapping profile and
  the five-example manifest.

Schema validity establishes representation, not numerical truth. Likewise,
Docling conversion success means a document was produced, not that chart values
or statistical meanings are correct. Native-only runs use `extracted_only`;
they are never labelled verified numerical datasets.

## Next actions and open questions

1. Use the worked income example above to explain the data/DSD/exchange distinction.
2. Dedicated enrichment checks are complete on the guarantee chart (4/4 on CPU
   and GPU/offload) and refugee pie (2/2 on CPU). Use these results before expanding
   to Shona or more samples. Keep raw failures; do not add automatic chart-to-SDMX
   mappings before review. No quantization is planned as part of the offload fix.
3. Compare the actual extracted examples with WDI/UNICEF/UNHCR concepts; document
   where reuse works, where extensions are needed, and what requires confirmation.
4. The draft below now includes measured enrichment results. Use the native
   extraction, long observations and local DSD to clarify the data-model meaning
   and extraction/review separation with Aivin. Sending remains the user's action.

Unresolved: the eventual shared DSD; standard-code mapping; units absent from
crops; time intervals that are not regular frequencies; confidence/error-bar
interpretation; regression-table semantics; and correction review policy.

## Draft message to Aivin (not sent)

Status: draft updated after the bar/pie CPU checks and bar GPU/offload check; not sent.

Hi Aivin, a quick update on structured data extraction from Data Snapshots.

I've implemented an initial local Docling pipeline that takes a PNG and preserves
the extracted document structure. For the simple income table, all 16 values and
their category/statistic associations matched the image. The regression table
was extracted, but its nested headers and coefficient/standard-error relationships
still need mapping. The initial chart results from the small Granite-Docling model
were incorrect or empty. With dedicated chart enrichment, the guarantee bar chart
now has all four values and their category/series associations correct. The refugee
pie chart also has both province percentages correct. CPU runs took about six to
seven minutes; GPU execution with CPU offloading reduced the bar-chart run to
about four minutes while preserving all four observations. These are initial
examples; broader chart accuracy remains to be tested.

Docling provides text, table cells and document structure, and can provide chart
data depending on the pipeline/model. To reach our SDMX target, we still need to
interpret these as statistical dimensions, measures and attributes, map them to
a Data Structure Definition (DSD), and write the observations in SDMX-JSON.

I'm understanding the DSD as the statistical schema: analogous to how the Data
Snapshot Metadata Schema defines our metadata fields, it defines the fields and
roles of the extracted statistical data. For example, the income table has
income category and summary statistic (Mean/Median) as dimensions, and the amount
as the measure. We have an experimental DSD for that example; the shared structure
still needs to be developed, preferably reusing existing SDMX concepts/DSDs.

Is this the kind of "data model" you meant in our last call, or were you referring
to something broader?

I'm also proposing two separate workflows: first, automated extraction and
conversion; second, a review workflow for correcting extraction errors and
confirming uncertain interpretations. The second may need a UI, but I suggest
deferring its design until we understand the extraction results better. Does
that separation match what you had in mind?
