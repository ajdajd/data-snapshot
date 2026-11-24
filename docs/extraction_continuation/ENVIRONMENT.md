# Local environment path repair

On **2026-11-24**, 46 text files in `.venv/bin/` were repaired after the checkout
was renamed from `/home/ajd/data-snapshot-annotation` to
`/home/ajd/data-snapshot`. The
[repair inventory](environment_path_repair_2026-11-24.json) lists each file and
its hashes before and after the change.

The repair replaced only the old absolute environment path in five activation
scripts and 41 command launchers. Permissions were preserved and each file was
replaced atomically after checking for concurrent edits. Python executable
symlinks and the editable package link were already correct and were left alone.
No dependencies were synced, installed, removed, or upgraded; the installed
distribution names and versions matched before and after the repair. The local
`.venv` itself is ignored and is not part of this commit.

Verification covered Bash activation and executable resolution, `pytest --version`,
`black --version`, package import from the current checkout, and absence of the
old environment path in `.venv/bin/`. Fish, C shell, Nushell, and Windows batch
activation scripts received the same path substitution but were not executed.
Historical paths in archived experiment evidence were preserved.

Reopen or reactivate an existing shell if it still carries the old
`VIRTUAL_ENV` or `PATH`. Existing Python processes were not restarted.

## Future environment setup

New machines should create their own environment with `uv` from the current
project and lockfile, selecting every required extra. A full environment
recreation is the standard approach when moving a virtual environment; this
local repair avoided rebuilding a shared environment while another task was
running. Do not treat these path edits as a portable environment distribution.

The concurrent structured-data task added the `structured_data` extra. Its
source, dependency changes, and lockfile changes belong to that workstream and
were excluded from the extraction archive commit. Preserve them when choosing
extras or rebuilding the environment, and coordinate before syncing a shared
environment. A plain sync may remove packages outside the selected extras.

## Message for the concurrent task

> The checkout is `/home/ajd/data-snapshot`. The old absolute `.venv` path was
> repaired in 46 launchers/activation scripts; pytest, Black, Bash activation,
> and package imports pass startup checks. No dependency sync or package-version
> changes were made. Your `structured_data` source, tests, documentation,
> `pyproject.toml`, `uv.lock`, and root README edits were left untouched and
> excluded from the archive commit. Reactivate any shell using the old path.
> Keep including the required extras in future uv syncs and coordinate before
> recreating or syncing the shared environment.
