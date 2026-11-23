# Snapshot extraction research handoff

Updated **2026-11-23**, Asia/Manila. Evidence was checked at research commit
`f67ce8f`. Five fixed-half benchmarks are complete; detector selection at
checkpoint A remains unfinished. The immediate focus is detecting and cropping
snapshots from PDFs. Snapshot metadata extraction uses Schema v1.4 and remains
a separate workflow, as does parent-document metadata processing.

## Start here

For a new session or machine, begin with [START_HERE.md](START_HERE.md).
All absolute paths below describe the investigated machine; resolve paths from
your current checkout and assess available local assets before using commands.

- Investigated checkout: `/home/ajd/data-snapshot`; former name:
  `data-snapshot-annotation`. Remote: `git@github.com:ajdajd/data-snapshot.git`.
- [Benchmark comparison and methodology](../half_paper_benchmark_report.md).
- [Preserved evidence](evidence/2026-11-23/): 20 original JSON reports,
  the earlier roadmap image, the Unlimited-OCR failure log, and a verification
  record with source paths and SHA-256 hashes. Include this entire directory in
  the commit so these small copies travel with Git.
- [Extraction guide](../../src/data_snapshot/inference/README.md),
  [evaluation guide](../../src/data_snapshot/evaluation/README.md), and
  [evaluation specification](../evaluation_spec.md).

Large predictions, native Docling sidecars, PDFs, weights, and environments are
still local assets. The evidence copies preserve results and context, not the
ability to repeat every verification on a clean clone. Hashes identify originals;
they do not back up those files. Preserve the local artifact roots below before
cleaning this machine.

## Verified benchmark progress

The fixed [half manifest](../../src/data_snapshot/evaluation/configs/paper_benchmark_half.json)
uses seed 42 and selects 238 PDFs: 169 UNHCR/ReliefWeb, 50 PRWP, and 19 refugee
PADs. It covers 3,753 pages, 1,324 Figures, and 625 Tables. Keep this selection
fixed for comparable runs. All selected PDFs and annotation files were available.

Evaluation IoU is 0.5; the minimum predicted-area filter is 0.008. Overall
metrics come from pooled reports. Spatial means describe matched detections.
These are directional half-sample results, not full-benchmark or significance
claims.

| Model | Status | Figure precision / recall | Table precision / recall |
|---|---|---:|---:|
| DocLayout-YOLO | Completed | 0.587 / 0.802 | 0.474 / 0.886 |
| YOLO11 medium | Completed | 0.405 / 0.772 | 0.503 / 0.885 |
| YOLO26 medium | Completed | 0.411 / 0.731 | 0.468 / 0.902 |
| Docling Heron | Completed | 0.442 / 0.718 | 0.521 / 0.899 |
| Docling Egret Medium | Completed | 0.421 / 0.711 | 0.536 / 0.888 |
| TF-ID Large | Implemented but unverified on fixed half | No saved result | No saved result |
| Unlimited-OCR | Blocked on demonstrated local setup | No completed result | No completed result |

All five completed models contain exactly the manifest's document IDs, identical
ground truth, and no report document mismatches. All five pooled prediction
files passed evaluation schema v1.3 validation. All 20 saved source/pooled reports
matched metrics recomputed from predictions at both saved IoU thresholds.

Both Docling models have 238 native JSON sidecars and 238 document-completion
events covering 3,753 pages, without expected/processed page-count mismatches.
Heron's 817 caption and 219 footnote references resolve; Egret's 846 caption
and 127 footnote references resolve. This establishes preservation, not correct
association or complete OCR.

DocLayout-YOLO leads Figure precision and recall. Egret improves Table precision
over Heron while losing recall; it is not a general improvement. The three
original models use PyMuPDF. Docling uses native PDF parsing, OCR, layout
postprocessing, and reading order, so cross-pipeline differences cannot be
attributed solely to model weights. Heron and Egret share the integration and
recorded settings, with different checkpoint architectures.

## Earlier roadmap and current status

The user supplied the [original roadmap image](evidence/2026-11-23/roadmap.png)
on 2026-11-23 as context for earlier work. The following preserves its intended
sequence and conditions. Planned rows are not completed experiments or blanket
authorization to install, download, train, or run models.

