# Data Snapshot Annotation

Label Studio tooling for creating human-annotated data-snapshot corpora from
PDF documents. This area manages annotation projects and converts Label Studio
exports into the Unified Evaluation Schema used by extraction benchmarking.

## Setup

Install the core package and start the repository's pinned Label Studio and
PostgreSQL services:

```shell
uv sync --locked
docker compose up
```

Open `http://localhost:8080/` and create a Label Studio account. In Label
Studio, enable legacy API tokens under **Organization > API Tokens Settings**,
then copy the token from **Account & Settings > Legacy Token**.

Copy `.env.template` to `.env` and set:

```text
LABELSTUDIO_API_KEY=your-token
```

The Docker services store local state in the gitignored `labelstudio_data/` and
`pg_data/` directories. Back up those directories or export projects before
changing the Docker configuration. If Docker reports a permission error,
inspect and repair ownership of those two directories only; do not make the
entire repository world-writable.

## Create an annotation project

Place source PDFs in a local directory such as `pdf_input/`, then run:

```shell
uv run --no-sync python -m data_snapshot.annotation.create_tasks \
    --project_name="My annotation project" \
    --dataset_name=my_dataset \
    --input_pdf_dir=pdf_input/
```

The command converts PDF pages to images, creates the Label Studio project,
and imports its tasks.

## Create a project with model pre-labels

Generate a prediction file with a [Data Snapshot Extraction
adapter](../inference/README.md), then run:

```shell
uv run --no-sync python -m data_snapshot.annotation.create_tasks_with_prelabeling \
    --project_name="My pre-labeled project" \
    --dataset_name=my_dataset \
    --input_pdf_dir=pdf_input/ \
    --pred_json_path=data/evaluation_input/preds.json
```

To take figures from one prediction file and tables from another:

```shell
uv run --no-sync python -m data_snapshot.annotation.merge_class_preds \
    --figure_preds=data/evaluation_input/figure_preds.json \
    --table_preds=data/evaluation_input/table_preds.json \
    --output_json_path=data/evaluation_input/combined_preds.json
```

## Back up and restore projects

Before exporting, submit all annotations and confirm that no drafts remain.

```shell
uv run --no-sync python -m data_snapshot.annotation.export_project \
    --project_id=22 \
    --output_path=data/backups/project_22_backup.json
```

Restore the backup with the original PDFs:

```shell
uv run --no-sync python -m data_snapshot.annotation.import_project \
    --project_name="My restored project" \
    --input_path=data/backups/project_22_backup.json \
    --input_pdf_dir=pdf_input/
```

The optional `--dataset_name` must match the backup's media paths. When image
paths need manual repair, follow the [local-storage setup
guide](../../../docs/manual_setup.md).

## Export benchmarking ground truth

Convert a Label Studio JSON export into Unified Evaluation Schema v1.3:

```shell
uv run --no-sync python -m data_snapshot.annotation.labelstudio_adapter \
    --input_json_path=path/to/labelstudio_export.json \
    --output_json_path=data/evaluation_input/ground_truth.json
```

The resulting file is the ground-truth input for the [benchmarking
tools](../evaluation/README.md).

## Verification

The offline adapter and shared utility tests do not require a running Label
Studio service:

```shell
uv sync --locked --extra test
uv run --no-sync pytest tests/test_adapters.py tests/test_adapter_utils.py
```

Creating, exporting, and importing projects are integration operations and
require the local Docker services and a valid API token.
