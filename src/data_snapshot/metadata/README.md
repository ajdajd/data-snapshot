# Source Document Metadata Tools

Utilities for converting and normalizing metadata about the parent source
document. These records support dataset publication and contextual workflows;
they are not fields in the Data Snapshot Metadata Schema.

## Environment

```shell
uv sync --locked
```

## Convert UNHCR and ReliefWeb metadata

Convert scraped UNHCR/ReliefWeb report metadata to the target document metadata
shape:

```shell
uv run --no-sync python -m data_snapshot.metadata.unhcr_to_schema \
    --input_dir=data/hf_metadata_source/unhcr/ \
    --output_dir=data/hf_metadata_converted/unhcr/
```

The field mappings and source-specific decisions are documented in
[`docs/UNHCR_TO_SCHEMA_MAPPING.md`](docs/UNHCR_TO_SCHEMA_MAPPING.md).

## Enforce a common dataset shape

Hugging Face datasets backed by Apache Arrow require compatible keys and value
types across records. Apply one common deep template across every subset that
will be loaded together:

```shell
uv run --no-sync python -m data_snapshot.metadata.enforce_metadata_schema \
    --input_dir data/hf_metadata_converted/unhcr/ \
    --input_dir data/hf_metadata_source/prwp/ \
    --input_dir data/hf_metadata_source/refugee/ \
    --output_dir data/hf_metadata_fixed/
```

Always write to a separate output directory and inspect the result before
replacing source data. The command normalizes nested keys, empty list element
types, and date-like values for cross-record compatibility.

## Inputs and outputs

The repository's `data/` directory is gitignored. A clean clone therefore does
not include the scraped source records or converted output. Keep source,
converted, and schema-enforced directories separate so transformations remain
auditable.

These tools currently have executable CLI help but no dedicated automated test
module. Use a copied representative subset for a workflow smoke test before
processing a full corpus.