| Step | Earlier scope | Current status and decision |
|---|---|---|
| 1 | Benchmark `docling-project/docling-layout-heron` with optional picture classification/descriptions disabled; preserve native context separately. | Completed half benchmark. Context correctness and crop completeness remain unverified. |
| 2 | Benchmark `PaddlePaddle/PP-DocLayoutV3_safetensors`; preserve contextual labels and reading order separately; no custom context expansion or relevance filter. | Proposed, previously planned; no adapter or run evidence found. |
| 3 | Benchmark `docling-project/docling-layout-egret-medium` through the shared Docling integration with comparable settings. | Completed half benchmark. |
| 4 | Benchmark `datalab-to/surya_layout2` using `FastLayoutPredictor`, avoiding the VLM layout/OCR path; verify scores, coordinates, reading order, and licensing. | Proposed, previously planned; no adapter or run evidence found. |
| 5 | Checkpoint A: compare completed detectors, representative errors, completeness, composites, runtime/resources, and error overlap; select an incumbent and which steps 6–8 to run. | Comparison report exists; visual error audit and selection remain unfinished. No training at this checkpoint. |
| 6 | Conditional: small confidence/minimum-area sweep and modest padding, one factor at a time, selected on development data. | Proposed. Reuse cached predictions where possible; lower thresholds may need inference because discarded detections cannot be recovered. |
| 7 | Conditional: one conservative context-completion method; prefer native links; compare unchanged bounds and padding. | Proposed. Measure required context, unrelated content, wrong attachments, and merges. Keep uncaptioned snapshots eligible. |
| 8 | Conditional: `docling-project/DocumentFigureClassifier-v2.5` on actual incumbent proposals, without training. | Proposed. Start with conservative rejection; inspect lost maps, matrices, and composites. Compare at unchanged boundaries; low IoU is not semantic irrelevance. |
| 9 | Checkpoint B: compare retained settings, context, and filtering separately and together; drop stages that do not justify their cost. | Proposed; depends on checkpoint A and justified experiments. Skip training if inexpensive changes suffice. |
| 10 | Conditional: frozen small DINOv3 backbone with a simple relevance classifier trained on adjudicated detector proposals. | Proposed. Use hard negatives and document/template-aware splits; distinguish incomplete true snapshots from irrelevant regions. This cannot recover missing proposals. |
| 11 | Conditional alternative: fine-tune one pretrained detector on complete snapshot boxes; no scratch training or synthetic-data generator. | Proposed. Establish training, validation, and protected evaluation partitions first; compare with the best inexpensive pipeline. |
| 12 | Freeze choices, verify generalization, and integrate only the chosen inference path in the research repository. | Proposed. Identify genuinely held-out documents/templates; report held-out and descriptive full-corpus results separately. |

The roadmap confirms that context association, crop expansion, a second-stage
classifier, and training had been considered. Each remains conditional; no
extraction-specific implementation or completed experiment was found for
steps 6–11. Metadata field-classification notebooks are separate work.

## Local evidence and environment

Original completed run roots, relative to this checkout:

| Models | Root |
|---|---|
| DocLayout-YOLO, YOLO11, YOLO26 | `data/evaluation_runs/pymupdf/paper_benchmark_half/<model>/` |
| Heron | `data/evaluation_runs/docling/user_run_concurrent_20261019/paper_benchmark_half/docling_heron/` |
| Egret Medium | `data/evaluation_runs/docling/egret_medium_20261019/paper_benchmark_half/docling_egret_medium/` |

Each root has `ground_truth/`, `predictions/`, and `reports/`, with pooled
`corpus.json` and per-source JSON. Docling native sidecars are at
`predictions/sources/<source>.native/<PDF filename>.json`; completion logs are
under `logs/`. The verification record preserves exact paths and hashes.

- Dataset: `data/hf_datasets/data-snapshot` links to
  `/home/ajd/hf_datasets/data-snapshot`.
- Hardware observed: GTX 1650 Ti, 4 GiB VRAM, compute capability 7.5;
  WSL reports about 12 GiB RAM. Recheck available resources before new inference.
- Python 3.10.19 and `uv` are available. `.venv` has Torch 2.10.0,
  Transformers 5.20.1, PyMuPDF 1.27.2.3, pytest, and jsonschema; Docling,
  RapidOCR, ONNX Runtime, Ultralytics, and DocLayout-YOLO are absent.
- The rename left `.venv/bin/pytest` and the editable package `.pth` pointing to
  `/home/ajd/data-snapshot-annotation`. Use the workaround below for offline
  checks; do not assume command launchers work or sync just to investigate.
- YOLO weights remain under `models/`. TF-ID and Unlimited-OCR checkpoints
  are cached under `/home/ajd/.cache/huggingface/hub/` at approximately 3.29 GB
  and 6.67 GB respectively. Cached weights do not establish runnable inference.
- Neither `models/docling` nor `/tmp/docling-heron-1a7BNUMJ` was present.
  Egret's local `run_config.json` still references that missing artifact root.
  The lock differs from the historical Docling environment in some transitive
  dependencies; validate a recreated runtime before making strict model claims.
- The older [Egret validation record](../docling_egret_medium_validation.md)
  describes pre-run checks. Its benchmark was subsequently completed; its
  temporary-environment commands are historical.

TF-ID has historical predictions under `data/batch_runs/` and
`data/evaluation_input/`, and reports under `data/evaluation_output/`.
No TF-ID artifacts were found under `data/evaluation_runs/`. The half report's
blank cells result from missing reports; why the run was omitted remains
unknown. Historical outputs do not establish comparable renderer/runtime
settings. The `tfid` extra conflicts with Docling and Unlimited-OCR.

