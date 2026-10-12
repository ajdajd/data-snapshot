# Research Notebooks

Notebooks contain exploratory workflows, executed research evidence, analysis,
and small utilities. They are not all maintained as current applications.

## Environment

Install the repository's locked notebook environment:

```shell
uv sync --locked --extra notebooks
uv run --extra notebooks python -m ipykernel install --user \
    --name data-snapshot --display-name "Data Snapshot (uv)"
```

Launch the locked Jupyter environment directly:

```shell
uv run --extra notebooks jupyter lab
```

It is also fine to launch Jupyter from Conda or an editor, but select the
**Data Snapshot (uv)** kernel. Conda is not a second dependency specification
for this repository.

## Maintained research workflows

| Directory | Status | Purpose |
|---|---|---|
| `metadata_extraction/` | Active | Sampling, calibration, batch extraction, export, and review inputs |
| `schema_discovery/` | Active research record | Paper 2 discovery and analysis workflow |
| `schema_validation1/` | Final research record | Held-out Schema v1.1 validation |
| `schema_validation2/` | Final research record | Confirmatory Schema v1.1.1 validation |
| `schema_validation3/` | Final research record | Confirmatory Schema v1.2 validation |
| `schema_v1_2_representation_stress_test/` | Superseded archive | Preserved exploratory instrument and evidence |

"Final research record" means the notebooks, prompts, outputs, and reports are
retained as executed evidence. It does not imply that live API cells should be
rerun. Read the adjacent protocol or report before executing a validation
notebook.

## Historical and utility notebooks

The following directories remain useful context but are not maintained as
clean-checkout entry points:

- `characterization/` contains earlier snapshot-description and modality work.
- `demos/` contains exploratory SDK and model demonstrations.
- `utils/` contains one-off data preparation and paper-analysis notebooks.

Some of these notebooks retain the retired `dsa` package name, old local paths,
or dependencies that are not in the maintained `notebooks` extra. They are
preserved rather than silently rewritten because their executed state is part
of the project history. Promote and repair a notebook before using it as a new
workflow.

## Data and API safety

Most notebook inputs and generated outputs are gitignored. A clean clone does
not contain the corpora, images, document metadata, gold records, or complete
run outputs needed to reproduce every cell.

Notebooks that use `OPENAI_API_KEY` can make paid, nondeterministic API calls.
Inspect the notebook and its configuration before running cells. Prefer dry-run
or analysis-only paths where available, and never overwrite tracked evidence
with a fresh run.
