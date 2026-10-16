# Data Snapshot Extraction Benchmarking

Use these tools to evaluate table and figure detections against human-annotated
ground truth. Inputs use the [Unified Evaluation Schema
v1.3](../../../docs/data-snapshot-eval-v1.3.schema.json). The
[evaluation specification](../../../docs/evaluation_spec.md) records the metric
definitions and matching methodology; the commands below describe the current
implementation.

## Starting point: `pred_json_path`

Model evaluation starts from `pred_json_path`: one prediction JSON file emitted
by an integrated model adapter. It is the handoff between model-specific
inference and model-independent evaluation. Evaluation does not load model
weights or require the model's dependency extra.

The prediction file must:

- conform to Unified Evaluation Schema v1.3;
- use `Figure` and `Table` labels;
- use normalized `[x1, y1, x2, y2]` bounding boxes;
- identify the same documents and pages as the ground-truth file; and
- contain all documents being evaluated, normally in one combined file.

Keep the ground-truth and prediction files inside the repository. The current
report records their paths relative to the repository root.

## Quick evaluation

Once `pred_json_path` is ready, metric calculation is one CLI call and requires
only the core package:

```shell
uv run --no-sync python -m data_snapshot.evaluation.evaluate_model \
    --gt_json_path=data/evaluation_input/ground_truth.json \
    --pred_json_path=data/evaluation_input/model_predictions.json \
    --output_report_path=data/evaluation_output/model_report.json
```

The command writes the full JSON report and prints paper-style Figure and Table
metric tables for IoU `0.5`. The report also contains results for IoU `0.75`.

The equivalent Python API is:

```python
from data_snapshot.evaluation.evaluate_model import evaluate

report = evaluate(
    gt_json_path="data/evaluation_input/ground_truth.json",
    pred_json_path="data/evaluation_input/model_predictions.json",
    output_path="data/evaluation_output/model_report.json",
)
```

## Step-by-step procedure

### 1. Select the ground truth

Use a ground-truth JSON created by the [Label Studio annotation
adapter](../annotation/README.md). Do not compare predictions from one PDF set
against ground truth from another.

For the paper-wide benchmark, the existing ground truth is:

```text
data/paper/evaluation_input/ground_truth_corpus_combined.json
```

### 2. Generate or locate the predictions

Run the integrated adapter over the same PDFs. For example, DocLayout-YOLO
writes its evaluation-ready output directly to `pred_json_path`:

```shell
uv run --no-sync python -m data_snapshot.inference.doclayoutyolo \
    --input_pdf_dir=pdf_input/ \
    --output_json_path=data/evaluation_input/doclayoutyolo.json
```

If inference was split into batches, place only compatible files from one model
in a directory and merge them:

```shell
uv run --no-sync python -m data_snapshot.evaluation.merge_batch_preds \
    --input_dir=data/batch_runs/doclayoutyolo/ \
    --output_json=data/evaluation_input/doclayoutyolo_combined.json
```

The merge command requires the same label map, model name, and coordinate
system in every input file. It keeps the first occurrence of a duplicate page.

### 3. Apply the small-prediction policy

The paper benchmark removes predictions with normalized bounding-box area below
`0.008`. Historical filenames mark this configuration with `_wo_small`. This
filter removes small logos and other detections unlikely to be data snapshots.

All currently supported adapters apply the `0.008` filter by default, so their
normal output can be passed directly to evaluation. The filename suffix is only
a naming convention; the evaluator does not interpret `_wo_small` or apply the
filter again.

If a prediction file was generated with
`--no-filter-small-predictions`, by an older adapter, or outside this repository,
filter it explicitly:

```shell
uv run --no-sync python -m data_snapshot.evaluation.filter_small_preds \
    --input_json=data/evaluation_input/model_predictions.json \
    --output_json=data/evaluation_input/model_predictions_wo_small.json \
    --min_area=0.008
```

`0.008` is the paper-reproduction setting and the command default. It can be
adjusted with `--min_area`, but a different value is a different benchmark
configuration and should be recorded with the results.

### 4. Run the evaluator

