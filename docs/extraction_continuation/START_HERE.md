# Continue snapshot extraction research

This folder preserves the extraction research state verified on **2026-11-23**
at commit `f67ce8f`, including the earlier roadmap supplied by the user.
Begin read-only and reconcile this snapshot with newer commits before acting.

## Reading order

1. Read [the handoff](README.md) for completed work, blockers, local assets,
   remaining decisions, and the proposed bounded audit.
2. Read [the comparison report](../half_paper_benchmark_report.md) for the
   protocol, corpus counts, scores, and their limitations.
3. Inspect [the preserved evidence](evidence/2026-11-23/verification.json)
   and the relevant model's reports under that same directory. The original
   [roadmap image](evidence/2026-11-23/roadmap.png) is included.
   For the full historical local outputs and trial scripts, read
   [the archive instructions](ARCHIVE.md) before opening or restoring the ZIP.
4. Read the repository guidance, [extraction guide](../../src/data_snapshot/inference/README.md),
   and [evaluation guide](../../src/data_snapshot/evaluation/README.md) before
   implementation. Follow the current
   [create-adapter skill](../../.agents/skills/create-adapter/SKILL.md) for adapters.

## Establish the current checkout

- Use the current repository root, branch, status, and commit. The saved
  `/home/ajd/...` paths describe the original machine; do not require that path
  or recreate the former `data-snapshot-annotation` checkout on another machine.
- Check which datasets, predictions, native sidecars, weights, and environments
  exist locally. Report copies and the historical extraction ZIP survive Git;
  source PDFs, weights, and environments do not. Recover archived predictions
  and native sidecars into a fresh location if needed. Do not treat an absent
  local artifact as proof that its recorded experiment never completed.
- Read [the local environment repair](ENVIRONMENT.md) before relying on the
  older path observations. The shared local launchers were repaired on
  2026-11-24 without syncing dependencies; another machine needs its own setup.
- Five fixed-half benchmarks completed: DocLayout-YOLO, YOLO11, YOLO26, Heron,
  and Egret Medium. PP-DocLayoutV3 and Surya Fast Layout remain planned, and
  checkpoint A's visual audit and incumbent selection remain unfinished.
- Context completion, relevance filtering, and training are conditional roadmap
  items. The 18-page audit is a recommendation, not an executed experiment or
  permission to generate outputs. Summarize the next bounded action for the user.

## Preserve scope and evidence

Keep snapshot detection/cropping separate from snapshot metadata extraction
(currently Schema v1.4) and parent-document metadata. Keep the fixed 238-PDF
manifest, evaluation IoU 0.5, and minimum predicted area 0.008 for comparable
experiments. Work in this research repository; production integration in
`data-snapshot-pipeline` is separate.

Ask permission before modifying, deleting, or overwriting ignored or untracked
files. Preserve historical evidence. Do not sync dependencies during the initial
investigation. New adapters require hardware assessment, research/approval, and
a successful real single-PDF smoke test before full integration. Hand large
installs/downloads to the user as exact commands unless explicitly asked to run
them. Batch necessary clarification questions.

## What this folder contains

- `README.md`: progress, earlier roadmap, environment observations, recommended
  next steps, offline test command, and a future-session prompt.
- `evidence/2026-11-23/<model>/reports/`: 20 byte-for-byte copies of the five
  completed models' pooled and per-source reports; original paths remain in
  report metadata as historical provenance.
- `evidence/2026-11-23/verification.json`: verification results, source paths,
  hashes, model/runtime metadata, and native link/page counts.
- `evidence/2026-11-23/roadmap.png`: the user's original planning notes.
- `evidence/2026-11-23/unlimitedocr_failure.jsonl`: the real sample attempt's
  out-of-memory failure, including preceding rendering events.
- `ARCHIVE.md`, the historical ZIP, its manifest, and checksum: original local
  experiment outputs and restoration instructions.
- `ENVIRONMENT.md` and the dated repair inventory: the local path repair and
  coordination guidance for the structured-data workstream.

Include this whole folder when committing. After committing and pushing it,
the next machine can pull the repository and start with this instruction:

> Read `docs/extraction_continuation/START_HERE.md` and reconstruct our current
> snapshot extraction progress before proposing the next action.
