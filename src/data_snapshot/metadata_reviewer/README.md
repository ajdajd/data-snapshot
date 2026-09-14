# Data Snapshot Metadata Reviewer

Local Streamlit utility for reviewing LLM-generated Data Snapshot metadata
against its PNG image and saving a human-reviewed gold JSON record.

This utility creates labels. It does not calculate extraction metrics or modify
the generated predictions.

## Install and run

From the repository root, in a **WSL terminal**:

```shell
uv sync --extra review
uv run --extra review streamlit run \
    src/data_snapshot/metadata_reviewer/app.py
```

The default dataset roots are:

```text
snapshots: notebooks/metadata_extraction/data/snapshots
generated: notebooks/metadata_extraction/exported
gold:      notebooks/metadata_extraction/gold
```

Pass different roots after Streamlit's `--` argument separator:

```shell
uv run --extra review streamlit run \
    src/data_snapshot/metadata_reviewer/app.py -- \
    --snapshots-root /path/to/snapshots \
    --generated-root /path/to/exported \
    --gold-root /path/to/gold
```

## File discovery

The reviewer recursively searches the three roots and matches files by their
globally unique filename stem. Generated filenames ending in `_metadata.json`
are matched after removing `_metadata`.

Supported snapshots have this relative structure:

```text
{source}/{type}/{snapshot_id}.png
```

`source` must be `unhcr`, `prwp`, or `refugee`; `type` must be `figure` or
`table`. A newly saved gold file mirrors that snapshot path:

```text
{gold_root}/{source}/{type}/{snapshot_id}.json
```

An existing gold file with the same stem is reused even if it is elsewhere
under the gold root. Duplicate stems are fatal. Missing counterparts,
unsupported snapshot paths, and orphan gold files are shown as warnings and
excluded from review.

The generated and gold roots must not overlap.

## Review workflow

1. The app opens the first snapshot without a gold file.
2. If gold exists, it becomes the editable working record. Otherwise the
   generated metadata pre-fills the form.
3. Scroll the editor independently while the snapshot remains visible.
4. All nested structures and fields are displayed, including blank placeholders
   for metadata that was missing from the generated record. A blank placeholder
   is not added to the working record until a value is entered.
5. Add, remove, reorder, or edit nested values as needed. Each field shows its
   canonical definition. Use **?** for the generated value and **ⓘ** for schema
   examples.
6. Orange labels identify values that differ from the immutable generated
   reference. The full generated JSON remains available in its own tab.
7. Select **Save Gold & Next**. The app validates the entire working record
   with the canonical `DataSnapshotMetadata` Pydantic model before saving.

Saving without edits is intentional: it records that the generated metadata is
already correct. A snapshot is considered reviewed when its gold file exists.

There is no autosave or draft file. If the working record has unsaved edits,
Previous or Next requires an explicit **Save & move**, **Discard & move**, or
**Cancel** decision. Validation errors are displayed by field path without
discarding the current edits.

## Data behavior and safety

- Generated JSON is read-only and is never a save target.
- Gold is written atomically to reduce the chance of a partial file.
- Saved records use `model_dump(mode="json", exclude_none=True)`.
- Missing and null values are treated as equivalent.
- The Pydantic model's intentional text normalization and exact-list
  deduplication occur during validation and saving.
- The UI does not infer, repair, or independently validate semantic metadata.

## Tests

From the repository root, in a **WSL terminal**:

```shell
uv run --extra dev --extra review pytest \
    tests/test_metadata_reviewer.py \
    tests/test_metadata_reviewer_app.py \
    tests/test_metadata_schema.py
```

The tests cover discovery, immutable generated records, canonical atomic saves,
field-difference highlighting, dirty-navigation protection, and the interactive
save path.