```shell
uv run --no-sync python -m data_snapshot.evaluation.evaluate_model \
    --gt_json_path=data/evaluation_input/ground_truth.json \
    --pred_json_path=data/evaluation_input/model_predictions_wo_small.json \
    --output_report_path=data/evaluation_output/model_report.json \
    --thr 0.5 0.75 \
    --labels Figure Table
```

The last two options show the defaults and may be omitted. The paper tables use
the `0.5` results.

Check the command output for document mismatches. A non-empty
`documents_mismatch` section means the two files do not cover the same corpus
and the resulting metrics should not be treated as the full benchmark.

### 5. Read the report

For each label, the paper columns map to report fields as follows:

| Paper metric | JSON field |
|---|---|
| Precision | `metrics["0.5"]["per_class"][label]["precision"]` |
| Recall | `metrics["0.5"]["per_class"][label]["recall"]` |
| IoU | `metrics["0.5"]["per_class"][label]["mean_iou"]` |
| Area precision | `metrics["0.5"]["per_class"][label]["mean_area_precision"]` |
| Area recall | `metrics["0.5"]["per_class"][label]["mean_area_recall"]` |

The evaluator performs greedy one-to-one matching independently for each page
and label. A pair is a true positive when its IoU meets the selected threshold.
Spatial metrics are averaged over matched pairs only.

## Reproduce the paper metrics

The repository contains the filtered corpus prediction files and their reports:

| Model | Prediction file | Existing report |
|---|---|---|
| TF-ID Large | `data/paper/evaluation_input/tfid-large_corpus_combined_wo_small.json` | `data/paper/evaluation_output/report_tfid-large_corpus_combined_wo_small.json` |
| DocLayout-YOLO | `data/paper/evaluation_input/doclayoutyolo_corpus_combined_wo_small.json` | `data/paper/evaluation_output/report_doclayoutyolo_corpus_combined_wo_small.json` |
| YOLO11 medium | `data/paper/evaluation_input/yolo11_corpus_combined_wo_small.json` | `data/paper/evaluation_output/report_yolo11_corpus_combined_wo_small.json` |
| YOLO26 medium | `data/paper/evaluation_input/yolo26_corpus_combined_wo_small.json` | `data/paper/evaluation_output/report_yolo26_corpus_combined_wo_small.json` |

Do not overwrite the existing reports; they are historical paper artifacts. To
recalculate DocLayout-YOLO into a new report:

```shell
uv run --no-sync python -m data_snapshot.evaluation.evaluate_model \
    --gt_json_path=data/paper/evaluation_input/ground_truth_corpus_combined.json \
    --pred_json_path=data/paper/evaluation_input/doclayoutyolo_corpus_combined_wo_small.json \
    --output_report_path=data/evaluation_output/reproduced_doclayoutyolo_report.json
```

The printed values, rounded to three decimal places, recreate the corresponding
DocLayout-YOLO column in the paper table.

## Evaluate a future integrated model

No evaluator change is needed for a new model once its adapter produces a
Unified Evaluation Schema v1.3 prediction file. The repeatable procedure is:

1. Run the adapter on the benchmark PDFs.
2. Merge batches if necessary.
3. Confirm whether the `0.008` filter was applied exactly once.
4. Use the resulting file as `pred_json_path` in the evaluator.
5. Save the report under a new model-specific filename.
6. Record the adapter configuration, model weights, confidence threshold,
   filtering threshold, and evaluated corpus with the result.

## Render comparisons

Visualization requires the `viz` extra:

```shell
uv sync --locked --extra dev --extra doclayout_yolo --extra viz
uv run --no-sync python -m data_snapshot.evaluation.visualize_pages \
    --gt_json_path=data/evaluation_input/ground_truth.json \
    --pred_json_path=data/evaluation_input/model_predictions.json \
    --input_pdf_dir=pdf_input/ \
    --output_dir=data/visualize_pages/
```

## Verification

```shell
uv run --no-sync pytest \
    tests/test_evaluate_model.py \
    tests/test_adapter_utils.py
```

Generated reports, rendered pages, input PDFs, and new model predictions
normally live in gitignored directories and are not supplied by a clean clone.
