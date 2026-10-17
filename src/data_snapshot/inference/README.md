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
extras in the same sync when that workflow needs them. `tfid` and `unlimitedocr`
require incompatible Transformers and PyTorch versions and cannot be installed
together; `uv sync --all-extras` is unsupported.

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
