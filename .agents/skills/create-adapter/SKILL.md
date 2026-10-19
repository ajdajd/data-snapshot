---
name: create-adapter
description: Develop or update layout-detection prediction adapters in the Data Snapshot research repository that emit Unified Evaluation Schema v1.3. Use when integrating a model or library into src/data_snapshot/inference; do not use for Label Studio ground-truth conversion, metadata extraction, or the separate production pipeline.
---

# Create Adapter

Build the smallest adapter that converts one model's layout detections into the
repository's Unified Evaluation Schema v1.3 prediction format.

This skill applies to the research repository at
`data-snapshot-annotation`. Production extraction belongs in the
separate `data-snapshot-pipeline` repository; do not copy its architecture,
environment, weights, or workflow into this checkout.

## Establish the Scope

Before editing:

1. Read the closest existing adapter in `src/data_snapshot/inference/`:
   - `yolo11.py` or `yolo26.py` for Ultralytics models;
   - `doclayoutyolo.py` for DocLayout-YOLO-style models;
   - `tfid.py` for generative Hugging Face models.
2. Read the current contracts:
   - `docs/data-snapshot-eval-v1.3.schema.json`;
   - `src/data_snapshot/inference/README.md`;
   - the evaluation contract in `src/data_snapshot/evaluation/README.md`.
3. Search for every caller of the adapter pattern before changing shared code:
   `rg "run_.*adapter|Config|_ADAPTERS" src tests scripts`.
4. Use official model and library documentation for current installation,
   loading, inference, output, coordinate, label, and score behavior. Treat a
   user-provided demo as evidence, not as permission to run it or download
   weights.
5. Assess whether the current machine can run the proposed model configuration
   before recommending installs or downloads. Use read-only checks for the OS
   (including WSL limits), Python version, CPU capabilities, GPU model and
   driver/CUDA compatibility, precision support, available RAM/VRAM, and disk
   space. Compare these with official runtime requirements and expected memory
   for both weights and inference working space; weight-file size alone is not
   a sufficient memory estimate. Distinguish observed facts, estimates, and
   unknowns. If access to hardware information is blocked, give the user exact
   diagnostic commands. Report known incompatibilities before proceeding and
   propose alternatives without installing them or assuming they work. This
   assessment does not replace the required single-PDF smoke test.

After the research pass, present a concise implementation plan in chat that
covers:

- model installation, initialization, and inference input;
- machine compatibility for the proposed runtime, device, and precision,
  including memory headroom, known blockers, and checks still needed;
- raw output parsing, label normalization, coordinate conversion, and score
  handling;
- the minimal configuration surface and optional dependencies;
- required callers, tests, fixtures, documentation, and other integration
  points;
- a single-PDF smoke test on the user's target machine before full integration,
  including its input, runtime, expected memory needs, and success criteria;
- any downloads, model execution, or generated files needed for verification.

Batch genuinely ambiguous model choices into the same message. Wait for
explicit user approval before changing project files, installing dependencies,
downloading weights, running real inference, or writing generated outputs. Keep
the plan in chat; create an `implementation_plan.md` only when the user asks for
one.

For large library installs or model downloads, ask the user to run the terminal
commands instead of launching them and waiting in the agent session. Provide
copy-paste commands with the working directory, target environment, and expected
download size when known. This includes first-run inference commands that would
automatically download weights. Wait for the user to confirm completion or share
errors before continuing dependent work. General integration approval does not
override this handoff; execute these commands only if the user specifically asks
the agent to run them.

## Pass a Single-PDF Smoke Test Before Integration

After approval, test the real model on one short, representative PDF before
writing the full adapter or changing package dependencies, the lockfile,
benchmark registration, or repository documentation. Use the intended Python
version, runtime, model revision, device, precision, and preprocessing on the
user's actual machine. Check available RAM/VRAM and hardware support first;
successful dependency resolution or model loading alone does not establish
inference compatibility.

Use the official inference API with the smallest standalone prototype needed,
kept in a temporary directory. Reuse the repository's PDF renderer where
practical. Prefer an isolated temporary environment for new dependencies;
do not replace the repository environment just to probe compatibility. Obtain
approval for installs, weight downloads, inference, and output locations as
part of the smoke-test plan. If the user will install dependencies or run the
test, provide exact commands and wait for the result.

The smoke test must:

- process every page of the selected short PDF, rather than a full corpus or
  the nine-document benchmark sample;
- complete real inference without memory, device, dependency, or truncation
  failures;
- expose raw labels, boxes, and scores (or confirm their absence), with a
  visual check that relevant detections and coordinate interpretation are
  plausible;
- record the tested settings, page count, elapsed time, and peak memory where
  observable, disclosing anything not measured.

If the test fails, cannot run, or produces unusable output, stop before full
integration. Report the evidence and propose a bounded next step; fake-output
tests do not satisfy this gate. Changes such as quantization, a different
runtime, or CPU offloading need a revised plan within the user's authorization.
Proceed after a successful smoke test when integration is already approved;
otherwise present the result and request integration approval. Do not request
the same authorization twice.

## Preserve the Output Contract

The adapter output boundary is `pred_json_path`. Preserve these invariants:

