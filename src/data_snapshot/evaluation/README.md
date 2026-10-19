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

## Run layout benchmarks from source PDFs

Use the full, smoke-test, or half-sample runner below. The original adapters
use PyMuPDF; Docling uses its native PDF pipeline. These runs remain separate
from historical paper outputs.

### 1. Install dependencies

Install the locked development, renderer, and selected model dependencies. For
example, for `doclayoutyolo`:

```shell
uv sync --locked --extra dev --extra doclayoutyolo
```

Repeat the sync with the selected model extra before switching adapters, then
use `uv run --no-sync` for execution. Include every extra needed for the run in
that sync. `tfid` conflicts with both `unlimitedocr` and `docling_heron`, so
`--all-extras` is unsupported. Unlimited-OCR uses a CUDA GPU with BF16 support; see
[its setup and prediction contract](../inference/README.md#unlimited-ocr).

PyMuPDF is a core dependency and requires no Poppler installation.

The model keywords and dependency extras are:

| Model | Keyword and extra | Paper configuration |
|---|---|---|
| TF-ID-Large | `tfid` | [`tfid_paper_benchmark.json`](configs/tfid_paper_benchmark.json) |
| DocLayout-YOLO | `doclayoutyolo` | [`doclayoutyolo_paper_benchmark.json`](configs/doclayoutyolo_paper_benchmark.json) |
| YOLOv11 medium | `yolo11` | [`yolo11_paper_benchmark.json`](configs/yolo11_paper_benchmark.json) |
| YOLOv26 medium | `yolo26` | [`yolo26_paper_benchmark.json`](configs/yolo26_paper_benchmark.json) |
| Unlimited-OCR | `unlimitedocr` | Not part of the paper; no paper configuration |
| Docling Heron | `docling_heron` | [`docling_heron_benchmark.json`](configs/docling_heron_benchmark.json); native PDF pipeline |
| Docling Egret Medium | `docling_egret_medium` | [`docling_egret_medium_benchmark.json`](configs/docling_egret_medium_benchmark.json); shared Docling pipeline and `docling_heron` extra |

Current benchmark configurations use PyMuPDF (`pdf_backend: "pymupdf"`).
Historical paper runs used `pdf2image` with Poppler; switching renderers can
change predictions. Use the same renderer and document selection for every
model in a comparison. Configuration filenames retain `paper_benchmark` for
compatibility, but their defaults now describe new PyMuPDF runs.

### 2. Prepare the dataset

Download the [Data Snapshot dataset](https://huggingface.co/datasets/ai4data/data-snapshot)
with this layout:

```text
data-snapshot/
├── documents/<source>/*.pdf
└── annotations/<source>/*.json
```

### 3. Configure the run

The checked-in `doclayoutyolo` paper configuration is used here as the worked
example:
[`configs/doclayoutyolo_paper_benchmark.json`](configs/doclayoutyolo_paper_benchmark.json):

```json
{
  "model": "doclayoutyolo",
  "dataset_root": "data/hf_datasets/data-snapshot",
  "output_root": "data/evaluation_runs/pymupdf",
  "sources": ["unhcr", "prwp", "refugee"],
  "device": "cuda:0",
  "adapter_config": {
    "pdf_backend": "pymupdf"
  }
}
```

Configuration fields:

| Field | Purpose |
|---|---|
| `model` | Integrated adapter: `doclayoutyolo`, `tfid`, `yolo11`, `yolo26`, `unlimitedocr`, `docling_heron`, or `docling_egret_medium` |
| `dataset_root` | Directory containing `documents/` and `annotations/` |
| `output_root` | Directory for generated evaluation files |
| `sources` | Allowed source runs and exact full-corpus membership |
| `device` | Model device, such as `cpu` or `cuda:0` |
| `adapter_config` | Optional keyword overrides passed to the adapter config |

Relative dataset and output paths are resolved from the repository root.

Paper configurations for the four original benchmark models use the
`configs/<model>_paper_benchmark.json` naming pattern. Select the file matching
the keyword in the table above, then adjust `dataset_root` and
`device` for the local environment. Keep the same `pdf_backend` for all models
in a comparison. Other `adapter_config` fields are model-specific and override
that adapter's defaults.

### 4. Choose a runner

All three runners accept `--config` and `--overwrite`, write source reports,
and recompute overall metrics from pooled ground truth and predictions.
Without `--overwrite`, existing outputs are protected.

| Selection | PDFs | Runner | Output beneath `data/evaluation_runs/pymupdf/` |
|---|---:|---|---|
| Full dataset | 476 | `scripts/evaluate_benchmark.py` | `<model>/` |
| Smoke test | 9 (3 per corpus) | `scripts/evaluate_benchmark_sample.py` | `paper_benchmark_sample/<model>/` |
| Fixed half sample | 238 (169 UNHCR, 50 PRWP, 19 refugee) | `scripts/evaluate_benchmark_half.py` | `paper_benchmark_half/<model>/` |

For example, the full runner executes all configured sources and then the
combined corpus in one command:

```shell
uv run --no-sync python scripts/evaluate_benchmark.py \
    --config src/data_snapshot/evaluation/configs/doclayoutyolo_paper_benchmark.json
```

For the smaller selections, change the script name to the smoke or half runner.

### Run or resume individual sources

Run sources independently so completed inference is preserved if a later source
fails. These commands continue the `doclayoutyolo` example; for another model,
use its model-specific configuration from step 3:

```shell
uv run --no-sync python scripts/evaluate_benchmark.py \
    --config src/data_snapshot/evaluation/configs/doclayoutyolo_paper_benchmark.json \
    --source unhcr
uv run --no-sync python scripts/evaluate_benchmark.py \
    --config src/data_snapshot/evaluation/configs/doclayoutyolo_paper_benchmark.json \
    --source prwp
uv run --no-sync python scripts/evaluate_benchmark.py \
    --config src/data_snapshot/evaluation/configs/doclayoutyolo_paper_benchmark.json \
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
    --config src/data_snapshot/evaluation/configs/doclayoutyolo_paper_benchmark.json \
    --corpus
```

The corpus run includes exactly the configured `sources` and writes the combined
ground truth, predictions, and report.

Generated files are organized by model and source:

```text
data/evaluation_runs/pymupdf/<model>/
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

## Smoke-test the benchmark pipeline

Before committing to a full-corpus run, use the fixed nine-document sample to
confirm that the selected model loads and the inference-to-evaluation pipeline
completes:

```shell
uv run --no-sync python scripts/evaluate_benchmark_sample.py \
    --config src/data_snapshot/evaluation/configs/doclayoutyolo_paper_benchmark.json
```

Replace `doclayoutyolo` in the configuration filename with `tfid`, `yolo11`, or
`yolo26`. The runner temporarily links the selected inputs into their original
source directories without copying or modifying the dataset. Results include
`reports/sources/{unhcr,prwp,refugee}.json` and `reports/corpus.json` under
`data/evaluation_runs/pymupdf/paper_benchmark_sample/<model>/`.
Use `--overwrite` only to replace a completed run.

The checked-in
[`paper_benchmark_sample.json`](configs/paper_benchmark_sample.json) selects the
three shortest documents containing both labels from each corpus: 9 PDFs, 170
pages, 17 Figures, and 43 Tables in total.

A successful smoke test processes all nine documents, reports no document
mismatch, and produces Figure and Table metrics. The values are diagnostic only:
this small sample is intended to catch model-loading, label-mapping, rendering,
filtering, and evaluator failures rather than reproduce the paper results.

## Half-size directional benchmark

[`paper_benchmark_half.json`](configs/paper_benchmark_half.json) fixes half the
PDFs within each corpus: 169 UNHCR, 50 PRWP, and 19 refugee PDFs, totalling
238 PDFs and 3,753 pages. It uses seed `42`, sorted filenames, and one random
number generator consumed in that source order. The manifest records each
selected PDF and annotation; use this exact selection for every compared model.

```shell
uv run --no-sync python scripts/evaluate_benchmark_half.py \
    --config src/data_snapshot/evaluation/configs/doclayoutyolo_paper_benchmark.json
```

Replace the model name for each run. Per-corpus reports and the overall report
are written beneath `data/evaluation_runs/pymupdf/paper_benchmark_half/<model>/`.
These scores support directional comparisons; resolve close rankings with the
full dataset.

## Rendering diagnostics

### Native Docling half-sample comparison

After the [explicit asset preparation](../inference/README.md#native-docling-heron),
run the same fixed half-sample through Docling:

```shell
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --no-sync \
    python scripts/evaluate_benchmark_half.py \
    --config src/data_snapshot/evaluation/configs/docling_heron_benchmark.json
uv run --no-sync python scripts/summarize_benchmark.py \
    --output-root data/evaluation_runs/pymupdf/paper_benchmark_half \
    --docling-root data/evaluation_runs/docling/paper_benchmark_half \
    --output data/evaluation_runs/docling/paper_benchmark_half/comparison.md
```

The adapter evaluates native picture/table layout clusters with the same
`0.008` area filter. Caption/footnote links remain in separate native JSON;
they do not expand evaluation bounds or native crops. The native Docling
backend, OCR, preprocessing, and layout postprocessing differ from the saved
PyMuPDF baseline, so interpret scores as complete-pipeline comparisons.
No custom filtering, caption association, or box-expansion rules are added.

Source and pooled reports are isolated under
`data/evaluation_runs/docling/paper_benchmark_half/docling_heron/`.
The checked-in configuration sets `adapter_config.document_concurrency` to 2
for native two-PDF threading, with layout batch size 1. Set it to 1 for serial
execution. This uses Docling's pairwise batching; it does not guarantee a speed
gain, and the concurrent memory check covered only the smaller diagnostic run.
`predictions/sources/<source>.native/` contains one native document JSON per
PDF. The comparison command reads the saved baseline without replacing it.
The checked-in config expects assets under `models/docling`; use a local
config copy with another `artifacts_path` when reusing prefetched assets.

For Egret Medium, use `docling_egret_medium_benchmark.json`. It retains Heron's
CUDA FP32, layout batch size 1, document concurrency 2, CPU English RapidOCR,
and disabled table structure/enrichment. Only the pinned layout checkpoint and
its architecture change. Outputs use the `docling_egret_medium/` directory.
The shared summarizer accepts `--egret-root <root>/paper_benchmark_half` alongside
`--docling-root` to add Egret and Heron from separate completed runs. Only compare
identical document selections and account for runtime-version differences.
See the [validation record](../../../docs/docling_egret_medium_validation.md)
for the current local asset override and ready-to-run half-benchmark command.

Docling logs a native `document_finished` event with page count, concurrency,
and cumulative `elapsed_run_seconds` for every completed PDF. Concurrent
ordered results do not provide individual document runtimes. Its backend warnings appear in the process
output; the detailed PyMuPDF page-render events described below apply only
to adapters using the shared PyMuPDF renderer. Capture native process output
alongside the source JSONL log when preserving Docling benchmark evidence.

All three benchmark runners automatically create a fresh JSON Lines log for
each source inference attempt under `<output_root>/<model>/logs/`. The terminal
prints the exact filename, which includes the source and a UTC timestamp. Logs
are flushed as events occur and retained even when inference fails. Restarting
with `--overwrite` replaces prediction/report outputs but preserves earlier logs.

For PyMuPDF, each record identifies the original resolved PDF path, document ID,
renderer, DPI, and event. Document-open records include PyMuPDF/MuPDF versions
and expected page count. Every successfully rendered page records its zero-based
`page_index`, one-based `page_number`, dimensions, and any MuPDF messages.
Document-level messages have a null page number. Document-finished records give
expected and rendered page counts. Rendering failures record the operation,
current page where known, exception, and traceback; failures are re-raised and
pages are not silently skipped. Source-level inference failures and Ctrl-C are
also logged. An externally killed process may leave no final completion event.

Inspect warning/error records after a half-sample run with:

```shell
rg '"status": "(warning|error)"' \
    data/evaluation_runs/pymupdf/paper_benchmark_half/*/logs/*.jsonl
```

This identifies PDFs/pages for later rendering inspection without repeating
model inference. Warnings alone do not prove images are defective; successful
page counts also do not establish visual correctness. The renderer still uses
the same settings and displays native MuPDF diagnostics. Logging does not repair
PDFs or change which pages are processed.

## Markdown comparison report

After running the selected models, render Figure overall, Table overall,
Figure by corpus, and Table by corpus tables from their JSON reports:

```shell
uv run --no-sync python scripts/summarize_benchmark.py \
    --output-root data/evaluation_runs/pymupdf/paper_benchmark_half
```

The default output is `<output-root>/report.md`. Use the matching smoke or full
output root when summarizing those selections. Missing model/corpus reports
leave blank cells, including TF-ID when skipped. An undefined metric is shown
as `N/A`; document mismatches reject the report. Use `--overwrite` only when
intentionally refreshing an existing Markdown file.

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

## Expected paper results

The tables below report the published full-corpus metrics at IoU `0.5`.
Use them as a reference when comparing fresh inference runs.

### Figures

| Category | Metric | TF-ID-Large | DocLayout-YOLO | YOLOv11 medium | YOLOv26 medium |
| --- | --- | ---: | ---: | ---: | ---: |
| Detection | Precision | **0.628** | 0.547 | 0.378 | 0.388 |
|  | Recall | 0.488 | **0.802** | 0.761 | 0.721 |
| Spatial accuracy | IoU | **0.877** | 0.820 | 0.817 | 0.817 |
|  | Area precision | 0.935 | **0.996** | 0.990 | 0.990 |
|  | Area recall | **0.938** | 0.824 | 0.826 | 0.826 |

### Tables

| Category | Metric | TF-ID-Large | DocLayout-YOLO | YOLOv11 medium | YOLOv26 medium |
| --- | --- | ---: | ---: | ---: | ---: |
| Detection | Precision | **0.562** | 0.468 | 0.487 | 0.460 |
|  | Recall | 0.861 | **0.893** | 0.862 | 0.891 |
| Spatial accuracy | IoU | **0.919** | 0.834 | 0.817 | 0.824 |
|  | Area precision | 0.972 | 0.993 | **0.994** | 0.994 |
|  | Area recall | **0.946** | 0.841 | 0.822 | 0.829 |

See [*Benchmarking Open-Source Layout Detection Models for Data Snapshot
Extraction from Institutional Documents*](https://arxiv.org/abs/2606.06242)
for the evaluation protocol, per-corpus results, and limitations.

Compare the appropriate column manually with the generated
`reports/corpus.json`. Changes in PDF rendering, installed fonts, or numerical
libraries can introduce discrepancies because they alter page images or model
predictions. In particular, installing fonts can change how non-embedded PDF
fonts are substituted, even with the same renderer and Python dependencies.
Model weights, inference settings, filtering policy, and input corpus must also
match for a comparable run.

A targeted check of one affected page from each of 10 UNHCR PDFs confirmed this
font effect across DocLayout-YOLO, YOLO11, and YOLO26. Restoring the older font
set reproduced the historical boxes and scores exactly for YOLO11 and YOLO26,
and within `1e-5` for DocLayout-YOLO. This check did not cover full documents or
the full corpus, so exact agreement with every published aggregate remains
unverified.

## Extend the benchmark

To evaluate another supported model, follow the same source and corpus workflow
with its configuration file. No evaluator change is required because every
integrated adapter writes Unified Evaluation Schema v1.3.

Unlimited-OCR can use the same runner with `model="unlimitedocr"` and
`device="cuda:0"`. It has no checked-in paper configuration. To run it through
the Python API after installing its extra:

```shell
uv sync --locked --extra unlimitedocr
uv run --no-sync python -c 'from data_snapshot.evaluation.benchmark import evaluate_source; evaluate_source(model="unlimitedocr", source="unhcr", dataset_root="data/hf_datasets/data-snapshot", device="cuda:0")'
```

This downloads weights if needed, runs inference, and writes evaluation files.
Unlimited-OCR scores are fixed at `1.0` because the model provides no region
confidence. Captions and surrounding text are discarded; boxes are not expanded.

To add a data source, create matching `documents/<source>/` and
`annotations/<source>/` directories, add the source name to `sources`, run that
source, and then rebuild the corpus.

For a newly integrated model, record the model weights, confidence threshold,
PDF renderer, filtering threshold, adapter configuration, and evaluated sources
with the resulting report.

## Render comparisons

Visualization requires the `viz` extra:

```shell
uv sync --locked --extra viz
uv run --no-sync python -m data_snapshot.evaluation.visualize_pages \
    --gt_json_path=data/evaluation_input/ground_truth.json \
    --pred_json_path=data/evaluation_input/model_predictions.json \
    --input_pdf_dir=pdf_input/ \
    --output_dir=data/visualize_pages/
```

## Verification

```shell
uv sync --locked --extra test
uv run --no-sync pytest \
    tests/test_benchmark.py \
    tests/test_benchmark_cli.py \
    tests/test_evaluate_model.py \
    tests/test_adapter_utils.py \
    tests/test_unlimitedocr.py
```

Generated reports, rendered pages, input PDFs, and new model predictions live
in gitignored directories and are not supplied by a clean clone.
