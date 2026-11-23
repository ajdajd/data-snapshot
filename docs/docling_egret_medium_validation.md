# Docling Egret Medium validation

Validated on 2026-10-19. The half-sample benchmark is ready for the user to run;
no Egret half-sample results are claimed here.

## Checkpoint and protocol

`docling-project/docling-layout-egret-medium` is pinned to
`77ede7cc7bed96d853c58f319734803d6ea2ea5c`, with weight SHA-256
`e7fc5b9a353826c123c5d03efc230909ac02b93e26293ec7cb4db8978fe9e3af`.
It uses `DoclingEgretMediumConfig` and the existing converter and prediction
transformation in `src/data_snapshot/inference/docling_heron.py`. The integrated
benchmark key is `docling_egret_medium`; existing Heron callers keep their default
checkpoint.

The protocol matches the completed Heron half-sample experiment: fixed 238-PDF
manifest, evaluation IoU 0.5, minimum predicted area 0.008, CUDA FP32, layout
batch size 1, native document concurrency 2, four accelerator threads, and
English RapidOCR on CPU through ONNX Runtime. Native PDF parsing, layout
postprocessing, and reading order remain enabled. Table structure, enrichment,
and compilation remain disabled. The detector score threshold is 0.3. Only
native picture/table bounds are scored; captions and footnotes remain separate
native associations, without box expansion.

Resolved pipeline options matched Heron's apart from the model specification;
the checkpoints' preprocessing JSONs are identical, including 640-by-640 input.
Egret uses D-FINE and Heron RT-DETRv2, so differences represent a checkpoint/model
substitution, rather than learned weights within one architecture. Comparisons
against the saved PyMuPDF models remain complete-pipeline comparisons.

## Completed checks

- **Pre-integration smoke:** both pages of
  `08072015_northgovernorateprofile.pdf` completed in **20.718 seconds**, including
  initialization and conversion. Peak process RSS was **2,661.9 MiB**; PyTorch
  peak allocated/reserved VRAM was **188.5/220.0 MiB**. The GTX 1650 Ti has 4 GiB
  VRAM; WSL has a 12 GiB RAM limit. GPU peaks cover the PyTorch allocator only.
- Both page overlays were inspected. Coordinates are plausible, but some
  infographics and surrounding text form one broad picture region. Diagnostic
  page-image retention at scale 2 supported overlays/crops; production retention
  is disabled, with `images_scale=1`. Native layout requests scale 1 in both.
- **Nine-PDF manifest trial:** intentionally stopped at the user's request after
  **six completed PDFs / 61 pages**, all from UNHCR and PRWP. All completed
  documents had full page coverage, and their native caption/footnote references
  resolved. The last completed document was emitted at **222.6 seconds**. Two
  later refugee PDFs were in flight at interruption; this is not a complete
  nine-PDF test or a validated refugee result. No final aggregate predictions,
  evaluation metrics, process peak RSS, or allocator peaks were retained for
  this interrupted attempt.
- **Post-integration smoke:** schema-valid predictions matched the standalone
  smoke detections exactly, using document concurrency 2. **58 focused offline
  tests** passed across checkpoint selection, metadata, native conversion,
  filtering, benchmark orchestration, and reporting. Black and the offline
  lockfile check passed.

The smoke and partial trial emitted empty-OCR and dense-vector page-separator
warnings. Conversion continued, but this does not establish OCR completeness or
association correctness. No page-by-page visual audit of the six-PDF trial was
performed.

On the single two-page smoke PDF, using Heron's saved concurrent half-run
predictions for that same document:

| Metric at IoU 0.5 | Heron | Egret Medium |
|---|---:|---:|
| Retained Figure predictions | 5 | 3 |
| Figure TP / FP / FN | 3 / 2 / 0 | 1 / 2 / 2 |
| Figure precision | 0.600 | 0.333 |
| Figure recall | 1.000 | 0.333 |
| Matched Figure mean IoU | 0.780 | 0.514 |
| Retained Table predictions | 1 | 1 |
| Table TP / FP / FN | 0 / 1 / 1 | 0 / 1 / 1 |

These are one-document diagnostics, not six-PDF, half-sample, or significance
results. No speed ranking is inferred from the smoke timings.

## Evidence

Local evidence is under
[`data/evaluation_runs/docling/egret_medium_20261019/`](../data/evaluation_runs/docling/egret_medium_20261019/):

- `smoke/`: raw native layout clusters, native document JSON, links/crops,
  inspected overlays, and measured runtime/memory.
- `preintegration9/`: six native documents, per-document completion records,
  `partial_summary.json`, and the interrupted run's process output.
- `integration_smoke/`: canonical predictions, the same-document Heron subset,
  ground truth, two evaluation reports, `comparison.json`, and process output.
- `verification_environment.json` and `verification_scripts/`: exact package
  versions, asset hashes, resolved options, and standalone trial sources.
- `run_config.json`: local half-benchmark configuration overriding only the
  checked-in configuration's artifact path to the existing temporary assets.

These generated artifacts are gitignored and may not accompany a clean clone.
Historical Heron/PyMuPDF reports, the fixed manifests, weights, dependencies,
lockfile, and legacy batch runner were not changed.

## Run the half benchmark in the existing environment

Keep the existing environment and assets under `/tmp/docling-heron-1a7BNUMJ/`.
The tested runtime is Python 3.10.19, Docling 2.140.0, Transformers 5.20.1,
Torch 2.10.0 (CUDA 12.8), RapidOCR 3.10.0, and ONNX Runtime 1.23.2. Its installed
package versions and asset hashes match the saved Heron environment. No sync,
download, or environment migration is needed for this command:

```shell
cd /home/ajd/data-snapshot-annotation
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH="$PWD/src" \
  /home/ajd/.local/bin/uv run --no-project \
  --python /tmp/docling-heron-1a7BNUMJ/venv/bin/python \
  python scripts/evaluate_benchmark_half.py \
  --config data/evaluation_runs/docling/egret_medium_20261019/run_config.json
```

This processes the fixed 238 PDFs and writes fresh results beneath
`data/evaluation_runs/docling/egret_medium_20261019/paper_benchmark_half/docling_egret_medium/`.
Capture process output as well as the automatically retained source JSONL logs
when preserving native warnings. Do not use `--overwrite` to resume an existing
native export; the adapter refuses to replace its evidence directories.

After completion, build the comparison without replacing the historical report:

```shell
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH="$PWD/src" \
  /home/ajd/.local/bin/uv run --no-project \
  --python /tmp/docling-heron-1a7BNUMJ/venv/bin/python \
  python scripts/summarize_benchmark.py \
  --output-root data/evaluation_runs/pymupdf/paper_benchmark_half \
  --docling-root data/evaluation_runs/docling/user_run_concurrent_20261019/paper_benchmark_half \
  --egret-root data/evaluation_runs/docling/egret_medium_20261019/paper_benchmark_half \
  --output data/evaluation_runs/docling/egret_medium_20261019/half_comparison.md
```

Temporary directories can be removed by system cleanup; preserve them before
rebooting or cleaning `/tmp`. A later `uv sync --locked --extra docling_heron`
would use the repository lock, which differs from this tested environment in
some transitive dependencies, including Pillow, OpenCV, and Pydantic. The exact
differences are saved in `lock_environment_differences.json`. Revalidate after
migration, and rerun Heron in that environment for strict checkpoint attribution.