- `info.schema_version` is `"1.3"` and `info.type` is `"prediction"`.
- Canonical labels come from `data_snapshot.constants.LABEL_MAP` and are only
  `"Figure"` and `"Table"`; ignore irrelevant model classes.
- Bounding boxes are normalized `[x1, y1, x2, y2]` with top-left origin and
  coordinates in `[0, 1]`.
- Use `normalize_bboxes_xyxy_with_indices()`, then use each retained source
  index to select the matching label and score. Normalization may drop boxes;
  positional zipping after normalization can silently misalign detections.
- Clamp confidence scores to `[0, 1]`. Use `1.0` only when the model genuinely
  provides no confidence, and document that choice.
- Keep `filter_small=True` in the adapter config and apply
  `filter_small_predictions()` by default. The shared threshold is
  `MIN_PREDICTION_AREA = 0.008`; the evaluator does not filter again.
- Use zero-based `page_index`, `"{doc_id}::p{page_index:03d}"` page IDs, and
  `"{page_id}:{object_index}"` object IDs.
- Include every processed document in `documents`. Match existing adapters by
  omitting page entries that contain no retained objects.
- Record truthful model name, version or weight identifier, configuration
  notes, run ID, and UTC creation time.

Do not copy the schema into the skill or invent a second output model. The JSON
Schema is authoritative.

## Implement the Adapter

Begin full implementation only after the single-PDF smoke-test gate passes.

Add `src/data_snapshot/inference/<adapter_name>.py` and follow the closest
existing adapter's structure:

- a descriptive public module docstring;
- model and output constants;
- a narrow raw-label-to-canonical-label mapping;
- a typed `<AdapterName>Config` containing only supported, useful settings;
- `run_<adapter_name>_adapter_directory(...) -> Path` with the same public
  calling shape as existing adapters;
- recursive, sorted PDF discovery and a clear `FileNotFoundError` when none
  are found;
- PDF rendering through `convert_pdf_to_images()`, defaulting to PyMuPDF;
- model-specific inference and output parsing;
- a module CLI consistent with the existing per-adapter commands.

Reuse `data_snapshot.constants` and `data_snapshot.utils`. Do not create an
adapter base class, registry framework, wrapper layer, or new shared helper for
one model. Extract shared code only when there is demonstrated reuse and the
change is separately in scope.

Follow `.agents/rules/coding-standards.md`: Black formatting, NumPy docstrings
for public Python objects, modern Python 3.10+ type hints, and PEP 8 naming.

## Update Only Required Integration Points

Review each place below; update it only when the adapter's intended use needs
it.

| Place | When to change it |
|---|---|
| `pyproject.toml` | Add a model-specific optional dependency group. Never add model dependencies to `dev`. |
| `uv.lock` | Update when dependency metadata changes. Do not run `uv sync` or install large model extras unless the user requests it. |
| `src/data_snapshot/inference/README.md` | Add every supported adapter to the model table and usage guidance. |
| `src/data_snapshot/inference/__init__.py` | Keep the package description's supported-model list accurate. Do not add re-exports unless callers require them. |
| `src/data_snapshot/evaluation/benchmark.py` | Add the adapter to `_ADAPTERS` only when it should be selectable by the integrated benchmark. |
| `src/data_snapshot/inference/batch_runner.py` | Add it only when legacy partitioned batch execution is requested; this module eagerly imports every model extra. |
| `src/data_snapshot/evaluation/configs/` | Add a configuration only for a requested reproducible benchmark or paper comparison. |
| `tests/` | Cover new parsing and transformation logic offline; add model inference coverage only when its runtime is available. |

Do not modify generated predictions, historical benchmark evidence, model
weights, or other ignored or untracked data without explicit permission.

## Test the Behavior

New non-trivial parsing or transformation logic needs a small offline test.
Prefer fake model outputs or pure parsing helpers that verify:

- raw label normalization and ignored classes;
- bounding-box normalization and source-index alignment;
- score clamping or the documented no-score fallback;
- small-area filtering;
- the emitted document, page, and object identifiers;
- schema-valid prediction output.

Do not add a permanently skipped end-to-end test as the only coverage. A
skipped reference-inference test in `tests/test_adapters.py` is optional when a
stable reference fixture exists and is useful for manual model verification.

Run checks from the repository root. Format each changed Python file in its own
process:

```shell
.venv/bin/black path/to/changed_file.py
```

Run the narrow offline tests without syncing dependencies:

```shell
env UV_CACHE_DIR=/tmp/codex-uv-cache PYTHONDONTWRITEBYTECODE=1 \
  uv run --frozen --no-sync python -m pytest -p no:cacheprovider <test-paths>
uv lock --check
```

If an optional model dependency is unavailable, report that boundary and give
the exact `uv sync --locked --extra <adapter_name>` command for the user to run.
Do not claim that imports, downloads, GPU execution, or real inference passed
unless they were actually exercised.

Run a real-model smoke test only with explicit permission when it would
download weights, use a GPU, incur cost, or write ignored or untracked output.
Any post-integration model test supplements the required pre-integration
single-PDF smoke test; it does not replace it.

## Finish

Report:

- the pre-integration single-PDF smoke-test result and measured runtime limits;
- files changed and integration points intentionally left untouched;
- focused checks that passed;
- unavailable optional-runtime checks;
- any output-contract assumption that still needs human confirmation.
