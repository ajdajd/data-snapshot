# Data Snapshot Extraction Benchmarking

Tools for evaluating data-snapshot detections against human-annotated ground
truth. Inputs and outputs use the [Unified Evaluation Schema
v1.3](../../../docs/data-snapshot-eval-v1.3.schema.json).

The full metric definitions and matching rules are specified in the
[evaluation specification](../../../docs/evaluation_spec.md).

## Inputs

1. Convert a Label Studio export into ground truth with the [annotation
   adapter](../annotation/README.md).
2. Generate model predictions with a [Data Snapshot Extraction
   adapter](../inference/README.md).
3. Confirm that both files use the same document, page, label, and coordinate
   conventions.

## Evaluate a model

The core evaluation requires no model dependency:

```shell
uv sync --locked
uv run python -m data_snapshot.evaluation.evaluate_model \
    --gt_json_path=data/evaluation_input/ground_truth.json \
    --pred_json_path=data/evaluation_input/preds.json \
    --output_report_path=data/evaluation_output/report.json
```

The report includes detection precision and recall together with spatial
metrics based on intersection over union, coverage, and purity.

## Prepare prediction files

Merge compatible batch files:

```shell
uv run python -m data_snapshot.evaluation.merge_batch_preds \
    --input_dir=data/batch_runs/ \
    --output_json=data/evaluation_input/combined.json
```

Remove predictions below the configured normalized-area threshold:

```shell
uv run python -m data_snapshot.evaluation.filter_small_preds \
    --input_json=data/evaluation_input/preds.json \
    --output_json=data/evaluation_input/preds_filtered.json
```

## Render comparisons

Visualization requires OpenCV and NumPy:

```shell
uv sync --locked --extra viz
uv run --extra viz python -m data_snapshot.evaluation.visualize_pages \
    --gt_json_path=data/evaluation_input/ground_truth.json \
    --pred_json_path=data/evaluation_input/preds.json \
    --input_pdf_dir=pdf_input/ \
    --output_dir=data/visualize_pages/
```

## Related dataset utilities

Crop annotated regions from their source PDFs:

```shell
uv run python -m data_snapshot.misc.extract_snapshots \
    --input_json_path=data/evaluation_input/ground_truth.json \
    --input_pdf_dir=pdf_input/ \
    --output_dir=data/snapshots/
```

Split a combined annotation file into one file per document:

```shell
uv run python -m data_snapshot.misc.annotations_to_hf_dataset \
    --input_json_path=data/evaluation_input/ground_truth.json \
    --output_dir=data/hf_annotations/
```

## Verification

```shell
uv run --extra test pytest \
    tests/test_evaluate_model.py \
    tests/test_adapter_utils.py
```

Generated reports, rendered pages, input PDFs, and model predictions normally
live in gitignored directories and are not supplied by a clean clone.
