# Data Snapshot Metadata Schema v1.4 Change Report

**Status:** Implemented

**Basis:** Batch 1 metadata extraction and human annotation review

**Previous contract:** Data Snapshot Metadata Schema v1.3

## Purpose

Schema v1.4 resolves field-boundary ambiguities observed while reviewing Batch
1 metadata. The changes focus on semantic placement and annotation consistency;
they do not add a deterministic normalization stage. Schema Validation 3 remains
a historical evaluation of Schema v1.2, and the Batch 1 extraction results
remain evidence produced under Schema v1.3.

## Changes

| Area | Schema v1.4 decision | Expected extraction effect |
|---|---|---|
| Analytical and figure roles | `AnalyticalRole` contains only `outcome`, `predictor`, `control`, and `instrumental`. The definitions require evidence from an analytical table or its labels, title, notes, or caption. | Prevents x- and y-axis encodings from being mistaken for analytical roles and discourages roles inferred from position alone. |
| Ordinary axes | New `AxisRole` contains `x_axis` and `y_axis`. New `variables[].axis_roles` records an ordinary single or shared Cartesian axis. | Gives figures a direct axis representation without implying an analytical model. |
| Multiple axes | `AxisAssignment` is renamed `MultiAxisAssignment`, and `variables[].axis_assignments` is renamed `variables[].multi_axis_assignments`. | Signals that side and position are needed only when distinct axes of the same dimension must be disambiguated. |
| Variables and dimensions | Definitions now distinguish a measured quantity from a characteristic that classifies or organizes observations. Repeated groups using the same measure are described as dimension categories. | Reduces repeated variables and moves sector, year, geography, and similar groupings into dimensions. |
| Table presentation | `row` means categories vary downward; `column` means they vary horizontally. The label cell's physical position is not the deciding evidence. | Reduces row-versus-column reversals in tables. |
| Geography | Definitions separate overall `scope`, additional `locations`, reporting `level`, location `role`, normalized `name`, and exact `source_text`. | Reduces duplicated places, parent codes assigned to child locations, and confusion between a place type and reporting granularity. |
| Population group | The field is limited to the human population that is the primary subject. Companies, institutions, products, locations, mixed entity classes, and ordinary disaggregation categories are excluded. | Reduces broad or nonhuman population entries. |
| Comparisons | The field requires an explicit comparative relationship or named comparator and excludes totals, cross-tab categories, dimensions, and merely co-present measures. | Reduces unsupported comparisons inferred from table structure. |
| Document label | The field requires an exact visible label such as `Table 3` or `Figure 4.2`; titles, captions, page numbers, filenames, and inferred positions are excluded. | Reduces inferred or partial document labels. |
| Unit and statistical form | A unit states how values are expressed; a statistical form states their mathematical form. `%` may be the unit without proving `percentage`; `rate` and `percentage` receive separate guidance. | Reduces automatic conversion of every percent-valued measure into the `percentage` statistical form. |
| Source and normalized text | Geographic definitions explicitly distinguish transcribed `source_text` from a standardized `name`. Existing normalized-term guidance continues to require exact visible wording for `source_text`. | Reduces invented source wording while retaining normalized values supported by structure or identifiers. |
| Composite visualization types | Visualization types are explicitly nonexclusive. A composite artifact records `composite_figure` and each identifiable component type. | Preserves both the overall structure and component forms instead of forcing one type. |

## Compatibility and migration

Schema v1.4 is a breaking schema release. Records using the v1.3 field
`variables[].axis_assignments` must rename it to
`variables[].multi_axis_assignments`. Values `x_axis` and `y_axis` must move
from `variables[].analytical_roles` to `variables[].axis_roles`. Other approved
changes refine definitions and examples without changing field shapes.

The active extraction wrapper now identifies its output contract as v1.4 and
uses a new prompt cache key. No extraction run is part of this change. Existing
v1.3 outputs are historical records and are not migrated automatically.

## Deferred normalization work

Schema v1.4 continues to validate local enums, code syntax, and cross-field
relationships. It does not verify external registry membership or perform
deterministic post-extraction normalization. A later pipeline stage may resolve
aliases against pinned reference data, preserve unresolved input, record the
normalization result, and route ambiguous or rejected values for review.
