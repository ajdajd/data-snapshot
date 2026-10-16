# Data Snapshot Extraction

Model adapters that locate tables and figures in PDF documents. Each adapter
converts model-specific output into the repository's [Unified Evaluation Schema
v1.3](../../../docs/data-snapshot-eval-v1.3.schema.json).

This is image extraction. It is distinct from [Data Snapshot Metadata
Extraction](../metadata_extraction/README.md), which reads an extracted image
and produces semantic metadata.

## Adapters

| Model | Dependency extra | Module |
|---|---|---|
| TF-ID Large | `tfid` | `data_snapshot.inference.tfid` |
| DocLayout-YOLO | `doclayoutyolo` | `data_snapshot.inference.doclayoutyolo` |
| YOLO11 Document Layout | `yolo11` | `data_snapshot.inference.yolo11` |
| YOLO26 Document Layout | `yolo26` | `data_snapshot.inference.yolo26` |

Install only the adapter required for a run:

```shell
uv sync --locked --extra yolo26
```

These extras are large and may install PyTorch, CUDA libraries, or other model
runtime dependencies. Model weights are downloaded from Hugging Face when a
configured local weight file is unavailable and are stored outside version
control.

## Run one adapter

All adapters accept an input PDF directory and write one prediction JSON file.
For example:

```shell
uv run --no-sync python -m data_snapshot.inference.yolo26 \
    --input_pdf_dir=pdf_input/ \
    --output_json_path=data/evaluation_input/yolo26.json
```

Replace `yolo26` in both places with the selected adapter and dependency extra.
The output contains documents, page-level detections, labels, normalized
bounding boxes, and run metadata.

## Batch extraction

The batch runner executes every supported adapter over numbered input
directories such as `pdf_input/unhcr_batch1/`:

```shell
uv sync --locked --all-extras
uv run --no-sync python -m data_snapshot.inference.batch_runner \
    --source unhcr --batch_start 1 --batch_end 5
```

Because the runner imports all four adapters at startup, it currently requires
all model extras. Per-adapter commands are preferable when only one model is
needed. Batch outputs are written beneath `data/batch_runs/` by default.

## Downstream use

- Use predictions to pre-label a [Label Studio annotation
  project](../annotation/README.md).
- Compare predictions with human ground truth using the [extraction
  benchmarking tools](../evaluation/README.md).
- Crop detected regions into image files with
  `data_snapshot.misc.extract_snapshots`.

## Verification

Shared adapter transformations are covered by the core offline suite. Reference
inference tests are intentionally skipped because they run full, deterministic
model inference. Manually unskip the relevant test after changing an adapter or
its inference pipeline:

```shell
uv sync --locked --extra test
uv run --no-sync pytest tests/test_adapter_utils.py tests/test_adapters.py
```

Passing these tests does not verify model-weight downloads, GPU compatibility,
or full inference on the local machine. Run a small PDF directory through the
selected adapter for that environment-specific check.
