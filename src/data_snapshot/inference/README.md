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
| Unlimited-OCR | `unlimitedocr` | `data_snapshot.inference.unlimitedocr` |
| Docling Heron (native pipeline) | `docling_heron` | `data_snapshot.inference.docling_heron` |
| Docling Egret Medium (native pipeline) | `docling_heron` (shared runtime) | `data_snapshot.inference.docling_heron` |

Install only the adapter required for a run:

```shell
uv sync --locked --extra yolo26
```

These extras are large and may install PyTorch, CUDA libraries, or other model
runtime dependencies. Model weights are downloaded from Hugging Face when a
configured local weight file is unavailable and are stored outside version
control.

Run `uv sync --locked --extra <model>` before switching adapters, and use
`uv run --no-sync` afterward. Include `--extra dev`, `--extra test`, or other
extras in the same sync when that workflow needs them. `tfid` conflicts with
both `unlimitedocr` and `docling_heron`; `uv sync --all-extras` is unsupported.

## Run one adapter

All adapters accept an input PDF directory and write one prediction JSON file.
For example:

```shell
uv sync --locked --extra yolo26
uv run --no-sync python -m data_snapshot.inference.yolo26 \
    --input_pdf_dir=pdf_input/ \
    --output_json_path=data/evaluation_input/yolo26.json
```

Replace `yolo26` in both places with the selected adapter and dependency extra.
The output contains documents, page-level detections, labels, normalized
bounding boxes, and run metadata.

### Unlimited-OCR

Use the native Transformers implementation on a CUDA GPU with BF16 support:

```shell
uv sync --locked --extra unlimitedocr
uv run --no-sync python -m data_snapshot.inference.unlimitedocr \
    --input_pdf_dir=pdf_input/ \
    --output_json_path=data/evaluation_input/unlimitedocr.json \
    --device=cuda:0
```

The adapter loads `baidu/Unlimited-OCR` at revision
`8249d20b2822a7d8a4c22c8d8c9069b5ac36bda3` using Transformers 5.20.1,
safetensors, and native code (`trust_remote_code=False`). It processes PIL page
images one at a time with `document parsing.`, dynamic 640-pixel tiles
(Gundam mode), deterministic decoding, and a total sequence limit of 32768.
`--max_length` changes that limit; reaching it without an end token raises an
error before writing predictions. The model's context capacity still limits
usable sequence lengths.

