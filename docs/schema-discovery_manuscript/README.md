# Schema Discovery Manuscript

Tracked LaTeX source and figures for the Data Snapshot Metadata Schema
Discovery paper (Paper 2).

Paper 1's Data Snapshot Extraction Benchmarking manuscript is maintained
externally in Overleaf and is not stored in this repository.

## Contents

- `main.tex` is the manuscript entry point.
- `references.bib` contains the bibliography.
- `data/` contains tracked manuscript figures.
- `internal_docs/` contains design and standards-alignment records that support
  the manuscript but are not publication sections.
- Local conference style and bibliography files make the source independent of
  a system-wide template installation.

## Build

From this directory, a conventional local build is:

```shell
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Build artifacts and `main.pdf` are gitignored. A successful build may still
contain ordinary LaTeX warnings; inspect the final log for unresolved
references, citations, or missing assets.

The repository does not manage a TeX distribution through `uv`. Use Overleaf
or a local LaTeX installation for manuscript compilation.

## Editing boundary

The manuscript reports completed schema-discovery and validation evidence.
Keep the evaluated schema versions, post-validation amendments, and generated
current schema clearly separated. Do not regenerate or overwrite tracked
figures merely to test the build.
