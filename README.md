# Data Snapshot Research Workspace

Research and exploratory tooling for finding, annotating, evaluating, and
describing data snapshots in institutional documents.

A **data snapshot** is a table, chart, map, dashboard, or composite figure that
communicates data within a source document. This repository covers the full
research lifecycle rather than presenting one production application.

Two forms of extraction are kept distinct:

- **Data Snapshot Extraction** locates tables and figures in documents and
  exports them as images and structured detections.
- **Data Snapshot Metadata Extraction** reads a data snapshot image and fills
  the canonical Data Snapshot Metadata Schema.

Source-document metadata is a third, separate concern.

## Research lifecycle

1. Annotate document pages and snapshots in Label Studio.
2. Extract candidate data snapshots with layout-detection models.
3. Benchmark detections against human annotations.
4. Characterize snapshots and develop the semantic metadata schema.
5. Validate and evolve the schema against held-out evidence.
6. Extract schema-conformant metadata from snapshot images.
7. Review generated metadata and save human-reviewed gold records.

## Repository areas

| Area | Purpose | Guide |
|---|---|---|
| Data Snapshot Annotation | Create, pre-label, export, restore, and convert Label Studio projects | [Annotation guide](src/data_snapshot/annotation/README.md) |
| Data Snapshot Extraction | Run TF-ID, DocLayout-YOLO, YOLO11, and YOLO26 adapters | [Extraction guide](src/data_snapshot/inference/README.md) |
| Extraction Benchmarking | Evaluate detections, merge runs, filter predictions, and render comparisons | [Benchmarking guide](src/data_snapshot/evaluation/README.md) |
| Schema Discovery | Reproduce the discovery, validation, and schema-evolution research | [Schema discovery guide](notebooks/schema_discovery/README.md) |
| Canonical Metadata Schema | Validate metadata and generate JSON Schema and field references | [Schema guide](src/data_snapshot/metadata_schema/README.md) |
| Data Snapshot Metadata Extraction | Extract Schema v1.4 metadata from images and review gold records | [Metadata extraction guide](src/data_snapshot/metadata_extraction/README.md) |
| Source Document Metadata | Convert and normalize parent-document metadata for dataset publication | [Source metadata guide](src/data_snapshot/metadata/README.md) |
| Research Notebooks | Run maintained notebooks and identify historical material | [Notebook guide](notebooks/README.md) |
| Schema Discovery Manuscript | Build and maintain the Paper 2 manuscript | [Manuscript guide](docs/schema-discovery_manuscript/README.md) |

## Research projects

### Paper 1: Data Snapshot Extraction Benchmarking

The extraction-benchmarking study uses the annotation, extraction, and
evaluation areas above. Its paper is maintained externally in Overleaf and is
not included in this repository.

- Paper: [Benchmarking Open-Source Layout Detection Models for Data Snapshot
  Extraction from Institutional Documents](https://arxiv.org/abs/2606.06242)
- Dataset: [ai4data/data-snapshot](https://huggingface.co/datasets/ai4data/data-snapshot)
- Evaluation contract: [Unified Evaluation Schema v1.3](docs/data-snapshot-eval-v1.3.schema.json)
- Methodology: [Evaluation specification](docs/evaluation_spec.md)

### Paper 2: Data Snapshot Metadata Schema Discovery

The schema-discovery study covers snapshot characterization, broad schema
discovery, held-out validation, standards-informed evolution, and the canonical
metadata schema. Its tracked manuscript and research evidence are retained in
this repository.

- Workflow: [Schema discovery notebooks](notebooks/schema_discovery/README.md)
- Schema versions: [`docs/schema_v1.2`](docs/schema_v1.2),
  [`docs/schema_v1.3`](docs/schema_v1.3), and
  [`docs/schema_v1.4`](docs/schema_v1.4)
- Manuscript: [`docs/schema-discovery_manuscript`](docs/schema-discovery_manuscript/README.md)

## Installation

The canonical environment manager is [uv](https://docs.astral.sh/uv/). Python
3.10 is required and `uv.lock` records the resolved environment.

```shell
# Core package
uv sync --locked

# Daily development, tests, notebooks, and metadata review
uv sync --locked --extra dev

# Add only the model currently being used
uv sync --locked --extra dev --extra yolo26
```

Model adapters have separate, potentially large dependency groups. Install only
the adapter being used; see the [Data Snapshot Extraction
guide](src/data_snapshot/inference/README.md).

### Notebook kernels

The repository does not maintain a separate Conda environment. Install and
register the locked `uv` kernel once:

```shell
uv sync --locked --extra dev
uv run --no-sync python -m ipykernel install --user \
    --name data-snapshot --display-name "Data Snapshot (uv)"
```

Launch Jupyter from the repository environment:

```shell
uv run --no-sync jupyter lab
```

Editors may also select the **Data Snapshot (uv)** kernel or the repository's
`.venv/bin/python` interpreter. Conda is not used for this repository.

## Environment variables

Copy `.env.template` to `.env` and populate only the credentials needed by the
workflow:

```text
LABELSTUDIO_API_KEY=  # Label Studio project operations
OPENAI_API_KEY=       # Schema research and metadata extraction API calls
```

Never commit `.env`. Offline tests use fake clients and do not require either
credential.

## Verification

Run the maintained offline suite without calling external services:

```shell
uv run --no-sync pytest
uv run --no-sync python -m data_snapshot.metadata_schema.generation --check
```

Adapter tests are skipped when their model-specific optional dependencies are
not installed. Live Label Studio operations, model downloads, and OpenAI calls
are workflow checks rather than offline test-suite requirements.

## Data and generated outputs

Large corpora, Label Studio state, model weights, generated predictions, and
most experiment outputs are gitignored. Notebooks and commands may therefore
require local files that are not available in a clean clone. Each local guide
identifies its expected inputs and outputs.

Tracked reports and outputs are research evidence. Historical notebooks are
retained even when they use retired package names or depend on local data; see
the [notebook status guide](notebooks/README.md) before treating one as a
current entry point.

## License

MIT License; see [LICENSE](LICENSE).

## Citation

```bibtex
@misc{dy2026benchmarkingopensourcelayoutdetection,
      title={Benchmarking Open-Source Layout Detection Models for Data Snapshot Extraction from Institutional Documents},
      author={AJ Carl P. Dy and Aivin V. Solatorio},
      year={2026},
      eprint={2606.06242},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2606.06242},
}
```