The [official Transformers guide](https://github.com/huggingface/transformers/blob/v5.20.1/docs/source/en/model_doc/unlimited_ocr.md)
documents native loading, image inputs, and `return_detections=True`.
The [processor implementation](https://github.com/huggingface/transformers/blob/v5.20.1/src/transformers/models/unlimited_ocr/processing_unlimited_ocr.py)
returns region labels and XYXY boxes on a 0–999 grid. The adapter divides by 999,
maps only `image` to `Figure` and `table` to `Table`, and discards captions and
other text regions. Caption association and box expansion are out of scope.
Scores are `1.0` because native detections contain no region confidence; these
values are placeholders, not calibrated probabilities. The shared area filter
of `0.008` is enabled by default; disable it with
`--no-filter_small_predictions` when needed.

Other options are `--run_id`, `--dpi`, `--pdf_backend`,
`--store_doc_path_as`, `--model_id`, and `--revision`. When selecting a different
checkpoint, supply its matching revision. For PDFs outside this repository,
use `--store_doc_path_as=absolute`; PDF filenames must be unique across the
input tree. Selecting `--pdf_backend=pdf2image` requires an additional
`--extra pdf2image` in the sync command and a system Poppler installation.

Python 3.10 remains the project requirement. The native Transformers release
supports Python 3.10; the older Baidu example's tested Python 3.12 environment
is not used by this adapter. Offline tests do not verify checkpoint loading or
CUDA compatibility; run the command above on a small input only when ready to
download weights and execute the model.

### Native Docling Heron

Install the model extra, then prefetch the pinned layout model and the English
OCR assets explicitly. The adapter itself requires local assets and does not
download missing models:

```shell
uv sync --locked --extra docling_heron
uv run --no-sync python - <<'PY'
from pathlib import Path
from huggingface_hub import snapshot_download
from docling.models.stages.ocr.rapid_ocr_model import RapidOcrModel
from data_snapshot.inference.docling_heron import MODEL_NAME, MODEL_REVISION

root = Path("models/docling")
snapshot_download(
    MODEL_NAME, revision=MODEL_REVISION,
    local_dir=root / MODEL_NAME.replace("/", "--"),
    allow_patterns=["*.json", "*.safetensors"],
)
RapidOcrModel.download_models(
    backend="onnxruntime", lang="en", local_dir=root / "RapidOcr",
)
PY
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 uv run --no-sync \
    python -m data_snapshot.inference.docling_heron \
    --input_pdf_dir=pdf_input/ \
    --output_json_path=data/evaluation_input/docling_heron.json \
    --device=cuda:0
```

Use `--artifacts_path` for another prefetched artifact root, and
`--document_concurrency=2` to process two PDFs concurrently through Docling's
native threads. The default is 1; layout batch size remains 1 in both modes.
The pipeline is initialized before worker threads start, and scoped native
settings are restored on completion or failure. Docling processes two-document
batches and waits for each batch; this is not multiprocessing or a continuously
replenished worker queue. Heron is fixed to
revision `8f39ad3c0b4c58e9c2d2c84a38465abf757272d8`; the adapter verifies its
weight SHA-256. The runtime uses Docling 2.140.0, Transformers 5.20.1, FP32,
batch size 1, and English RapidOCR on CPU through ONNX Runtime. Table structure
recognition, enrichment, and compilation are disabled. Docling's default engine
confidence threshold is 0.3; its native layout postprocessing and reading-order
rules remain enabled. No custom detection or association rules are added.

Egret Medium uses the same module, dependency extra, converter, and output
transformation. Select `--layout_model=egret_medium` in the module CLI, or use
`DoclingEgretMediumConfig` with `run_docling_heron_adapter_directory()` in Python.
The benchmark key is `docling_egret_medium`; it selects the Egret configuration
without requiring a checkpoint override. The default remains Heron.

Egret is pinned to revision `77ede7cc7bed96d853c58f319734803d6ea2ea5c`, with
weight SHA-256 verification. Prefetch it with the download snippet above after
substituting `EGRET_MODEL_NAME` and `EGRET_MODEL_REVISION` for the Heron constants;
the weight download is about 78 MB, and existing RapidOCR assets can be reused.
Both checkpoints supply identical 640-by-640 processor configurations. Egret's
D-FINE architecture replaces Heron's RT-DETRv2; all optional pipeline settings,
score threshold, FP32 precision, and shared filtering remain the same. This
compares checkpoint/model substitutions, not learned weights in one architecture.

Native `picture` and `table` layout clusters become `Figure` and `Table`, with
their native confidence and point coordinates normalized by page dimensions.
The shared `0.008` area filter remains enabled. The evaluation boxes are not
expanded to captions or footnotes. Native document JSON, including all native
caption/footnote references, text, and provenance, is stored separately in
`<prediction stem>.native/<PDF filename>.json`, including objects removed by
the benchmark area filter. No spatial matching is used to invent links.
This is Docling's assembled document, not a full dump of every detector proposal
or all-class confidence scores. The nine-PDF diagnostic trials also retain
`native-layout.json`, containing every postprocessed layout cluster's label,
bounding box, and confidence. Additional labels are excluded from evaluation.

Docling consumes PDFs through its own `docling-parse` backend rather than the
repository's PyMuPDF renderer. Its layout stage requests page images at scale
1 and the pinned processor resizes to 640 by 640. Comparisons with the saved
300 DPI PyMuPDF baseline therefore compare complete pipelines.

The benchmark retains native JSON without page-image payloads and does not
mass-export crops. With retained page images, Docling's native
`item.get_image(document)` crops the item provenance bounds; caption/footnote
references do not enlarge that crop. Text already inside the detected bounds
can still appear. The single-PDF smoke evidence includes example native crops.

On 2026-10-19 the pre-integration smoke processed both pages of
`08072015_northgovernorateprofile.pdf` on a GTX 1650 Ti (4 GiB), using the
settings above: 15.18 seconds including initialization/conversion, 2651 MiB
peak process RSS, 299 MiB peak PyTorch-allocated GPU memory and 348 MiB reserved.
Both page overlays were inspected; native output had five pictures and one
table, with no caption/footnote links on that PDF. GPU measurements cover only
PyTorch's allocator, and these measurements do not establish full-corpus limits.

The subsequent fixed nine-PDF sample completed all 170 pages with no conversion
failures, schema errors, or document mismatches. It retained 26 native caption
links and five footnote links, with all references resolving. These checks verify
preservation, not the correctness of Docling's associations. At evaluation IoU
0.5, Figure precision/recall were 0.326/0.824 and Table precision/recall were
0.465/0.930; these are sample diagnostics, not half-benchmark scores.

Serial execution remains available as the default; layout batch size stays 1.
The nine-PDF baseline took 652.26 seconds (3547 MiB peak process RSS, 348 MiB
PyTorch-reserved VRAM). Layout batch size 4 took 705.47 seconds and 952 MiB
reserved VRAM. It retained the same 129 detections and detection counts, with
maximum normalized coordinate drift of `2.69e-7` and score drift of `4.99e-5`;
native links and text were unchanged. Native two-document concurrency took
212.13 seconds for the first six PDFs / 61 pages, versus 206.27 seconds serial,
and was stopped at the user's request. All six native document JSON files were
identical. Neither experiment demonstrated a speed gain. Native two-document
concurrency was subsequently integrated at the user's request; the benchmark
configuration selects 2, while `document_concurrency=1` retains serial execution.
Timings are single trials, include initialization
and native JSON export, and exclude interpreter imports and evaluation; close
timing differences should not be treated as statistically established slowdowns.
The concurrency trial did not complete all nine PDFs, and peak RAM for the
broader interrupted attempt was 4751 MiB; full half-benchmark memory limits
remain unverified.

Existing prediction files and native evidence directories are protected. For
a failed attempt, use a fresh output location; the legacy batch runner is not
extended for this adapter.

## Batch extraction

The legacy batch runner executes the four original adapters over numbered input
directories such as `pdf_input/unhcr_batch1/`:

```shell
uv sync --locked --extra tfid --extra doclayoutyolo --extra yolo11 --extra yolo26
uv run --no-sync python -m data_snapshot.inference.batch_runner \
    --source unhcr --batch_start 1 --batch_end 5
```

Because the runner imports all four adapters at startup, it requires those four
extras. Unlimited-OCR is available through its own command and the integrated
benchmark, and is excluded from this legacy runner. Per-adapter commands are
preferable when only one model is needed. Batch outputs are written beneath
`data/batch_runs/` by default.

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
uv run --no-sync pytest tests/test_adapter_utils.py tests/test_unlimitedocr.py tests/test_adapters.py
```

The Unlimited-OCR tests use fake native model outputs and require no model
extra. To manually run an original reference-inference test, include its model
extra alongside `--extra test` in the sync command before unskipping that test.

Passing these tests does not verify model-weight downloads, GPU compatibility,
or full inference on the local machine. Run a small PDF directory through the
selected adapter for that environment-specific check.
