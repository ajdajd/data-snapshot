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
