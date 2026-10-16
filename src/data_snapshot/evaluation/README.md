# Data Snapshot Extraction Benchmarking

This package evaluates Figure and Table detections against human-annotated
ground truth. Both inputs use the [Unified Evaluation Schema
v1.3](../../../docs/data-snapshot-eval-v1.3.schema.json). This README documents
the current executable workflow and report fields.

## Evaluation contract

Evaluation starts from two JSON files:

- `gt_json_path`: human-annotated ground truth;
- `pred_json_path`: predictions emitted by an integrated model adapter.

`pred_json_path` is the boundary between model-specific inference and the
model-independent evaluator. It must:

- conform to Unified Evaluation Schema v1.3;
- use `Figure` and `Table` labels;
- use normalized `[x1, y1, x2, y2]` bounding boxes;
- identify the same documents as the ground truth; and
- contain all documents being evaluated.

Predictions may contain pages without annotated objects. Keep generated ground
truth, predictions, and reports inside the repository because report metadata
currently stores their paths relative to the repository root.

The paper benchmark removes predictions whose normalized bounding-box area is
below `0.008`. This removes small logos and other detections unlikely to be
data snapshots. Integrated adapters apply this filter by default; the evaluator
does not filter again. Historical filenames use `_wo_small` to identify this
configuration.

## Reproduce the paper benchmark from source PDFs

