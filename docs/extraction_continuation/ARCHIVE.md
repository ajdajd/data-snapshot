# Historical snapshot extraction archive

Created **2026-11-24**. The
[ZIP](snapshot_extraction_legacy_2026-11-24.zip) preserves the local snapshot
detection experiments that supported the handoff, including completed benchmarks,
smoke tests, interrupted attempts, trial scripts, logs, native Docling documents,
crop examples, and older predictions and ground truth. It is committed here so
another machine can recover this evidence after pulling the repository.

Use [START_HERE.md](START_HERE.md) for current status and decisions. The ZIP
contains historical evidence, not a current installation or a ready-to-run
pipeline. Some runs are partial or failed, and recorded configurations refer
to environments that no longer exist. Do not interpret file presence as proof
of successful inference or replace the completed results with partial trials.

## Contents and exclusions

The [manifest](snapshot_extraction_legacy_2026-11-24.manifest.json) records every
member's original repository-relative path, size, and SHA-256 hash, together
with the ZIP's size and hash. It covers these older extraction locations:

- `data/evaluation_runs/`, including the five completed half benchmarks,
  Docling smoke/stability/integration trials, and the failed Unlimited-OCR run.
- `data/evaluation_runs_smoke/` and `data/evaluation_runs_smoke_pdf2image/`.
- `data/batch_runs/`, `data/evaluation_input/`, and `data/evaluation_output/`.
- Ground truth under `data/temp/{unhcr,prwp,refugee}/` and
  `data/backups/{combined,unhcr,prwp,refugee}/`.

The archive excludes the concurrent structured-data workstream: its source,
tests, documentation, `data/structured_data_trials/`, and changes to the root
README, `pyproject.toml`, and `uv.lock`. It also excludes environments, model
weights, source PDFs, image datasets, and bytecode caches. Obtain those assets
separately before trying to repeat inference.

All originals were retained in place to preserve existing paths while another
task was active. This is an evidence backup, not a record of completed deletion.
Any later cleanup must check dependencies and confirm approval before removing
ignored originals. Keep the small readable reports and handoff alongside the ZIP.

## Verify and restore

From the repository root, verify the checksum and ZIP integrity:

```shell
(cd docs/extraction_continuation && \
  sha256sum -c snapshot_extraction_legacy_2026-11-24.zip.sha256)
unzip -t docs/extraction_continuation/snapshot_extraction_legacy_2026-11-24.zip
```

Extract into a fresh temporary directory so existing work is not overwritten:

```shell
restore_dir="$(mktemp -d /tmp/snapshot-extraction-restore.XXXXXX)"
unzip -n docs/extraction_continuation/snapshot_extraction_legacy_2026-11-24.zip \
  -d "$restore_dir"
```

The restored directory contains the original `data/...` layout. Inspect it there
first. Before selectively restoring files into the checkout, compare hashes
with the manifest, check current callers, and obtain approval for any ignored
or untracked files that would be modified. Historical scripts may require old
dependencies or missing temporary environments; do not execute them as part of
restoration. ZIP CRCs and all member hashes were checked against the originals
when this archive was created.
