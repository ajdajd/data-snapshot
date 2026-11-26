# P1: optional Docling for initial data-model proposals

Protocol frozen before calls, 2026-11-26. User authorized this small experiment
under the existing cumulative $5 workstream budget.

Question: does standard Docling preprocessing improve the initial data model
enough to justify its local processing time? This experiment does not extract
observation values or evaluate a formal SDMX DSD.

- Six existing core examples: income, financing, regression, education, trade,
  duration. These cover simple/hierarchical tables, statistical results and
  multi-panel/unlabelled/multilingual charts.
- A: PNG only. B: same PNG plus freshly generated standard CPU Docling native
  evidence. No chart-enrichment model is used.
- Same Luna medium, 12,000 output-token limit, system/user prompt templates and
  strict working-data-model schema. Optional Docling content is null in A.
  Neither arm receives design sketches, accepted models, correction notes,
  filenames as evidence, other-arm responses or metadata extraction outputs.
- One fresh call per arm/image: 12 calls. Reverse arm order on alternate images.
  No automatic retry, repair or tuning between calls. Invalid outputs and costs
  remain part of the result. Global spending reservations and reported charges
  use the existing ledger, never a reset experiment-specific budget.
- Frozen content/schema/settings hashes and source hashes are in
  `data/structured_data_trials/P1_docling_ab_20261126/manifest.json`.
  `scripts/run_proposal_docling_comparison.py` prepares offline by default;
  `--execute` runs unattempted calls and logs the cumulative spend after each.
  Existing attempts are preserved on resume. Stop on an uncertain charge.

Review each pair against the PNG using the same checklist, allowing multiple
valid component decompositions:

1. Components and identifying categories preserve source coverage.
2. Results preserve numeric/text roles, summaries and specifications.
3. Unit, scale, time and population qualifiers have correct scopes.
4. Hierarchies, totals/exclusions and cross-panel relationships are preserved.
5. Missing information remains unknown; no unsupported factual claims or quotes.

Record concrete substantive corrections before acceptance, remaining questions,
and which arm is preferable or whether neither has a useful advantage. Structural
validation is recorded separately from semantic review. Reviewer findings stay in
this research report/chat, outside the end-user app.

Record input/output/reasoning tokens, reported API cost, LLM wall time and local
Docling conversion time separately. Fresh Docling conversions were sequential in
one process; these are local batch timings, not six independent cold starts.
Image-only avoids Docling time entirely. One call per arm is an MVP decision aid.

## Results

All 12 calls completed, with every charge reported. No repair or retry was run.
Each of the six original PNGs was reopened for the following qualitative review.
Component count alone is not a quality score: both one-component scoped income
and two-component labor-income/remittance designs can be valid.

| Metric, all attempts included | PNG only | PNG + standard Docling |
| --- | ---: | ---: |
| Proposals passing application validation | 5 / 6 | 6 / 6 |
| Reported API cost, six calls | $0.01624410 | $0.02531624 |
| Input tokens | 24,149 | 56,576 |
| Output tokens, including reasoning | 10,564 | 11,780 |
| Median LLM request-stage time | 16.9 s | 21.6 s |
| Median request stage + per-image Docling conversion | 16.9 s | 27.8 s |

Request-stage times include pricing/client/network work and artifact writing;
they are not pure model-generation time. The Docling sum is an approximation of
the sequential application stages, excluding UI and process startup overhead.
CPU Docling conversion took 5.4–19.4 seconds per image. Its model initialization
was included by the extractor, but all six images ran in one process with warm
OS caches. These figures do not measure the heavier chart-enrichment pipeline.
API charges are the provider-reported amounts, including any provider caching.

| Case | PNG-only proposal | With Docling | Review conclusion |
| --- | --- | --- | --- |
| Income | Preserves all eight rows, mean/median and exclusion relationship. Correctly scopes the age/sex note to seven labor-income/total rows. | Uses separate labor-income and remittance components; also scopes population correctly. | Comparable. Both assert monthly wording for remittances without preserving its ambiguity. Scope that context and revise component/result wording before acceptance. |
| Financing | Preserves four rows, US dollars, millions and the IBRD/IDA subset relationship. | Preserves the same structure, using a combined US-dollar/millions unit. | Comparable; no substantive structural correction identified in either. Keeping unit and multiplier separate is a later formalization choice. |
| Regression | Separates coefficients, text-valued specification and numeric firm/survey counts, with result-specific count units. | Separates Manufacturing/Services panels, but represents each combined firm/survey sample description as a text result. Predictor categories also include the specification/sample rows. | PNG-only is more useful for the statistical target. Split the Docling arm's sample description into numeric firm and country-survey results, and clarify which row categories apply to each result type. Neither arm invents numeric standard errors. |
| Education | Raw response preserves both panels, all categories, correct displayed units/period wording, and unknown country-specific years. It labels percent as `kind=scale` without the required numeric-result unit context, so application validation fails. | Preserves both panels and supplies percent as `kind=unit`; keeps the qualified period and country-specific-year question. | Docling arm is usable sooner. The image-only repair is a unit/scale representation correction, not evidence that the LLM missed the printed word Percent. Failed raw output and its charge are retained. |
| Trade | Preserves eight region/aggregate labels, three modes, unknown result unit and printed-only policy. Keeps numbered-mode mapping as an unresolved question. | Preserves the same fields and unknown unit. Proposes mode 1/3/4 mappings as explicitly labeled interpretations, with scoped coverage notes. | Similar structure, different uncertainty treatment. The crop does not explicitly pair mode numbers with legend labels; review those proposed mappings rather than treating them as source-stated facts. No numerical bar values were requested. |
| Duration | Preserves all six Spanish categories, including Toda la vida; percentage unit, unknown denominator and uncertain source-year role are explicit. | Preserves the six labels, percentage unit and source attribution; fewer unresolved-context questions. | Comparable core structure; image-only is more explicit about missing context. Neither proposal creates an observation date from the source's 2023 attribution. |

Evidence cleanup remains separate from statistical structure: several responses
in both arms join noncontiguous legend/category labels into a quoted string. The
regression footnote is also normalized to “cluster-robust” although the printed
fragment uses “cluster robust.” Preserve separate literal fragments or null text
with a visual location. The duration proposals include joined percentage strings
as evidence, rather than a numerical dataset; do not score them as extracted
value/association accuracy. These raw outputs have not been rewritten.

**Decision:** keep Docling available as a user choice, initially unchecked to
favor speed. This sample shows one application-validity benefit and one clearer
statistical structure without Docling, with similar core coverage in the other
examples. It does not establish a consistent improvement from preprocessing.
This is one call per arm/image; numerical extraction quality and behavior on
other images remain untested by P1. Existing fixtures are not numerical gold for
this experiment, and the reviewer was not blinded to the arm.

**Spend:** batch `P1_proposal_docling_ab` cost **$0.04156034**. Previous running
total was **$1.97849147**; new total **$2.02005181 / $5**; remaining
**$2.97994819**, outstanding reservations **$0**.

Artifacts under `data/structured_data_trials/P1_docling_ab_20261126/` include:
frozen manifest/configuration, CPU Docling native outputs and timing reports,
offline request previews, all 12 responses/raw outputs/run reports, console log,
`metrics.json` and `review.json`. The image-only education response remains under
`runs/image_only/education/raw_output.txt`, without a validated proposed model.
No experiment proposal was applied to or accepted in an existing user session.
