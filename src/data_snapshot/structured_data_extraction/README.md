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
artifact directory explicitly. Both pipelines default to CPU; use `--device cuda:0`
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