Unlimited-OCR reached real generation in the nine-PDF sample on 2026-10-17,
then failed with CUDA out-of-memory. The [preserved failure log](evidence/2026-11-23/unlimitedocr_failure.jsonl)
is stronger evidence than the older description of the work as paused.
Rendered-page completion in that log is not successful model inference. No
completed predictions or benchmark were found. Its BF16 guard uses PyTorch's
default emulation-inclusive check; passing it does not prove native BF16 support.

Native Docling bounds do not expand to linked captions or footnotes. The half
runs saved predictions and native JSON, not mass-exported crops. Two caption
examples in `data/evaluation_runs/docling/stability9_20261019/native_crop_examples_verified/`
show linked text outside native crops. OCR completeness, association accuracy,
footnote crop correctness, and broader visual quality remain unassessed.

The separate `/home/ajd/data-snapshot-pipeline` application has its own four
adapters, page-image detection interface, cropping, and Schema v1.4 metadata
extraction. Research adapters emit evaluation JSON, and native Docling consumes
PDFs. Production integration is separate work; the earlier roadmap explicitly
keeps final integration here.

## Recommended resumption

1. Perform the bounded audit below using existing outputs, to classify the
   remaining extraction failures before spending resources on more inference.
2. Resume roadmap step 2, then step 4: research hardware/runtime feasibility,
   pass an approved single-PDF smoke test, and only then integrate and run the
   unchanged half manifest. These model choices have not received a new
   feasibility assessment in this investigation.
3. Finish checkpoint A using completed runs and representative error overlap;
   decide which inexpensive experiments are justified.
4. Test only justified settings/padding, context completion, and relevance
   filtering, then checkpoint B. Training remains conditional on a documented
   limitation that inexpensive approaches cannot resolve.
5. Freeze the chosen path and identify genuinely protected evaluation data
   before final claims. Repeatedly inspected half-sample data are development
   evidence, not newly held-out confirmation.

### Proposed bounded audit

Freeze 18 pages from the existing manifest, six per corpus, covering Figures,
Tables, high false-positive pages, and native context links. Use unchanged
DocLayout-YOLO as the baseline and inspect all five completed models on the
same pages. Record missing snapshots, irrelevant detections, clipped content,
missing headings/captions/notes, wrong links, and composite splits/merges.
Judge semantic relevance separately from geometric matching.

Success means all selected pages receive review, per-model error counts and
examples are recorded, and the findings motivate specific next experiments.
This is a diagnostic audit, not a significance test. It needs CPU rendering,
the saved PDFs/predictions/native sidecars, and human review; no model download,
GPU inference, API call, or training is needed.

Proposed output: `data/evaluation_runs/extraction_quality_audit_20261123/`,
with selection, review records, overlays, and findings. This directory has not
been created and the audit has not been approved or executed. Choose a fresh
dated directory when resuming and obtain approval for generated local outputs.

## Verification and working rules

The reconstruction passed 89 focused offline tests. The command below avoids
dependency sync, old launchers, and writes to repository bytecode/test caches:

```shell
cd /home/ajd/data-snapshot
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/src" \
  uv --no-cache run --no-sync --offline python -m pytest -q -p no:cacheprovider \
  tests/test_adapter_utils.py tests/test_docling_heron.py \
  tests/test_unlimitedocr.py tests/test_evaluate_model.py \
  tests/test_benchmark.py tests/test_benchmark_cli.py \
  tests/test_benchmark_sample_cli.py tests/test_benchmark_report.py
```

These tests use fake model outputs; they do not verify new GPU inference.

- Ask explicit permission before modifying, deleting, or overwriting ignored
  or untracked files. Preserve historical predictions and benchmarks.
- For new adapters, follow the current
  [create-adapter skill](../../.agents/skills/create-adapter/SKILL.md): hardware
  assessment and research/approval, then successful real single-PDF smoke
  testing before full integration. Its old repository name refers to this checkout.
- Hand large installs/downloads to the user as exact commands unless explicitly
  asked to execute them. Do not sync during an initial investigation; it can
  remove extras needed by another workflow.
- Follow [coding standards](../../.agents/rules/coding-standards.md): Black,
  NumPy docstrings, modern type hints, and PEP 8 naming. Batch necessary questions.
- Keep snapshot extraction, snapshot metadata extraction, and parent-document
  metadata separate. Schema v1.4 is current; do not revive v1.1/v1.2 deferrals
  without checking current evidence.

## Prompt for a future session

> Continue snapshot extraction research in this checkout. Read
> `docs/extraction_continuation/START_HERE.md` first, then follow its reading
> order. Reconcile the current checkout
> and local assets with the recorded state before acting. Five half benchmarks
> are complete; PP-DocLayoutV3, Surya Fast Layout, and checkpoint A remain
> unfinished. Conditional context/filtering/training work is not yet selected.
> Start read-only, keep metadata work separate, preserve ignored artifacts,
> and follow the recorded approval and single-PDF smoke-test gates.
