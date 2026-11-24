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
sent. Use those examples to clarify his proposed interaction between model
inference, user confirmation, and data extraction.

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

The user-confirmation workflow is still a hypothesis to discuss with Aivin. One
interpretation is: propose a model/mapping, show a preview, let the user correct
uncertain meanings, then populate and export the observations. It may be a mapping
to a shared DSD, rather than a new DSD per image.

### Exchange version

Use **SDMX 3.1.0** and **SDMX-JSON 2.1.0**. Their version numbers describe different
specifications. [AI4Data's dissemination standards guide](https://worldbank.github.io/ai4data/cookbook/ai-ready-dissemination/standards/)
lists SDMX 3.1. The [official data schema](https://json.sdmx.org/2.1.0/sdmx-json-data-schema.json)
identifies that pairing. Metadata Editor's bundled JSON 2.0 schema concerns
reference metadata and is not an observation-data exchange requirement.

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
Our current trials do not enable that stage. The poor results from the small
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
It has a PNG CLI, two local Docling pipelines, a reviewed income mapping profile,
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
- Some existing console launchers still reference the old
  `data-snapshot-annotation` checkout. Tools were invoked as Python modules
  through `uv run --no-sync python -m ...` to use the current environment.
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

Evidence roots under `data/structured_data_trials/`:

- `20261124_standard_01`: first failed environment attempt (missing `cv2`).
- `20261124_standard_02`: verified CPU income extraction, observations and SDMX.
- `20261124_standard_03`: native regression extraction.
- `20261124_granite_01`: CPU guarantee-chart extraction.
- `20261124_granite_02`: CPU pie extraction and interrupted Shona attempt.
- `20261124_gpu_standard_01`: verified GPU income output.
- `20261124_gpu_granite_01`: GPU guarantee-chart extraction.
- `20261124_gpu_granite_02`: bounded GPU Shona rerun.

These large/generated outputs are gitignored. The income test fixture is manually
transcribed from the source image and is independent of model predictions.

## Checks and interpretation

- 15 focused offline tests pass: observation associations, official-schema
  validation, indexed-data decoding, missing versus zero, ambiguous numbers,
  malformed structures, GPU option forwarding, immutable runs and interruption.
- The focused suite plus existing metadata-schema tests passed (107 tests).
- `uv lock --check --offline` passes. The new `structured_data` extra reuses the
  pinned Docling stack and declares its TF-ID dependency conflict explicitly.
- A wheel build includes both official schemas, the income mapping profile and
  the five-example manifest.

Schema validity establishes representation, not numerical truth. Likewise,
Docling conversion success means a document was produced, not that chart values
or statistical meanings are correct. Native-only runs use `extracted_only`;
they are never labelled verified numerical datasets.

## Next actions and open questions

1. Keep the verified income example as the first tangible end-to-end artifact.
2. Review chart failures before adding automatic chart-to-SDMX mappings. Consider
   another Docling model/configuration only with an explicit hardware assessment.
3. Compare the actual extracted examples with WDI/UNICEF/UNHCR concepts; document
   where reuse works, where extensions are needed, and what requires confirmation.
4. Use the native extraction, long observations, local DSD and failure examples
   to clarify the intended model-inference/user-interaction workflow with Aivin.

Unresolved: the eventual shared DSD; standard-code mapping; units absent from
crops; time intervals that are not regular frequencies; confidence/error-bar
interpretation; regression-table semantics; and correction review policy.
