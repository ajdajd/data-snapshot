# PNG structured data extraction prototype

Independent of `metadata_extraction` and `metadata_schema`. Input is a PNG;
native extraction is Docling JSON. A reviewed table mapping can additionally
produce long observations, a local DSD, and SDMX-JSON 2.1.0 data. CSV, remote
models, RapidAI, and an interactive reviewer are deferred.

The central [plan and experiment notebook](../../../docs/data_extraction/working_notebook.md)
records decisions, candidate DSDs, hardware checks and live findings.

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
The CPU pie example also matched both percentages; GPU pie/Shona runs are untested.

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
```

The income test values were manually transcribed from the PNG, independently of
Docling. These tests check transformation and serialization; live extraction
must additionally be compared with the image. The new CLI retains fresh run
directories so failed trials remain available for review.
