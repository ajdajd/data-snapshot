# Metadata Extraction v1.3 Calibration Laboratory Notebook

## Protocol

The calibration series tests prompt treatments for image-only Schema v1.3
metadata extraction. Each experiment uses the same six snapshots: one figure and
one table from each source. C0-C4 use GPT-5.6 Luna at medium reasoning effort on
the Flex service tier. C5 varies reasoning effort. The production Pydantic output
contract and all other request settings remain fixed unless an experiment entry
explicitly says otherwise.

The existing Calibration0 run is the baseline (`C0`). `C0R` repeats that request
unchanged to measure run-to-run variation before prompt treatments begin. Later
experiments are run only after the preceding result is reviewed.

API cost is estimated from response usage using the
[GPT-5.6 Luna Flex rates](https://developers.openai.com/api/docs/pricing) in effect
on 2026-09-11: $0.10/M uncached input tokens, $0.01/M cached input tokens,
$0.125/M cache-write tokens, and $0.60/M output tokens. The cumulative calibration
guardrail is $5.00, including C0.

## Fixed snapshots

| Source | Type | Snapshot path |
| --- | --- | --- |
| prwp | figure | `prwp/figure/document_11174028_figure_002.png` |
| prwp | table | `prwp/table/document_11174028_table_007.png` |
| refugee | figure | `refugee/figure/027_Jordan-Emergency-Food-Security-Project_figure_000.png` |
| refugee | table | `refugee/table/001_BOSIB-3f2311b3-9a20-44d3-b637-b3b2b3d21695_table_008.png` |
| unhcr | figure | `unhcr/figure/impact_lby_so_refugees_and_migrants_access_to_food_wash_shelter_november_2018_figure_007.png` |
| unhcr | table | `unhcr/table/rpublique_dmocratique_du_congo_-_points_saillants_de_protection_-_aot_2024_table_000.png` |

Paths are relative to `notebooks/metadata_extraction/data/snapshots/`. The runner
passes only each image to the extractor. Source, type, path, and filename are
written to the local result record after the API call and are not model evidence.

## Cost ledger

| Experiment | Treatment | Successes | Errors | Estimated cost | Cumulative cost | Status |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| C0 | Existing production prompt | 6 | 0 | $0.007329 | $0.007329 | Complete |
| C0R | Unchanged repeat baseline | 6 | 0 | $0.008586 | $0.015915 | Complete |
| C1 | OpenAI-compatible schema duplicated in prompt | 6 | 0 | $0.017497 | $0.033411 | Complete |
| C1A | Canonical Pydantic schema with examples duplicated in prompt | 6 | 0 | $0.026214 | $0.059625 | Complete |
| C2 | Selected schema reference plus boundary rules | 6 | 0 | $0.017841 | $0.077466 | Complete |
| C3 | C2 treatment plus curated examples | 6 | 0 | $0.017999 | $0.095465 | Complete |
| C4 | Repeat of the strongest treatment | 6 | 0 | $0.006632 | $0.102097 | Complete |
| C5L | C2 prompt at low effort | 5 | 1 | $0.017163 | $0.119260 | Complete |
| C5H | C2 prompt at high effort | 6 | 0 | $0.027155 | $0.146415 | Complete |
| C5X-8k | Initial xhigh run with binding output ceiling | 3 | 3 | $0.037980 | $0.184395 | Confounded pilot |
| C5X | C2 prompt at xhigh effort with 32k ceiling | 6 | 0 | $0.028606 | $0.213002 | Complete |

`calibration0_errors.jsonl` also preserves six preflight failures generated before
the extractor fixes. Those records have no API usage and cost $0; the completed C0
run itself contains six successful calls. C0R through C4 produced no error records.

## Experiment C0R: repeat baseline

### Purpose

Measure natural output variation using the exact C0 snapshots and production
request. This gives later prompt comparisons a baseline for interpreting changes.

### Controlled settings

- Model: `gpt-5.6-luna`
- Reasoning effort: `medium`
- Service tier: `flex`
- Prompt cache key: `metadata-extraction-v1-3`
- Output contract: runtime Schema v1.3 Pydantic JSON Schema
- System and user prompts: unchanged production files
- Source-document metadata: not supplied
- Results: `outputs/calibration0_repeat_results.jsonl`
- Errors: `outputs/calibration0_repeat_errors.jsonl`

### Results

C0R completed all six calls without an extraction or validation error. It cost
$0.008586125, or approximately $0.001431 per snapshot. Together, C0 and C0R cost
$0.015914650.

| Usage | C0 | C0R | Difference |
| --- | ---: | ---: | ---: |
| Input tokens | 63,058 | 63,058 | 0 |
| Cached input tokens | 41,745 | 41,745 | 0 |
| Cache-write tokens | 21,295 | 21,295 | 0 |
| Output tokens | 7,079 | 9,175 | +2,096 |
| Reasoning tokens | 3,804 | 5,227 | +1,423 |
| Estimated cost | $0.007329 | $0.008586 | +$0.001258 |

The identical input and cache-token counts support that the fixed request inputs
were preserved. C0R cost 17.2% more than C0 because it produced 29.6% more output
tokens; input cost did not change.

### Paired qualitative review

The two valid outputs were not semantically identical for any of the six
snapshots. Five titles were identical. The sixth changed from `Respondents’ shelter
types` to the more source-faithful `Figure 9: Respondents’ shelter types`.

C0R was often richer in visibly supported metadata:

- It captured the Epanechnikov kernel, degree, bandwidth, and pwidth shown in the
  PRWP figure.
- It represented the PDO outcome headings as category groups rather than only a
  flat outcome list.
- It captured both provinces and their displayed territories in the UNHCR table,
  and normalized its visible month to `2024-08`.
- It represented `World Bank calculations` as an attribution alongside the
  `2017-18 HEIS` source, rather than duplicating the entire source line as an
  interpretive note.

C0R also exposed unresolved boundary choices rather than dominating C0 uniformly:

- In the PRWP regression table it omitted the visible `Estimated Effects` panel
  title and did not retain `Early onset` and `Late onset` as a dimension, although
  it improved attachment of coefficient and standard-error forms to variables.
- The Jordan density-plot y variable changed from `Density` to `Density:Kernel`;
  neither output preserved the source-visible axis wording exactly.
- Subject-domain wording and the placement of some visible text among subject,
  method, provenance, and interpretive-note fields varied across the pair.

The practical conclusion is that natural run-to-run variation is material at
medium effort. Later prompt treatments should be judged against both C0 and C0R
using explicit evidence-boundary and field-placement criteria, not by exact JSON
agreement or by treating either single baseline output as ground truth.

### Run identity

- Repository commit before the run: `a2c7149e3418f785fb73f0599b42d35a24ca5e56`
- Config SHA-256: `46ce14f163751b1e61b2e60468d74f06acb32d63b6632051de817d833aa5cfd6`
- System prompt SHA-256: `e865057c10b5e4d19d89e3de5565ebc7f738e54db2255e92241284b4b4bbee42`
- User prompt SHA-256: `c0899f27c3359101ac6f626205b33d788b53dae5996f468322e96fb83864bd06`
- Runtime response-schema SHA-256: `36b12d0e2a7d7f518ad1ead8f84865cc44d6b94496210ec48bd8a46220fb0d4a`

## Remaining experiment sequence

### C1: duplicate the model-facing schema

Append the exact OpenAI-compatible JSON Schema used as the response contract to
the user prompt. This schema retains field descriptions and validation rules but
does not contain the Pydantic `examples` metadata removed for Structured Outputs
compatibility. The production prompt files and response contract remain unchanged.

- Results: `outputs/calibration1_results.jsonl`
- Errors: `outputs/calibration1_errors.jsonl`

#### Results

C1 completed six valid calls for $0.017496590. It used 149,002 input tokens and
7,721 output tokens. The larger prompt made C1 approximately twice as expensive
as C0R.

Restating the model-facing schema did not show a clear qualitative improvement
over C0R. It lost several useful assignments, including both figure document
labels, the PDO outcome category grouping, detailed geographic locations in the
UNHCR table, and the attribution/source distinction for `World Bank calculations`.
It improved some isolated details, such as expressing the national poverty line
as a comparison, but also duplicated the corresponding source line between
provenance and interpretive notes. C1 is therefore not the current leading
treatment. This outcome strengthens the rationale for testing whether the
canonical examples in C1A supply guidance absent from the compatible schema.

### C1A branch: duplicate the canonical schema with examples

Append the canonical Pydantic validation schema, including `examples`, to the user
prompt while keeping the OpenAI-compatible schema as the authoritative response
contract. C0/C0R showed material variation in exactly the kinds of field boundaries
illustrated by the examples, so the examples branch is warranted.

- Results: `outputs/calibration1a_results.jsonl`
- Errors: `outputs/calibration1a_errors.jsonl`

#### Results

C1A completed six valid calls for $0.026213540, bringing cumulative spend to
$0.059624780. It used 219,640 input tokens and 7,533 output tokens.

The canonical examples changed several structural choices but did not improve
quality consistently. Positive changes included expressing `Baseline vs Closing
Period` as one comparison and treating visible violation headings as dimension
categories in the UNHCR table. Negative changes included treating `residuals`,
`deviation`, and `Persons` as unsupported units, losing the visible `95% CI` as a
statistical form, and representing regression predictors as row categories while
making coefficient and standard error standalone variables. C1A is not the current
leading treatment.

### C2: add field-boundary rules

Select the stronger C1 schema treatment by paired visual review, then add concise
rules for recurring ambiguities: variables versus dimensions, qualifier ownership,
comparisons, panels, provenance, temporal and geographic coverage, and exact
`source_text`. Record the selected C1 branch before running C2.

**Selection:** C2 uses C1's OpenAI-compatible schema reference. C1A did not show a
consistent quality gain and cost 49.8% more than C1. C2's explicit boundary rules
target the useful C1A changes without carrying the full canonical example payload.

#### Results

C2 completed six valid calls for $0.017840990, bringing cumulative spend to
$0.077465770. It used 151,114 input tokens and 7,855 output tokens. The boundary
guidance added only $0.000344 relative to C1.

C2 corrected most targeted issues: it restored all visible figure labels, attached
coefficient and standard-error forms to measured variables, represented comparative
relationships coherently, retained applicable temporal coverage, and separated the
Jordan survey source from the World Bank attribution without duplicating the source
line. It also preserved category groups in the UNHCR table.

Remaining issues were narrower. One methodological note transcribed `pwidth` as
`pwdth`; the UNHCR geographic `source_text` shortened the visible province wording;
and `monitoring de protection` remained only in an interpretive note rather than
provenance. The distinction between column measures and category dimensions also
remained sensitive to the table layout. C2 is the current leading treatment.

### C3: add curated examples

Add a small set of generic positive and negative examples to the C2 treatment.
Examples must illustrate general schema boundaries without reproducing the six
calibration snapshots.

**Examples selected before execution:** regression-variable qualifier ownership,
grouped rows in a table, dataset-versus-agent provenance, inferred visualization
type without manufactured source text, and panels versus ordinary table sections.

#### Results

C3 completed six valid calls for $0.017999390, bringing cumulative spend to
$0.095465160. It used 153,082 input tokens and 7,709 output tokens. The curated
examples added only $0.000158 relative to C2.

C3 improved some details: it corrected `pwidth`, retained predictor roles in the
regression table, deterministically normalized `2017-18`, and preserved complete
visible province and territory wording. It was not a consistent improvement. It
duplicated the same method statement between analysis methods and interpretive
notes, weakened the regression lag dimensions, omitted a visible currency, merged
the distinct `Total` and `%` columns, and still did not place `monitoring de
protection` in provenance. C2 remains the leading treatment.

### C4: confirmation repeat

Repeat the strongest treatment selected from C1, C1A, C2, and C3 without changing
its prompt. C4 measures whether the apparent improvement survives normal model
variation.

**Selection:** C4 repeats C2 byte-for-byte. C2 had the strongest overall field
placement and evidence fidelity; C3's examples traded several improvements for new
structural errors.

#### Results

C4 completed six valid calls for $0.006631960, bringing then-current spend to
$0.102097120. It used the same 151,114 input tokens as C2, but 151,096 were cached
and none were cache writes. It produced 8,532 output tokens. The warm prompt cache
made C4 62.8% cheaper than the initial C2 run.

C4 confirmed several useful C2 tendencies: all visible figure and table labels were
retained, the central variable/qualifier assignments were generally coherent, and
the principal comparison relationships remained represented. However, none of the
six C4 records exactly matched C2. C4 again treated table section headings as panel
titles, moved `World Bank calculations` from attribution to source, duplicated
territory categories alongside their category groups, and omitted or weakened some
currency, percentage, and normalized temporal details.

## C0-C4 prompt-treatment conclusion

C2 is the preferred prompt treatment for the next evaluation stage. The experiment
series does not support duplicating the schema by itself, using the full canonical
example payload, or retaining the C3 generic examples:

- C1 increased cost without a clear quality gain.
- C1A was the most expensive treatment and introduced several example-driven field
  placement errors.
- C2's concise boundary guidance produced the strongest overall result at almost the
  same initial cost as C1.
- C3 fixed isolated details but introduced new structural errors.
- C4 confirmed that C2 improves important tendencies but does not eliminate normal
  output variation at medium reasoning effort.

The evidence supports using C2 as a candidate production prompt, not treating any
single result as ground truth. C5 therefore holds the C2 treatment fixed while
varying reasoning effort.

## Final cost summary

| Experiment | Estimated cost |
| --- | ---: |
| C0 | $0.007328525 |
| C0R | $0.008586125 |
| C1 | $0.017496590 |
| C1A | $0.026213540 |
| C2 | $0.017840990 |
| C3 | $0.017999390 |
| C4 | $0.006631960 |
| C5L | $0.017163125 |
| C5H | $0.027154925 |
| C5X-8k confounded pilot | $0.037980125 |
| C5X corrected | $0.028606360 |
| **Total** | **$0.213001655** |

C2 and C4 used identical runner-generated prompt text, verified immediately before
C4 execution. Their matching 151,114 input-token totals provide an independent
run-level check that the request inputs were unchanged.

## C5: reasoning-effort cost-benefit experiment

### Design

C5 compares GPT-5.6 Luna at `low`, `medium`, `high`, and `xhigh` reasoning effort.
All levels use the same six images, C2 prompt, Pydantic response contract, Flex
service tier, prompt cache key, and timeout. Low, medium, and high use the original
8,000-token output ceiling. Corrected xhigh uses 32,000 because the API counts both
reasoning and visible output against this ceiling; all lower levels stayed below
8,000. GPT-5.6 Luna supports up to 128,000 output tokens according to the
[model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-luna).

- C5L: new low-effort run; `outputs/calibration5_low_results.jsonl`
- C5M: reuse C2 and C4 as the two existing medium-effort replicates
- C5H: new high-effort run; `outputs/calibration5_high_results.jsonl`
- C5X: new xhigh-effort run; `outputs/calibration5_xhigh_32k_results.jsonl`

C2 is the primary production-like medium cost reference because each image was a
new request under that prompt. C4 provides a second medium quality observation and
an exact-request warm-cache lower bound, not a realistic full-run estimate for
different images. Because the other levels have one valid run each, quality
differences remain calibration evidence rather than precise performance estimates.

### Preregistered review rubric

Each of the following 18 checks receives 1 for materially correct, 0.5 for partial
or minor error, and 0 for missing, unsupported, or materially misplaced metadata.
The maximum score is 18.

| Snapshot | Check 1 | Check 2 | Check 3 |
| --- | --- | --- | --- |
| PRWP figure | Complete title, label, and visible panel heading | Correct axes and attached confidence interval | Exact method parameters and fixed-effects note without harmful duplication |
| PRWP table | Outcome, predictors, coefficient, and standard-error ownership | Separate lag-specification, lag-period, and onset-timing structure | Preserve the visible note without false panel or provenance assignments |
| Refugee figure | Identity, subject, geography, and represented period | Correct axes, unit, and visible currency | Poverty-line comparison and survey-versus-agent provenance |
| Refugee table | Complete indicators with applicable units and statistical forms | PDO grouping and reporting-period structure | Baseline/closing comparison and represented temporal bounds |
| UNHCR figure | Complete title and document label | Respondent measure and shelter-type categories | No unsupported metadata or manufactured source text |
| UNHCR table | Subject and represented month | Exact province/territory grouping and geographic roles | Count/percentage structure plus monitoring provenance and substantive note |

Cost-benefit reporting will include total and per-snapshot cost, total and reasoning
tokens, elapsed time, rubric score, and cost per rubric point. The preferred level
must offer a material quality benefit; a numerically higher effort is not presumed
better.

### Results

#### C5L: low

C5L completed five valid extractions and one Pydantic validation failure for
$0.017163125, bringing cumulative calibration spend to $0.119260245. The invalid
record used `relation="point"` with both `start` and `end` for the same month;
Schema v1.3 requires a point period to contain `start` only. The failed call remains
part of C5L's cost and reliability result. It was not retried because the design is
one first-pass call per snapshot.

#### C5H: high

C5H completed six valid extractions for $0.027154925, bringing cumulative
calibration spend to $0.146415170.

#### C5X output-budget correction

The initial xhigh run used the common 8,000-token output ceiling. Its three figure
requests completed, but all three table requests exhausted the ceiling entirely on
reasoning tokens before producing structured output. Because `max_output_tokens`
includes reasoning and visible output, this run cannot support an inference about
xhigh reliability or cost-benefit. Its artifacts are preserved as
`outputs/calibration5_xhigh_results.jsonl` and
`outputs/calibration5_xhigh_errors.jsonl`, and its $0.037980125 cost remains in the
cumulative ledger.

The corrected C5X run raises only xhigh's ceiling to 32,000 tokens. Low, medium,
and high did not approach 8,000 tokens, so they do not require reruns. The prompt,
schema, six images, model, service tier, and all other request settings remain
fixed.

Corrected C5X completed six valid extractions for $0.028606360, bringing total
calibration spend, including the confounded pilot, to $0.213001655. This confirms
that the three pilot failures were caused by the binding output budget. The
[Responses API reference](https://developers.openai.com/api/reference/python/resources/responses/methods/create)
defines `max_output_tokens` as the combined ceiling for reasoning and visible
output tokens.

### Usage, latency, and observed cost

Every valid C5 comparison row used 151,114 input tokens across the same six
requests. Output usage, latency, and prompt-cache state differed.

| Effort/run | Valid | Output tokens | Reasoning tokens | Mean seconds/snapshot | Observed cost | Cost/snapshot |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Low | 5/6 | 5,125 | 1,359 | 15.6 | $0.017163 | $0.002861 |
| Medium C2 | 6/6 | 7,855 | 4,485 | 36.5 | $0.017841 | $0.002973 |
| Medium C4 | 6/6 | 8,532 | 4,982 | 44.4 | $0.006632 | $0.001105 |
| High | 6/6 | 21,778 | 18,192 | 60.2 | $0.027155 | $0.004526 |
| Xhigh, corrected | 6/6 | 45,156 | 41,015 | 103.9 | $0.028606 | $0.004768 |

The observed C4 and corrected-xhigh costs are unusually low because each reused
the exact prompt-image requests from an immediately preceding run: 151,096 of
151,114 input tokens were cached. C2, low, and high are more representative of
processing different images. Low and high had the same input-cost profile; their
cost difference came entirely from output tokens. Corrected xhigh's observed cost
therefore should not be compared directly with high without adjusting for cache
state.

### Rubric results

A failed extraction receives zero for that snapshot's three checks. The scores
below are bounded human review of these six images, not a population accuracy
estimate.

| Effort/run | PRWP fig. | PRWP table | Refugee fig. | Refugee table | UNHCR fig. | UNHCR table | Total/18 | Observed cost/point |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Low | 3.0 | 2.5 | 2.0 | 3.0 | 3.0 | 0.0 | 13.5 | $0.001271 |
| Medium C2 | 2.5 | 2.0 | 3.0 | 2.5 | 3.0 | 2.5 | 15.5 | $0.001151 |
| Medium C4 | 2.5 | 2.5 | 2.0 | 3.0 | 3.0 | 2.0 | 15.0 | $0.000442 |
| High | 2.5 | 2.5 | 3.0 | 2.0 | 3.0 | 1.5 | 14.5 | $0.001873 |
| Xhigh, corrected | 2.5 | 3.0 | 3.0 | 2.5 | 3.0 | 2.0 | 16.0 | $0.001788 |

The principal score deductions were:

- Low produced strong valid table structure but failed Schema v1.3 validation for
  the UNHCR table and omitted the Jordan figure's y variable and attribution role.
- Medium C2 misspelled `pwidth`, combined lag specification and lag period, and did
  not group PDO indicators under outcome headings. C4 repaired some of these but
  introduced false table panels and weaker currency, attribution, and UNHCR
  percentage handling.
- High did not improve on medium overall. It omitted predictor roles in the PRWP
  table, flattened the PDO grouping, and weakened UNHCR geographic and temporal
  semantics.
- Xhigh gave the strongest PRWP table and the most complete UNHCR geography and
  provenance. Its remaining issues included omitting the PRWP figure's panel
  heading, not storing PDO count/percentage forms as units, omitting the UNHCR
  `Total` count variable, and inferring day-level bounds from a month-only label.

### Production-like cost projection

The extraction corpus contains 102 snapshots: 17 in each source/type stratum. The
projection below scales the six-image sample by 17. It uses the observed
partial-cache/new-image input cost rather than the exact-image cache hits in C4 and
corrected C5X. Medium is a range based on the C2 and C4 output-token totals.

| Effort | Approx. cost/snapshot | Projected 102-snapshot cost |
| --- | ---: | ---: |
| Low | $0.00286 | $0.29 |
| Medium | $0.00297-$0.00320 | $0.30-$0.33 |
| High | $0.00453 | $0.46 |
| Xhigh | $0.00686 | $0.70 |

These are estimates for similarly sized images and outputs, not billing guarantees.
The exact-repeat cache lower bound is substantially cheaper, but it is not expected
when every production snapshot is different.

### C5 conclusion

Medium remains the recommended production reasoning effort. It produced six valid
records in both runs and scored 15.0-15.5. Low saved only about 4-11% under the
production-like projection, scored lower, and failed one first-pass validation.
High was slower and more expensive without a quality gain over medium.

Corrected xhigh achieved the best single score, 16.0, but the 0.5-point gain over
the best medium run is within the scale of the 0.5-point medium replicate variation.
It used 8.2 times as many reasoning tokens as C4, took 2.3-2.8 times as long per
snapshot, and is projected to cost about 2.1-2.3 times as much on unseen images.
That is not yet a material enough quality benefit for the full run. Xhigh remains a
reasonable targeted second pass for difficult snapshots if later validation shows
a specific medium-effort failure pattern.

## C7-C8: schema-example visibility and completeness instructions

### Motivation

The production adapter removes Pydantic `examples` because they are not part of the
OpenAI-compatible response schema. C1A exposed the complete canonical schema and
examples as a separate JSON prompt block, but did not attach examples to field
descriptions in the authoritative response contract. C7 and C7A test whether
placing examples directly beside their field definitions changes extraction
behavior without editing the canonical Pydantic models.

The production results also showed repeated omission of supported normalization
fields and `axis_assignments`. C8, C8A, and C8B hold the schema fixed and compare
three short system-level completeness instructions: explicit field-by-field
traversal, an outcome-first success criterion, and a final schema re-scan.

### Fixed conditions and cost guardrail

All experiments use GPT-5.6 Luna, medium reasoning, Flex service tier, the
production evidence and field-boundary prompts, and the same 12 batch-1 snapshots.
The treatments do not receive filename, directory, or source-document metadata.
Results and errors are written to separate JSONL files and remain resumable. The
runner checks cumulative recorded calibration spend before every request and stops
at the approved $5 limit.

The 12 images were chosen from batch 1 before any C7-C8 calls by inspecting the
images for assessable opportunities. They cover UN/CEFACT unit codes, ISO 4217
currency codes, SDMX unit multipliers, ISO 3166-1 alpha-3 country codes, one
explicit left/right dual-axis chart, and negative controls where normalization or
axis assignments should remain absent.

| Source | Type | Snapshot |
| --- | --- | --- |
| PRWP | Figure | `document_11958451_figure_004.png` |
| PRWP | Figure | `document_14861148_figure_004.png` |
| PRWP | Table | `document_437268_table_005.png` |
| PRWP | Table | `document_14861148_table_002.png` |
| Refugee | Figure | `189_multi-page_figure_001.png` |
| Refugee | Figure | `196_multi-page_figure_001.png` |
| Refugee | Figure | `197_multi-page_figure_000.png` |
| Refugee | Table | `060_Yemen-Emergency-COVID-19-Project_table_003.png` |
| UNHCR | Figure | `education_underattack_updatesept23_figure_003.png` |
| UNHCR | Figure | `rbsa_population_data_analysis_sep_2022_figure_009.png` |
| UNHCR | Table | `pays_cotiers_-_aperu-en_31_july_2022_v2_table_001.png` |
| UNHCR | Table | `unhcr_global_report_2020_-_east_and_horn_of_africa_and_the_great_lakes_table_002.png` |

### Treatments

| Experiment | Treatment | Results |
| --- | --- | --- |
| C7 | Append the first canonical example to each associated schema description | `outputs/calibration7_results.jsonl` |
| C7A | Append the complete canonical examples list to each associated schema description | `outputs/calibration7a_results.jsonl` |
| C7B | Append complete examples only to selected normalization-field descriptions | `outputs/calibration7b_results.jsonl` |
| C8 | “Go through all fields in the schema one by one. Populate every field supported by visible evidence, and leave every unsupported field null.” | `outputs/calibration8_results.jsonl` |
| C8A | “Populate every schema field supported by visible evidence. Success means that no supported field is omitted and every unsupported field is null.” | `outputs/calibration8a_results.jsonl` |
| C8B | “Before returning, re-scan the image against the entire schema and correct any omissions of fields supported by visible evidence. Leave every unsupported field null.” | `outputs/calibration8b_results.jsonl` |

The existing `batch1_results.jsonl` records are the no-treatment production
baseline for the same images. Reviewer-generated records labeled as `gold` are
excluded: they are not treated as ground truth, and confidence in their true- and
false-negative classifications is currently limited. Findings below are therefore
bounded, image-based human judgments about visible opportunities and regressions.
C7B was conditional on a useful but mixed C7/C7A result. That condition was met,
so the normalization-only branch was run. A combined schema-example and
completeness treatment remains deferred because the individual example branches
did not establish a clean benefit.

### Results

#### C7: first example per field

C7 completed all 12 snapshots successfully for **$0.045027030**, bringing
cumulative recorded calibration spend to **$0.314012695**. Relative to the
no-treatment batch-1 records, attaching one example produced only a narrow gain in
the targeted normalization fields: it added the valid percent unit code `P1` to
two variables in `document_14861148_table_002.png`. It did not add the expected
ISO country codes, USD codes, unit multipliers, or left/right assignments in the
other assessable images. Several non-target fields also varied in both directions,
including omitted geography and changed variable decomposition. Because this is a
single nondeterministic replicate, those differences are signals rather than
attributable effects. The initial result does not support adopting first-example
augmentation by itself.

#### C7A: all examples per field

C7A completed all 12 snapshots successfully for **$0.050744370**, bringing
cumulative recorded calibration spend to **$0.364757065**. Unlike C7, it produced
a large normalization response: 37 populated unit multipliers and 60 currency
codes across the selected records, including multiplier 6 for visible millions
and `USD` for visible US-dollar expressions. It still produced no ISO alpha-3
country codes and no UN/CEFACT unit codes in this replicate.

The gain came with a material boundary warning. C7A added five `axis_assignments`
to an at-a-glance composite even though those assignments describe separate or
shared-axis panels rather than distinct axes of the same graph. It also propagated
`USD` and multiplier 6 broadly across a dense page, increasing the need for
variable-by-variable visual review. Thus all-example augmentation appears much
more behaviorally potent than first-example augmentation, but the current result
does not establish that its added fields are uniformly precise. It is a plausible
motivation for a narrower C7B treatment if the instruction-only experiments cannot
recover normalization without this overpopulation tendency.

#### C8: direct field-by-field traversal

C8 completed all 12 snapshots successfully for **$0.044734425**, bringing
cumulative recorded calibration spend to **$0.409491490**. The instruction
recovered all six expected left/right assignments in the explicit dual-axis PRWP
chart. It also populated five assessable multipliers and 35 currency codes,
including billion-scale exponent 9 and million-scale exponent 6. This shows that
the model can produce several normalization fields without receiving schema
examples when prompted to check field coverage explicitly.

However, C8 still produced no ISO alpha-3 country codes or UN/CEFACT unit codes.
It also added four inappropriate x/y assignments to grouped panels in the Rwanda
at-a-glance composite, where `axis_assignments` should be reserved for distinct
axes within the same graph. The direct traversal wording therefore improved the
intended dual-axis case but also encouraged some unsupported structural filling.

#### C8A: outcome-first success criterion

C8A completed all 12 snapshots successfully for **$0.045351955**, bringing
cumulative recorded calibration spend to **$0.454843445**. It was more
conservative than C8: no `axis_assignments` were populated, so it avoided C8's
composite-page overassignment but also missed the explicit PRWP dual-axis case.
It populated three million-scale multipliers and 12 currency codes, while again
producing no ISO alpha-3 or UN/CEFACT unit codes. The result does not show that the
abstract success criterion reliably induces a full schema traversal; its
conservatism traded away a clearly supported target field.

#### C8B: final schema re-scan

C8B completed all 12 snapshots successfully for **$0.043227330**, bringing
cumulative recorded calibration spend to **$0.498070775**. Like C8, it recovered
all six expected left/right assignments in the explicit dual-axis chart. It
populated six million-scale multipliers and four currency codes, but no ISO
alpha-3 or UN/CEFACT unit codes. It also added five unsupported axis assignments:
four in the Rwanda at-a-glance composite and one in a simple UNHCR chart. The
final re-scan wording therefore retained C8's positive dual-axis behavior but
showed a stronger unsupported-axis tendency and weaker currency normalization.

#### C7B: normalization-only examples

The mixed C7A result triggered the planned conditional branch. C7B appended the
complete examples list only to `Unit.code`, `Unit.multiplier_exponent`,
`Currency.code`, and the `iso3_code` fields on places. It did not expose examples
on axis assignments or unrelated fields. C7B completed all 12 snapshots
successfully for **$0.043113730**, bringing cumulative recorded calibration spend
to **$0.541184505**.

C7B populated 11 multipliers and eight currency codes, a smaller and less diffuse
normalization response than C7A. It still produced no ISO alpha-3 or UN/CEFACT
unit codes, missed the explicit dual-axis chart, and added one unsupported y-axis
assignment to a simple chart. Narrowing the examples reduced C7A's structural
pressure but did not solve the originally reported omissions.

### Original aggregate comparison (all 12 images)

All six runs returned 12 Schema v1.3-valid records. The counts below are raw
populated-field counts, not precision or recall scores. They are sensitive to each
run's variable decomposition, especially on dense at-a-glance pages. The two axis
columns instead apply the schema boundary directly to the deliberately selected
charts.

This table is retained as the chronological record of the first analysis. Its
interpretation is superseded below by the review-oriented split, which excludes
at-a-glance composites and evaluates C8x for coverage and C7x for quality.

| Run | Unit codes | Multipliers | Currency codes | ISO3 codes | Supported dual-axis assignments | Unsupported axis assignments | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Batch-1 baseline | 0 | 0 | 4 | 0 | 0 | 2 | n/a |
| C7, first example | 2 | 0 | 1 | 0 | 0 | 0 | $0.045027030 |
| C7A, all examples | 0 | 37 | 60 | 0 | 0 | 5 | $0.050744370 |
| C7B, normalization examples | 0 | 11 | 8 | 0 | 0 | 1 | $0.043113730 |
| C8, direct traversal | 0 | 5 | 35 | 0 | 6 | 4 | $0.044734425 |
| C8A, success criterion | 0 | 3 | 12 | 0 | 0 | 0 | $0.045351955 |
| C8B, final re-scan | 0 | 6 | 4 | 0 | 6 | 5 | $0.043227330 |

| Run | Input tokens | Output tokens | Reasoning tokens | Mean latency |
| --- | ---: | ---: | ---: | ---: |
| C7 | 352,033 | 22,543 | 11,438 | 20.32 s |
| C7A | 411,577 | 24,904 | 10,407 | 18.37 s |
| C7B | 321,373 | 23,043 | 9,611 | 15.62 s |
| C8 | 320,041 | 25,931 | 8,818 | 17.74 s |
| C8A | 320,017 | 26,961 | 9,777 | 17.13 s |
| C8B | 320,077 | 23,418 | 9,122 | 15.46 s |

The six experiments added **$0.272198840** to the calibration program. The
cumulative recorded total, including earlier experiments, is **$0.541184505**,
well below the approved $5 guardrail. The initial sandboxed C7 attempt recorded 12
zero-token `APIConnectionError` entries before external API access was enabled;
they incurred no estimated cost and are not included in the successful-run table.

### Initial combined conclusion

This conclusion is retained for auditability but is superseded by the reframed
analysis below. It treated coverage and quality as one objective and weighted
overfilling more heavily than is appropriate for the planned manual review.

Do not adopt C7, C7A, or C7B as the production schema treatment. Examples clearly
change model behavior, but one example was too weak, all examples were too broad,
and normalization-only examples still failed to recover country and unit codes.
The example variants also altered variable decomposition enough to complicate
their apparent normalization gains.

C8 is the strongest completeness-instruction candidate in this set. It is the
only wording that combined correct extraction of the explicit dual-axis case with
substantial currency and multiplier completion. C8A was too conservative, while
C8B added more unsupported axes and fewer currency codes. C8 should still be
treated as a calibration finding rather than a general accuracy estimate: it
produced four unsupported assignments on the known difficult at-a-glance page,
and none of the six treatments solved ISO3 or UN/CEFACT unit-code completion.

The next clean experiment, if those remaining normalization fields are important
enough to pursue, is a direct normalization instruction that explicitly names the
four code systems and states that deterministic normalization from visible labels
is allowed. That should be tested separately before combining it with C8. No
canonical Pydantic schema edit is supported by these results; the fields and their
descriptions were already present, and the observed differences came from
model-facing runtime treatments.

### Reframed analysis for the 102-snapshot manual review

#### Decision context

The immediate objective is to create useful first-pass metadata for personal
review of 102 snapshots. In that workflow, a visibly populated but unsupported or
misplaced field is usually easier to find and remove than a missing field is to
notice and reconstruct. Overfilling remains a tracked error, but underfilling is
assigned the greater practical cost at this stage. Precision and recall can be
rebalanced after review produces a trustworthy gold set.

The reviewer-generated records currently labeled `gold` remain excluded from this
analysis. The following three dense country at-a-glance composites are also
excluded from the primary C7x and C8x comparisons because their multiple panels,
shared labels, and dense layout form a distinct extraction problem:

- `refugee/figure/189_multi-page_figure_001.png`
- `refugee/figure/196_multi-page_figure_001.png`
- `refugee/figure/197_multi-page_figure_000.png`

Their outputs are retained, but they do not determine the conclusions below.

#### C8x: supported-field coverage

Because no trusted gold set exists yet, C8x coverage is evaluated only on
predeclared, visibly assessable opportunities in the remaining nine images. Raw
field count is not treated as recall. Each counted addition was checked against
the image and its schema placement.

| High-confidence opportunity | Available | Baseline | C8 | C8A | C8B |
| --- | ---: | ---: | ---: | ---: | ---: |
| Left/right assignments in the explicit dual-axis chart | 6 | 0 | 6 | 0 | 6 |
| Million-scale multipliers on visibly million-denominated variables | 8 | 0 | 3 | 3 | 6 |
| Normalized place names in the provenance-by-host-country table | 7 | 0 | 7 | 0 | 7 |
| Separate `Denar` currency source text on applicable variables | 5 | 0 | 0 | 0 | 5 |
| ISO3 codes for conservative visible country opportunities | 17 | 0 | 0 | 0 | 0 |
| UN/CEFACT percent codes on explicit percentage variables | 7 | 0 | 0 | 0 | 0 |
| ISO 4217 `MKD` codes on explicit denar variables | 5 | 0 | 0 | 0 | 0 |

The multiplier opportunities comprise three loan-series variables in the
dual-axis chart, two denar-million variables in the credit table, and three
dollar-million variables in the Yemen table. The conservative ISO3 set comprises
Russia, Yemen, eight countries explicitly represented in the Central Sahel
legend, and seven fully named countries in the provenance-by-host-country table;
custom abbreviations in the asylum-country chart are not counted.

C8 produced 16 supported additions in these checks: six axis assignments, three
multipliers, and seven normalized place names. No clear overfill was found within
these targeted opportunities. C8A produced only the three Yemen multipliers and
also omitted the education figure's existing geographic coverage, making it too
conservative for the review workflow.

C8B produced 24 supported additions: six axis assignments, six multipliers, seven
normalized place names, and five correctly separated `Denar` currency expressions.
It also produced two conspicuous overfills outside the at-a-glance family: a
left-y assignment on a single-axis education chart and `schools` as an explicit
unit where the chart only names the measured concept. Its use of `Central Sahel`
as geographic-level `source_text` is an additional placement-quality issue. C8B
also omitted the visibly present environmental and social risk variable from the
Yemen table. These issues remain important, but under the current review-cost
preference C8B provides the strongest coverage result, followed by C8; C8A is not
competitive.

Combining C8's initial traversal with C8B's final re-scan is therefore a coherent
next branch. A candidate C8C instruction is:

> Go through all fields in the schema one by one and populate every field supported
> by visible evidence. Leave every unsupported field null. Before returning,
> re-scan the image against the entire schema and correct any supported-field
> omissions. Do not add fields merely for completeness, but when visible evidence
> reasonably supports a field, prefer populating it rather than omitting it.

The final sentence preserves the evidence boundary while still favoring supported
overfill over silent omission. C8C should be judged on the same non-composite,
opportunity-level checks rather than on total populated fields.

#### C7x: metadata quality

C7x is now assessed separately. Its primary question is whether placing examples
beside schema descriptions improves the correctness and usefulness of metadata
that the model returns. Coverage differences are secondary observations. Quality
includes normalization correctness, source fidelity, semantic decomposition,
field placement, relationships among fields, and ease of manual correction.

| Run | Supported quality gains on the nine-image set | Important quality concerns |
| --- | --- | --- |
| C7, first example | Correct `P1` on two percentage variables; corrected the regression-title OCR; detailed six-series decomposition of the dual-axis chart; added normalized place names and provenance/host roles | Dropped visible `t` statistical forms; read `REG5N` as `REGSN`; omitted education geography and donor categories; omitted some useful column content |
| C7A, all examples | Correct million multipliers on the dual-axis and Yemen images; retained regression `t` forms; correctly recovered `REG5N`; added useful region normalization | Added intercept, R-squared, and observation count as measured variables; invented a contiguous temporal `source_text`; flattened useful category grouping; omitted coastal-table geography/count metadata and donor categories; sometimes represented `USD` redundantly as unit and currency |
| C7B, normalization examples | Correct million multipliers and denar currency on the credit table; strongest preservation of donor categories and pillar groups; retained detailed education geography; normalized the Yemen date; remained stable on the simple asylum-country chart | Read `Denar` as `Demar` in the dual-axis chart; added an unsupported single-axis assignment; represented approval date and risk rating as variables in the Yemen table; flattened credit-table grouping; misused geographic-level `source_text`; normalization gains were inconsistent |

On this review-oriented reading, C7B is the most promising quality candidate, not
because it has the most populated normalization fields, but because it generally
retains richer reviewable structure while limiting C7A's broad example pressure.
C7 and C7A each show real local gains, so neither demonstrates that examples are
unhelpful. However, one nondeterministic run per treatment cannot attribute those
differences confidently to the example strategy. The C7x results support further
quality-focused replication rather than a final winner.

#### Potential experiment branches

1. **C8C: traversal plus final re-scan.** Combine C8 and C8B exactly as above and
   evaluate it on the nine non-composite images. This is the primary coverage
   branch.
2. **C8D: explicit normalization checklist.** If C8C still omits ISO3,
   UN/CEFACT, ISO 4217, and SDMX normalization, add a short instruction naming
   those four systems and allowing deterministic normalization from visible
   labels. Keep this separate from C8C initially so its effect is identifiable.
3. **C7 replication branch.** Repeat C7, C7A, and C7B on the same nine images and
   conduct a blinded paired review using a quality rubric with a lower penalty for
   easy-to-delete overfill than for omission or hard-to-detect wrong metadata.
   Replication should precede a new example design because current differences may
   reflect run-to-run variation.
4. **C7C: all examples with an anti-copy boundary.** If C7A's quality gains recur,
   retain all examples but state explicitly that examples are illustrative, never
   defaults, and must not be copied without image support. This tests whether its
   useful detail can be retained while reducing example-driven misplacement.
5. **C7D: selected quality-family examples.** If C7B remains strongest, extend its
   targeted example set one family at a time to variable/dimension structure,
   temporal representation, and geography. This avoids returning immediately to
   examples on every schema field.
6. **Combined production candidate.** Combine the winning C8x coverage treatment
   and winning C7x quality treatment only after both branches have independent
   evidence. Evaluate that combined prompt against the eventual reviewed gold
   set, with the at-a-glance family maintained as a separate challenge set.

## C8x finalization experiments

### Design

The final C8x comparison used the same nine non-composite snapshots and continued
to exclude the three country at-a-glance pages. Reviewer-generated `gold` records
were not consulted. Four runs separated completeness wording from the redundant
schema copy in the user prompt:

- **C8BR:** exact repeat of C8B, including the user-prompt schema copy.
- **C8C:** combined field traversal and final schema re-scan, including the
  user-prompt schema copy.
- **C8D:** exact C8C wording without the user-prompt schema copy.
- **C8E:** exact C8B wording without the user-prompt schema copy. This conditional
  branch was run because C8C and C8D produced a mixed coverage result.
- **C8DR:** follow-up replication of C8D, requested after recognizing that the
  original C8 traversal result and the first combined runs could be separated by
  ordinary run-to-run variation.

In C8D, C8E, and C8DR, the complete strict Pydantic-derived schema remained the
authoritative `text.format` contract. Only its second, token-heavy rendering in
the user message was removed.

### Execution and cost

All five runs completed 9/9 requests without an API error.

| Run | User-prompt schema | Input tokens | Cached input tokens | Output tokens | Reasoning tokens | Mean latency | Experiment cost | Cumulative cost |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C8BR | Yes | 232,162 | 68,504 | 14,461 | 7,240 | 15.49 s | $0.029818215 | $0.571002720 |
| C8C | Yes | 232,540 | 68,840 | 13,791 | 6,870 | 15.44 s | $0.029424825 | $0.600427545 |
| C8D | No | 102,139 | 77,445 | 15,328 | 7,808 | 15.93 s | $0.013057325 | $0.613484870 |
| C8E | No | 101,761 | 77,067 | 16,135 | 8,376 | 16.98 s | $0.013537745 | $0.627022615 |
| C8DR | No | 102,139 | 68,840 | 17,190 | 9,668 | 28.61 s | $0.015164100 | $0.642186715 |

The original four finalization runs added **$0.085838110** to the calibration
program; C8DR added **$0.015164100**, or approximately **$0.001684900** per
snapshot. Removing the user copy reduced experiment cost by approximately 56%
for C8C/C8D and 55% for C8BR/C8E. Final cumulative recorded calibration spend was
**$0.642186715**, below the approved $5 guardrail.

### Coverage and legitimacy review

The same predeclared visible opportunities were checked. Exact counts are useful
but not sufficient: the dual-axis chart can be represented either as six visible
series variables or as two measures crossed with a sector dimension.

| Run | Six explicit-series axis assignments | Million multipliers | Coastal normalized names | Separate Denar source text | Notable additional coverage or concern |
| --- | ---: | ---: | ---: | ---: | --- |
| C8, initial reference | 6 | 3 | 7 | 0 | Retained eight education locations; no asylum locations |
| C8BR | 0 | 2 | 0 | 0 | Two coarser loan/share axis assignments; omitted both selected geographic sets |
| C8C | 0 | 3 | 7 | 0 | No education or asylum geographic coverage |
| C8D | 6 | 0 | 0 | 2 | Added an unsupported duplicate `Total loans` variable/axis; retained asylum geography |
| C8E | 0 | 0 | 7 | 2 | Two supported coarser axis assignments; retained eight education and eight asylum locations |
| C8DR | 0 | 0 | 0 | 0 | Retained eight asylum locations; no education locations; no explicit dual-axis assignments |

C8E supplied the most balanced reviewable record among the finalization runs. Its
two-variable representation of the dual-axis chart is less granular than C8B's
original six-series representation, but it is supported by the image and avoids
C8D's simultaneous aggregate-plus-series duplication. It also retained the
coastal normalized names and both selected geographic location sets. Its visible
weaknesses remain important: it missed all eight million multipliers and all
tested ISO3, UN/CEFACT, and MKD codes, and it treated `schools` as a unit on the
education chart. These omissions are candidates for a later normalization-focused
branch, not evidence that duplicating the complete schema in the user prompt is
helpful.

The large differences between the original C8B run and C8BR, and between C8D and
C8DR, confirm material run-to-run variation. C8DR did not reproduce either the
original C8 traversal run's broad coverage or C8D's axis-assignment behavior. This
does **not** establish that the combined instruction is worse: the experiment
cannot separate treatment effects from nondeterminism with confidence. It only
shows that the hoped-for combined lift has not been replicated. The
schema-duplicated runs likewise did not show a consistent quality or coverage
advantage over their schema-free counterparts, while their token and cost penalty
was large and repeatable.

### Final C8x decision

Provisionally promote the **C8E configuration** for the current review workflow:

1. Keep C8B's concise final schema re-scan instruction in the production system
   prompt.
2. Do not render the schema again in the production user prompt.
3. Continue supplying the complete Pydantic-derived strict schema as the
   authoritative Structured Outputs `text.format` contract.
4. Keep medium reasoning effort, Flex service tier, and prompt caching.

The user-prompt template retains an explicit
`{{MODEL_FACING_SCHEMA_SECTION}}` marker so calibration runs can reproduce the
with-schema treatment without a hidden runtime append. Production replaces the
marker with an empty string. No canonical Pydantic schema change is supported by
these C8x results. C8DR did not provide evidence to replace this provisional
choice. A genuine ranking of traversal, re-scan, and combined wording requires
multiple paired replications or the reviewed 102-snapshot reference set.

## C9x examples experiments

### Preregistered design

C9x evaluates whether exposing canonical Pydantic examples through their
associated field descriptions improves metadata quality on top of the provisional
C8E production configuration. The output schema remains supplied only through
Structured Outputs; it is not duplicated in the user prompt. All runs use medium
reasoning, Flex, prompt caching, and the same nine non-composite snapshots. The
three country at-a-glance pages and reviewer-generated `gold` records remain
outside the primary analysis.

| Run | Examples treatment | Additional instruction |
| --- | --- | --- |
| C9 | None; contemporaneous production control | None |
| C9A | All canonical examples appended as JSON to their field descriptions | None |
| C9B | Same full-example schema as C9A | Examples are illustrative, not defaults; never copy an example without visible evidence |
| C9C | Examples limited to field families showing credible gains in C9A/C9B | Retain the anti-copy instruction only if C9B reduces example-driven errors without erasing gains |

C9C is adaptive but follows a predeclared selection rule: include a field family
only when C9A or C9B shows at least one clear supported quality gain over C9 and
does not introduce unsupported or misplaced values that outweigh that gain. Its
exact selected schema paths and anti-copy choice must be recorded before C9C is
executed.

Primary evaluation concerns metadata quality rather than raw field count:
normalization correctness, source fidelity, variable/dimension decomposition,
field placement and relationships, manual correction effort, and unsupported
additions. Omissions remain more costly than conspicuous overfills for the current
102-snapshot manual-review workflow, but difficult-to-detect wrong values remain
serious.

### C9 through C9B results and C9C selection

All three runs completed 9/9 requests without an API error.

| Run | Input tokens | Cached input tokens | Output tokens | Reasoning tokens | Mean latency | Cost | Cumulative cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C9 | 101,761 | 68,504 | 17,620 | 9,413 | 29.02 s | $0.015413490 | $0.657600205 |
| C9A | 136,258 | 99,168 | 16,261 | 9,556 | 21.50 s | $0.015383855 | $0.672984060 |
| C9B | 136,510 | 99,392 | 15,408 | 8,578 | 25.59 s | $0.014877795 | $0.687861855 |

C9 was a strong contemporaneous control: it recovered all six explicit-series
axis assignments, three Yemen multipliers, two separate Denar currency
expressions, and the eight education and eight asylum locations. It did not add
normalized names to the seven coastal-table locations.

C9A's clearest supported gains were normalized names for all seven coastal
locations and Russia, cleaner grouped-category structure in the credit table, and
a more complete regression-variable rendition that restored `REG4N` and the
visible `t` statistical form while avoiding `Number obs.` as a measured variable.
Its important losses included the detailed six-series axis representation, all
million multipliers, and most education and asylum geographic coverage. It also
added empty dimensions to the Yemen and education records. Full examples therefore
changed behavior but did not provide a general quality improvement.

C9B recovered the two credit-table multipliers, but the anti-copy instruction did
not yield a net safeguard. It omitted all dual-axis assignments, coastal
geography, education locations, and asylum locations, while still adding an
intercept as a measured variable and empty Yemen dimensions. The anti-copy
instruction is therefore excluded from C9C.

Before execution, C9C is fixed to the following example-bearing schema paths:

- `$defs.CategoryGroup.properties.name`
- `$defs.CategoryGroup.properties.categories`
- `$defs.Dimension.properties.category_groups`
- `$defs.GeographicLocation.properties.name`
- `$defs.Place.properties.name`

These paths isolate the two example families with the clearest directly related
gains in C9A: normalized geographic names and grouped-category structure. C9C does
not include normalization-code, unit, currency, temporal, variable, axis, or
statistical-form examples because C9A/C9B did not show a consistent net benefit
that could be attributed to those example families.

### C9C result and C9x conclusion

C9C completed 9/9 requests without an API error.

| Run | Input tokens | Cached input tokens | Output tokens | Reasoning tokens | Mean latency | Cost | Cumulative cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C9C | 102,895 | 69,512 | 14,777 | 8,359 | 26.12 s | $0.013733520 | $0.701595375 |

The targeted treatment reproduced two narrow behaviors related to its selected
example families. It normalized Russia's name, and the credit table represented
the product/activity values only inside the appropriate `NATURAL PERSONS` and
`CORPORATES` category groups instead of also duplicating them as ungrouped
categories. These are legitimate supported improvements.

Those gains did not generalize or outweigh the losses relative to C9. C9C did not
emit normalized names for the seven coastal-table countries; it omitted that
table's geographic coverage entirely. It also omitted all six explicit-series
axis assignments, all three Yemen million multipliers, and all eight asylum
locations. It retained only the two visible education-region labels rather than
C9's eight constituent country locations. In the regression table it emitted the
unsupported transcription `REGSN`, omitted visible `REG4N`, and treated
`Intercept`, `R²`, and `Number obs.` as variables. It preserved the two Denar
currency expressions and correctly emitted the visible `USD` currency code, but
also misplaced `USD` in the UN/CEFACT unit-code field. None of these behaviors is
attributable to the selected examples.

The C9x result is therefore **no examples**. C9A showed that examples can change
schema interpretation and sometimes improve particular records, but C9B did not
make full examples safe and C9C did not make their gains reliable. With one run
per treatment, some differences may be run-to-run variation; the evidence does
not support promoting any example-bearing configuration. Production remains C8E:
medium reasoning, Flex, prompt caching, the concise final schema re-scan, no
user-prompt schema copy, and the example-free Structured Outputs schema.

This conclusion does not claim that canonical Pydantic examples lack value. It
only rejects exposing them to the extractor in the tested forms before the
102-snapshot reviewed reference set exists. A future paired evaluation can revisit
examples against that reference set with replicated runs and field-family-level
scoring.