Use this workflow to run inference again from the dataset PDFs. For recalculating
metrics from the stored paper predictions without inference, see
[Historical paper artifacts](#historical-paper-artifacts).

### 1. Install dependencies

Create the locked DocLayout-YOLO paper-reproduction environment:

```shell
uv sync --locked --extra dev --extra doclayout_yolo --extra pdf2image
```

The `pdf2image` backend also requires Poppler. On Ubuntu or WSL:

```shell
sudo apt install poppler-utils
```

The paper predictions used `pdf2image`; current adapters default to PyMuPDF,
which can shift bounding boxes slightly. For another model, replace
`doclayout_yolo` with that model's dependency extra while retaining
`pdf2image` for paper-comparable rendering.

### 2. Prepare the dataset

Download the [Data Snapshot dataset](https://huggingface.co/datasets/ai4data/data-snapshot)
with this layout:

```text
data-snapshot/
├── documents/<source>/*.pdf
└── annotations/<source>/*.json
```

### 3. Configure the run

The checked-in DocLayout-YOLO paper configuration is
[`doclayoutyolo_paper_benchmark.json`](doclayoutyolo_paper_benchmark.json):

```json
{
  "model": "doclayoutyolo",
  "dataset_root": "/home/ajd/hf_datasets/data-snapshot",
  "output_root": "data/evaluation_runs",
  "sources": ["unhcr", "prwp", "refugee"],
  "device": "cuda:0",
  "adapter_config": {
    "pdf_backend": "pdf2image"
  }
}
```

Configuration fields:

| Field | Purpose |
|---|---|
| `model` | Integrated adapter: `doclayoutyolo`, `tfid`, `yolo11`, or `yolo26` |
| `dataset_root` | Directory containing `documents/` and `annotations/` |
| `output_root` | Directory for generated evaluation files |
| `sources` | Allowed source runs and exact full-corpus membership |
| `device` | Model device, such as `cpu` or `cuda:0` |
| `adapter_config` | Optional keyword overrides passed to the adapter config |

Relative dataset and output paths are resolved from the repository root.

### 4. Run each source

Run sources independently so completed inference is preserved if a later source
fails:

```shell
uv run --no-sync python scripts/evaluate_benchmark.py \
    --config src/data_snapshot/evaluation/doclayoutyolo_paper_benchmark.json \
    --source unhcr
uv run --no-sync python scripts/evaluate_benchmark.py \
    --config src/data_snapshot/evaluation/doclayoutyolo_paper_benchmark.json \
    --source prwp
uv run --no-sync python scripts/evaluate_benchmark.py \
    --config src/data_snapshot/evaluation/doclayoutyolo_paper_benchmark.json \
    --source refugee
```

Each run validates PDF and annotation coverage, combines the source ground
truth, runs the selected adapter, and evaluates both Figure and Table objects.

Existing outputs are not replaced by default. Use `--overwrite` only when the
generated outputs should be replaced. If inference completed but a later step
failed, use `--reuse-predictions --overwrite` to rebuild the ground truth and
report without rerunning the model.

### 5. Combine the corpus

After every configured source completes, combine and evaluate the corpus:

```shell
uv run --no-sync python scripts/evaluate_benchmark.py \
    --config src/data_snapshot/evaluation/doclayoutyolo_paper_benchmark.json \
    --corpus
```

The corpus run includes exactly the configured `sources` and writes the combined
ground truth, predictions, and report.

Generated files are organized by model and source:

```text
data/evaluation_runs/<model>/
├── ground_truth/
│   ├── sources/<source>.json
│   └── corpus.json
├── predictions/
│   ├── sources/<source>.json
│   └── corpus.json
└── reports/
    ├── sources/<source>.json
    └── corpus.json
```

## Evaluate an existing prediction file

When `pred_json_path` already exists, run the evaluator directly without loading
model weights:

```shell
uv run --no-sync python -m data_snapshot.evaluation.evaluate_model \
    --gt_json_path=data/evaluation_input/ground_truth.json \
    --pred_json_path=data/evaluation_input/model_predictions.json \
    --output_report_path=data/evaluation_output/model_report.json
```

The equivalent Python API is:

```python
from data_snapshot.evaluation.evaluate_model import evaluate

report = evaluate(
    gt_json_path="data/evaluation_input/ground_truth.json",
    pred_json_path="data/evaluation_input/model_predictions.json",
    output_path="data/evaluation_output/model_report.json",
)
```

The evaluator reports IoU thresholds `0.5` and `0.75`; the paper tables use
`0.5`. A non-empty `documents_mismatch` section means the files do not cover the
same corpus and should not be treated as a complete benchmark result.

If predictions came from outside the integrated adapters or were created with
small-prediction filtering disabled, apply the paper filter once before
evaluation:

```shell
uv run --no-sync python -m data_snapshot.evaluation.filter_small_preds \
    --input_json=data/evaluation_input/model_predictions.json \
    --output_json=data/evaluation_input/model_predictions_wo_small.json \
    --min_area=0.008
```

A different `min_area` value defines a different benchmark configuration and
should be recorded with the result.

## Read the report

For each `Figure` or `Table` label, the paper columns map to these report fields:

| Paper metric | JSON field |
|---|---|
| Precision | `metrics["0.5"]["per_class"][label]["precision"]` |
| Recall | `metrics["0.5"]["per_class"][label]["recall"]` |
| IoU | `metrics["0.5"]["per_class"][label]["mean_iou"]` |
| Area precision | `metrics["0.5"]["per_class"][label]["mean_area_precision"]` |
| Area recall | `metrics["0.5"]["per_class"][label]["mean_area_recall"]` |

Matching is greedy and one-to-one within each page and label. A pair is a true
positive when its IoU meets the selected threshold. Spatial metrics are averaged
over matched pairs only.

## Historical paper artifacts

The repository keeps the filtered corpus predictions and reports used for the
paper. Treat these as read-only historical artifacts:

| Model | Prediction file | Existing report |
|---|---|---|
| TF-ID Large | `data/paper/evaluation_input/tfid-large_corpus_combined_wo_small.json` | `data/paper/evaluation_output/report_tfid-large_corpus_combined_wo_small.json` |
| DocLayout-YOLO | `data/paper/evaluation_input/doclayoutyolo_corpus_combined_wo_small.json` | `data/paper/evaluation_output/report_doclayoutyolo_corpus_combined_wo_small.json` |
| YOLO11 medium | `data/paper/evaluation_input/yolo11_corpus_combined_wo_small.json` | `data/paper/evaluation_output/report_yolo11_corpus_combined_wo_small.json` |
| YOLO26 medium | `data/paper/evaluation_input/yolo26_corpus_combined_wo_small.json` | `data/paper/evaluation_output/report_yolo26_corpus_combined_wo_small.json` |

The shared ground truth is
`data/paper/evaluation_input/ground_truth_corpus_combined.json`. To verify the
evaluator without rerunning inference, evaluate one of the stored prediction
files and write the new report outside `data/paper/`.

The repository ignores `data/` by default but explicitly includes JSON files
under `data/paper/evaluation_input/` and `data/paper/evaluation_output/`. This
keeps historical paper evidence versioned without admitting other generated
data.

## Extend the benchmark

To evaluate another supported model, copy the JSON configuration, change
`model`, and install that model's dependency extra. No evaluator change is
required because every integrated adapter writes Unified Evaluation Schema v1.3.

To add a data source, create matching `documents/<source>/` and
`annotations/<source>/` directories, add the source name to `sources`, run that
source, and then rebuild the corpus.

For a newly integrated model, record the model weights, confidence threshold,
PDF renderer, filtering threshold, adapter configuration, and evaluated sources
with the resulting report.

## Render comparisons

Visualization requires the `viz` extra:

```shell
uv run --no-sync python -m data_snapshot.evaluation.visualize_pages \
    --gt_json_path=data/evaluation_input/ground_truth.json \
    --pred_json_path=data/evaluation_input/model_predictions.json \
    --input_pdf_dir=pdf_input/ \
    --output_dir=data/visualize_pages/
```

## Verification

```shell
uv run --no-sync pytest \
    tests/test_benchmark.py \
    tests/test_benchmark_cli.py \
    tests/test_evaluate_model.py \
    tests/test_adapter_utils.py
```

Generated reports, rendered pages, input PDFs, and new model predictions live
in gitignored directories and are not supplied by a clean clone.
