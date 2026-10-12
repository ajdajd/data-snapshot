# Data Snapshot Metadata Extraction

Extract semantic Schema v1.4 metadata from an individual data snapshot image.
The extractor uses the canonical Pydantic model as its response contract and
validates every completed structured output before returning it.

This workflow starts from an already extracted table, chart, map, dashboard,
or composite image. It is distinct from [Data Snapshot
Extraction](../inference/README.md) and from [source-document metadata
processing](../metadata/README.md).

## Environment

Install the core package and set the API credential only when making live
requests:

```shell
uv sync --locked
```

```text
OPENAI_API_KEY=your-key
```

The default request configuration is
[`config/default.json`](config/default.json). It selects the model, service
tier, reasoning effort, timeout, prompt-cache key, and output-token budget.
Prompts live in `prompts/`.

## Extraction workflow

The maintained batch workflow is
[`notebooks/metadata_extraction/extraction.ipynb`](../../../notebooks/metadata_extraction/extraction.ipynb).
Install and launch its locked environment with:

```shell
uv sync --locked --extra notebooks
uv run --extra notebooks jupyter lab notebooks/metadata_extraction
```

The notebook reads snapshot images from the configured local data directories,
calls `data_snapshot.metadata_extraction.extract_metadata`, and appends
resumable JSONL results and errors. These data and output directories are
normally gitignored.

Controlled calibration configurations and results are preserved alongside the
notebook. Validate a calibration's paths and request without making an API call:

```shell
uv run python notebooks/metadata_extraction/run_calibration.py c15 --dry-run
```

Export successful JSONL metadata objects into individual JSON files:

```shell
uv run python notebooks/metadata_extraction/export_metadata.py \
    --input_path=notebooks/metadata_extraction/outputs/batch1_results.jsonl \
    --output_dir=notebooks/metadata_extraction/exported/
```

## Human review

Use the [Data Snapshot Metadata
Reviewer](../metadata_reviewer/README.md) to compare generated JSON with its
snapshot and save separately validated gold records. Generated predictions are
immutable; reviewed gold is the editable output.

## Historical implementation

`data_snapshot.metadata_extraction_v1_1` and
`notebooks/metadata_extraction/extraction_v1.1/` preserve the earlier Schema
v1.1 workflow. The archived Python package intentionally contains stale paths
and is not the current extraction entry point.

## Verification

Offline tests use fake API clients and make no paid requests:

```shell
uv run --extra test pytest \
    tests/test_metadata_extraction.py \
    tests/test_metadata_schema.py
```

A green offline suite verifies configuration, request construction, structured
output handling, and canonical validation. It does not verify current model
availability or execute live extraction.
