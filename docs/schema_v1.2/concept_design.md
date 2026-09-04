# Data Snapshot Metadata Schema v1.2: Concept Design

Status: Concept design complete; deferred Aivin questions tracked separately
Date: 2026-09-04

## Purpose

This document translates the approved semantic baseline in
[`standards_crosswalk.md`](standards_crosswalk.md) into the v1.2 application
concept design. It records the decisions on field retention, renaming,
definition revision, consolidation, and splitting.

The names and structures below are conceptual design decisions rather than
Pydantic implementation details. Exact types, cardinalities, validators, and
serialization behavior are addressed in subsequent normalization and
implementation work. Questions requiring Aivin's input are tracked in
[`aivin_review.md`](aivin_review.md); until they are resolved, the working
choices recorded here remain the v1.2 baseline.

## Disposition labels

- **Retain**: preserve the current field name and concept.
- **Rename**: preserve the concept under a clearer application-facing name.
- **Fold**: preserve the concept as a facet of a related object or collection.
- **Split**: replace an overloaded concept with two or more explicit semantic
  relations.

## Design principles

1. Preserve the approved information coverage of all 35 concepts.
2. Prefer clear application-facing names over vocabulary-specific names.
3. Introduce an object only when it preserves a meaningful relationship,
   supports normalization, or prevents ambiguity.
4. Retain source-visible labels alongside normalized codes or identifiers.
5. Do not import parent-document metadata into the snapshot model.

## Concept design matrix

The examples are minimal JSON-like fragments showing the change from the flat
v1.1.1 field to the v1.2 representation. They illustrate conceptual
relationships only and do not establish final Pydantic types or cardinalities.
The **Standards basis** column is a concise pointer to the standards concepts
that inform each design direction. Full mappings, relationship classifications,
rationales, and source links remain in
[`standards_crosswalk.md`](standards_crosswalk.md).

### Identity and discovery

| v1.1.1 concept | Disposition | v1.2 location/name | Standards basis | Definition | Minimal example | Design rationale |
|---|---|---|---|---|---|---|
| `title` | Retain | `title` | `dcterms:title`; `schema:name` | The primary title, caption, or heading identifying the data snapshot. | — | Retained without structural change. |
| `internal_identifier` | Rename | `document_label` | JATS `label`; `schema:identifier`; `dcterms:identifier` | The label or identifier assigned to the snapshot within its parent source document, such as “Figure 3” or “Table 4.2.” | — | `document_label` expresses the JATS-like function and avoids implying a globally unique identifier. |
| `subject_domain` | Rename | `subject_domains` | `dcterms:subject`; `schema:about`; DCAT `theme`; SKOS | The broad thematic, policy, or sectoral domains represented by the snapshot, optionally associated with controlled concepts. | `"subject_domain": "Poverty and social; key economic ratios"` → `"subject_domains": ["Poverty and social", "Macroeconomics"]` | The Guinea and Jordan composite calibration snapshots contain multiple coequal broad domains, so a collection is justified. |
| `subject_summary` | Retain | `subject_summary` | `schema:abstract`; `dcterms:description` | A concise summary of the snapshot's primary analytical subject or purpose. | — | Prefer the clear application name; `schema:abstract` can remain an interoperability mapping. |
| `panel_title` | Rename | `panel_titles` | JATS `fig-group` / `fig` / `caption/title`; `schema:hasPart` + `schema:name` | The ordered titles or headings explicitly shown for individual panels in a multi-panel snapshot. | — | Preserves explicitly visible panel headings without introducing panel objects or inferred untitled panels. |

### Subject, dimensions, and presentation

| v1.1.1 concept | Disposition | v1.2 location/name | Standards basis | Definition | Minimal example | Design rationale |
|---|---|---|---|---|---|---|
| `variable_name` | Rename; fold | `variables[].name` | `schema:variableMeasured`; Schema.org `StatisticalVariable`; DDI Variable; SDMX measure concept | The explicitly named variables, indicators, metrics, or measured concepts represented by the snapshot. | `"variable_name": ["Inflation rate"]` → `"variables": [{"name": "Inflation rate"}]` | The variable-centric structure allows a variable to carry its own measurement qualifiers without becoming an extracted observation. |
| `category_dimension` | Fold | `dimensions[].name` | SDMX `Dimension`; DDI `RepresentedVariable`; RDF Data Cube `qb:DimensionProperty` | The conceptual variable used to organize, group, classify, or compare represented values. | `"category_dimension": ["Sex"]` → `"dimensions": [{"name": "Sex"}]` | Each dimension should own its categories and presentation roles. |
| `category_labels` | Fold | `dimensions[].categories` and `dimensions[].category_groups` | SDMX `Code` / `Codelist`; DDI `Category` / `CodeList`; SKOS labels and hierarchical relations | The explicit displayed categories associated with a particular dimension, optionally organized into one broad grouping level and carrying normalized codes or concepts. | `"category_labels": ["Arrestations arbitraires", "Enlèvements"]` → `"dimensions": [{"name": "Incident typology", "presentation_roles": ["column"], "category_groups": [{"name": "Violation du droit à la liberté", "categories": ["Arrestations arbitraires", "Enlèvements"]}]}]` | Preserve ungrouped values in `categories`; use non-recursive `category_groups` only when an explicit two-level grouping is visible. |
| `population_group` | Retain | `population_group` | DDI `Universe`; Schema.org `StatisticalVariable.populationType` | The human population, beneficiary group, or demographic group that is the primary subject of the represented data. | — | Keep distinct from dimensions and categories and represent it as an open controlled term. |
| `row_dimension` | Fold | `dimensions[].presentation_roles` | SDMX `Dimension`; local presentation role | A dimension explicitly assigned to table rows in the snapshot. | `"row_dimension": "Region"` → `"dimensions": [{"name": "Region", "presentation_roles": ["row"]}]` | Use a local `row` role on the relevant dimension rather than duplicating its name. |
| `column_dimension` | Fold | `dimensions[].presentation_roles` | SDMX `Dimension`; local presentation role | A dimension explicitly assigned to table columns in the snapshot. | `"column_dimension": "Year"` → `"dimensions": [{"name": "Year", "presentation_roles": ["column"]}]` | Use a local `column` role on the relevant dimension. |
| `visualization_type` | Rename | `visualization_types` | `dcterms:type`; Schema.org `additionalType`; local SKOS scheme | The explicitly visible visualization forms used by the snapshot, including a combination when a composite has no single adequate type. | — | A controlled collection accommodates composites without creating panel objects. |

### Temporal context

| v1.1.1 concept | Disposition | v1.2 location/name | Standards basis | Definition | Minimal example | Design rationale |
|---|---|---|---|---|---|---|
| `time_period` | Rename; fold | `temporal_coverage.period` | `schema:temporalCoverage`; `dcterms:temporal`; SDMX `TIME_PERIOD`; ISO 8601 | The date, interval, or source expression describing when the represented data apply, excluding artifact and parent-document dates. | `"time_period": "2020–2023"` → `"temporal_coverage": {"period": {"source_text": "2020–2023", "start": "2020", "end": "2023"}}` | Preserve the source expression alongside normalized bounds when deterministic. |
| `temporal_granularity` | Fold | `temporal_coverage.granularity` | SDMX `FREQ` / `CL_FREQ`; DCAT `temporalResolution`; OWL-Time | The temporal resolution or reporting interval of the represented data. | `"temporal_granularity": "Annual"` → `"temporal_coverage": {"granularity": {"source_text": "Annual", "normalized_value": "annual"}}` | Use a normalized value alongside the displayed label; do not equate all granularity with regular frequency. |

### Spatial context

| v1.1.1 concept | Disposition | v1.2 location/name | Standards basis | Definition | Minimal example | Design rationale |
|---|---|---|---|---|---|---|
| `geographic_scope` | Rename; fold | `geographic_coverage.scope` | `schema:spatialCoverage`; `dcterms:spatial`; DCAT spatial coverage | The overall place or geographic area that the snapshot principally covers or concerns. | `"geographic_scope": "Southern Africa"` → `"geographic_coverage": {"scope": {"source_text": "Southern Africa"}}` | The scope summarizes the overall coverage; it need not be repeated in `locations`. |
| `geographic_entities` | Rename; fold | `geographic_coverage.locations[].name` | `schema:spatialCoverage` + `schema:Place`; DDI `GeographicLocation` | Additional named geographic entities explicitly represented within or in relation to the overall coverage. | `"geographic_entities": ["South Sudan", "Uganda"]` → `"geographic_coverage": {"locations": [{"name": "South Sudan"}, {"name": "Uganda"}]}` | Omit `locations` when only the overall scope is named. Each additional location may carry an identifier, type, or role. |
| `geographic_granularity` | Rename; fold | `geographic_coverage.level` | DDI `GeographicLevel`; ISO 3166-2 where applicable | The administrative, geographic, or reporting level at which the snapshot's data are represented. | `"geographic_granularity": "Province"` → `"geographic_coverage": {"scope": "Vietnam", "level": "province"}` | The Vietnam map reports at provincial level without naming each province, so level must be representable at coverage level rather than only on named locations. |
| `geographic_role` | Fold | `geographic_coverage.locations[].role` | Local concept; DDI / IATI / SKOS patterns | The explicit semantic role a geographic entity plays, such as country of origin, country of asylum, or secondary destination. | `"geographic_role": "Country of origin"` → `"locations": [{"name": "South Sudan", "role": "Country of origin"}]` | Preserve a source-grounded role string. An optional mapping may be added when exact, but a closed controlled vocabulary is not required. |
| `location_type` | Fold | `geographic_coverage.locations[].type` | Local concept; IATI `LocationType`; Schema.org `DefinedTerm`; SKOS | The physical or administrative kind of a represented location, such as camp, school, settlement, or district. | `"location_type": "Camp"` → `"locations": [{"name": "Zaatari", "type": "camp"}]` | Use a controlled term capable of carrying a local or external scheme. |

### Measurement and comparison

| v1.1.1 concept | Disposition | v1.2 location/name | Standards basis | Definition | Minimal example | Design rationale |
|---|---|---|---|---|---|---|
| `unit_of_measure` | Retain; fold | `variables[].unit` | SDMX `UNIT_MEASURE`; `schema:unitCode`; UN/CEFACT Recommendation 20 | The unit needed to interpret values for a represented variable, indicator, metric, or measured concept, preserving its displayed label and an optional normalized code. | `"variable_name": "Enrollment", "unit_of_measure": "students"` → `"variables": [{"name": "Enrollment", "unit": {"source_text": "students"}}]` | Variable-centric attachment preserves the relationship between a variable and its unit without introducing a parallel general-purpose `measures` collection. |
| `currency` | Retain; fold | `variables[].currency` | `schema:currency`; ISO 4217; SDMX `CL_CURRENCY` | The currency denomination for monetary values associated with a represented variable, preserving the displayed form and an optional ISO 4217 code. | `"variable_name": "Project cost", "currency": "PHP"` → `"variables": [{"name": "Project cost", "currency": {"source_text": "PHP", "code": "PHP"}}]` | Keep currency semantically separate from unit. The project-specific `financing.measures` concept also remains separate. |
| `measure_type` | Rename; fold | `variables[].statistical_forms` | `schema:statType`; SDMX measure concepts; local vocabulary | The statistical or quantitative forms in which values for a represented variable are expressed, such as count, mean, standard deviation, rate, percentage, or index. | `"measure_type": ["Mean", "Standard deviation"]` → `"variables": [{"name": "Inflation rate", "statistical_forms": ["mean", "standard_deviation"]}]` | Variable-centric attachment preserves the relationship between a variable and its statistical forms. Use a collection because one variable may have multiple forms. |
| `comparison_group` | Rename | `comparisons` | Local concept; DDI comparison structures; `schema:measurementQualifier` (related) | Concise descriptions of explicitly presented comparisons, benchmarks, reference groups, cohorts, scenarios, or entities. | `"comparison_group": "Men vs Women"` → `"comparisons": ["Men vs Women"]` | Keep at snapshot level as source-grounded free text. It may summarize an explicit relationship among categories without being collapsed into the category list. |

### Provenance and attribution

| v1.1.1 concept | Disposition | v1.2 location/name | Standards basis | Definition | Minimal example | Design rationale |
|---|---|---|---|---|---|---|
| `data_source` | Split; fold | `provenance.sources` and `provenance.attributions` | PROV-O `wasDerivedFrom` / `wasAttributedTo`; `dcterms:source`; Schema.org attribution properties | Sources identify entities from which represented data derive; attributions identify agents explicitly credited with producing or contributing to the snapshot artifact. | `"data_source": ["DHS 2022", "Ministry of Health"]` → `"provenance": {"sources": [{"name": "DHS 2022"}], "attributions": [{"name": "Ministry of Health", "role": "producer"}]}` | Role-bearing entries replace the overloaded flat list. Parent-document authors and publishers remain excluded unless explicitly relevant to the snapshot. |
| `language` | Rename | `languages` | `schema:inLanguage`; `dcterms:language`; BCP 47 | The languages explicitly used within the snapshot, preserving labels and optional BCP 47 tags. | — | Multiple languages should be supported. |
| `interpretive_note` | Rename | `interpretive_notes` | `dcterms:description`; `schema:description`; SDMX annotations | Explicit explanatory, methodological, uncertainty, sample-size, or provenance statements that aid interpretation or traceability. | — | Preserve complete source statements. Structured extraction of their internal facts remains outside this concept. |

### Project and operational context

| v1.1.1 concept | Disposition | v1.2 location/name | Standards basis | Definition | Minimal example | Design rationale |
|---|---|---|---|---|---|---|
| `project_name` | Fold | `project.name` | `schema:Project` + `schema:name`; IATI activity title | The name of the project, program, operation, or initiative associated with the snapshot. | `"project_name": "Coastal Resilience Project"` → `"project": {"name": "Coastal Resilience Project"}` | Do not narrow the application concept to Schema.org's `Project`. |
| `project_identifier` | Fold | `project.identifiers` | `schema:Project` + `schema:identifier`; IATI `iati-identifier` | Formal identifiers assigned to the associated project or operation, optionally including their scheme or issuer. | `"project_identifier": "P123456"` → `"project": {"identifiers": [{"value": "P123456", "scheme": "World Bank project ID"}]}` | Use a collection because multiple identifier schemes may coexist. |
| `project_component` | Rename; fold | `project.components` | `schema:hasPart`; Schema.org project substructure; IATI related-activity | The explicitly identified component, workstream, results area, or other subordinate part of the associated project context. | `"project_component": ["Component 2"]` → `"project": {"components": [{"name": "Component 2"}]}` | Keep general enough for components that are neither organizations nor separately reported activities. |
| `intervention_type` | Rename | `intervention_types` | Local concept; IATI classifications; Schema.org `DefinedTerm`; SKOS | The explicitly represented interventions, services, policies, or operational activities, optionally associated with controlled concepts. | — | Keep outside `project` so it remains usable when no project is named. |
| `financial_measure` | Rename; fold | `financing.measures` | Local concept; IATI transaction/budget classifications; SDMX measure concepts | The financial quantities or funding-related measures represented, such as project cost, allocation, disbursement, or funding gap. | `"financial_measure": ["Funding gap"]` → `"financing": {"measures": [{"name": "Funding gap"}]}` | Preserve a local concept with targeted IATI mappings. |
| `financing_source` | Rename; fold | `financing.funders` | `schema:funder`; IATI funding-role organization | The organizations or other funding sources explicitly identified as providing financial support. | `"financing_source": ["Asian Development Bank"]` → `"financing": {"funders": [{"name": "Asian Development Bank"}]}` | Use role-bearing organization references. |
| `financing_instrument` | Rename; fold | `financing.instruments` | IATI `FinanceType`; Schema.org `Grant` / `LoanOrCredit` | The financing mechanisms explicitly associated with the represented activity, preserving labels and optional scheme codes. | `"financing_instrument": ["Grant"]` → `"financing": {"instruments": [{"source_text": "Grant"}]}` | IATI/OECD codes are optional domain-specific normalizations. |

### Analytical and methodological context

| v1.1.1 concept | Disposition | v1.2 location/name | Standards basis | Definition | Minimal example | Design rationale |
|---|---|---|---|---|---|---|
| `analysis_method` | Rename | `analysis_methods` | Local concept; Schema.org `measurementTechnique`; PROV activity pattern | The explicitly stated analytical, statistical, or computational methods used to produce the reported results. | — | Keep distinct from data collection. Permit a displayed label and optional external identifier. |
| `data_collection_method` | Rename | `data_collection_methods` | DDI `ModeOfCollection`; `schema:measurementMethod`; SDMX collection concepts | The explicitly stated methods or instruments used to collect the underlying data. | — | Permit DDI-compatible controlled values without requiring the DDI model. |

## Snapshot evidence

### Evidence boundary

The v1.2 design evidence is intentionally limited to **18 unique snapshots**:

- the six representative examples in
  [`manuscript/data/snapshots`](../../manuscript/data/snapshots); and
- the twelve snapshots in Validation 1
  [`calibration0`](../../notebooks/schema_validation1/data/calibration0), which
  were subsequently reused by Validation 2 calibration. Later Validation 2
  ablation sets contain subsets of these same twelve snapshots and do not
  expand the design evidence.

No other discovery or held-out validation snapshots are inspected during v1.2
design. After the v1.2 Pydantic schema is frozen, a separate confirmatory
Schema v1.2 validation exercise will assess whether critical reusable metadata
in the validation sample can be adequately represented. This preserves a clear
boundary between design evidence and later stability evidence.

Two held-out Validation 2 snapshots were subsequently inspected as explicit,
question-specific exceptions:

- the composite UNHCR
  [`protection_trends_paper_no_7_jan-mar_2016_final_figure_004.png`](../../notebooks/schema_validation1/data/snapshots/unhcr/figure/protection_trends_paper_no_7_jan-mar_2016_final_figure_004.png),
  which raised the `panel_metadata_mapping` candidate; and
- the UNHCR
  [`rapport_du_monitoring_de_protection_de_la_region_de_diffa_du_mois_de_octobre_2022_ciaud_niger_table_002.png`](../../notebooks/schema_validation1/data/snapshots/unhcr/table/rapport_du_monitoring_de_protection_de_la_region_de_diffa_du_mois_de_octobre_2022_ciaud_niger_table_002.png),
  which raised the `column_group_hierarchy` candidate.

These exceptions do not expand the general design sample. They inform
only their respective deferred representation questions; the panel question is
recorded for further review in [`aivin_review.md`](aivin_review.md).

Visible image content was treated as the primary evidence;
prior discovery observations were used only as supporting context.

### Manuscript examples

| Manuscript snapshot | Relevant visible evidence | Design implication |
|---|---|---|
| [UNHCR cross-border-movements dashboard](../../manuscript/data/snapshots/nov_2023_rbsa_population_data_analysis_figure_002.png) | Southern Africa is the overall scope, while named countries participate as origins, asylum countries, and destinations. The snapshot also contains multiple measures, units, dimensions, and visualization forms. | Confirms that geographic scope and represented entities are distinct. Supports open, source-grounded geographic roles. Composite relationships remain difficult without panel modeling. |
| [Afghanistan labor-income table](../../manuscript/data/snapshots/108733-revised-public-wb-unhcr-policy-brief-final_table_000.png) | Employment sectors form the rows; mean and median form the columns. “Authors' calculation based on ALCS 2013-14” combines an attribution with a derivation source. | Supports dimension/category relationships and splitting provenance roles. Afghanistan can be represented as scope without duplicating it in a locations list. |
| [Vietnam provincial-poverty map](../../manuscript/data/snapshots/document_13148967_figure_003.png) | Vietnam is the overall scope, the data are reported at provincial level, and individual provinces are not named. Two titled maps represent 1999 and 2006. | Geographic level must be representable at coverage level rather than requiring a named location. The ordered panel-title approach remains adequate. |
| [Dependent and explanatory variables table](../../manuscript/data/snapshots/document_7255556_table_001.png) | Many variables have different units or transformations, while mean and standard deviation apply across them. Several variables have special temporal qualifications in the note. | Confirms that flat global lists can lose variable-to-unit and variable-to-time relationships. Supports variable-centric measurement qualifiers while preserving variable-specific temporal qualifications in notes. |
| [Technical-education graduates chart](../../manuscript/data/snapshots/005_BOSIB-8191b179-7209-4faa-b5e0-11783bcd492d_figure_001.png) | Men and women are explicitly compared across three titled STEAM fields and annual observations. | Supports a snapshot-level comparison such as “Men vs Women” while retaining gender as a category dimension. Panel titles remain sufficient for the current scope. |
| [Niger project-financing table](../../manuscript/data/snapshots/056_Niger-COVID-19-Emergency-Response-Project_table_003.png) | The snapshot combines project cost, financing, funding gap, credit, grant, funders, US dollars in millions, and fiscal years. | Supports grouped project and financing structures and demonstrates why financial measures, instruments, funders, currency, magnitude, and time must remain distinguishable. |

### Calibration examples

| Calibration subset | Relevant visible evidence | Design implication |
|---|---|---|
| [Policy Research Working Papers](../../notebooks/schema_validation1/data/calibration0/prwp) | The four snapshots include coded product categories, an explicit line-comparison rule, a regression table with several dependent variables and statistics, and a zone-level table with named places, several measures, a data source, and a period note. | Reinforces dimension/category pairing, snapshot-level comparison descriptions, coverage-level geographic granularity, provenance roles, and the difficulty of one uniform measure attachment. |
| [Refugee Project Appraisal Documents](../../notebooks/schema_validation1/data/calibration0/refugee) | The Guinea and Jordan composites span several subject domains, comparator groups, time periods, variables, units, and visualization forms. The monitoring table associates each indicator with a unit, target, frequency, method, responsible agent, and project components. The Guinea table distinguishes country scope from named natural regions. | Justifies plural `subject_domains`; reinforces scope/entity separation and structured provenance, project, and financing context; and supports variable-centric measurement qualifiers. |
| [UNHCR / ReliefWeb](../../notebooks/schema_validation1/data/calibration0/unhcr) | The four snapshots include country-of-origin roles, nested response-plan and country geography, province/territory hierarchy, multiple financing measures, and product-specific units compared before and during a crisis. | Supports open geographic-role strings, coverage-level geographic hierarchy, snapshot-level comparison descriptions, and preservation of unit-to-subject relationships where explicit. |

### Snapshot-informed design conclusions

The bounded evidence supports the dimension, provenance, geographic-coverage,
and project/financing directions. It resolves the current questions as follows:

- use plural `subject_domains`, because the composite country profiles contain
  multiple coequal broad domains;
- retain separate scope and location concepts, while avoiding duplicate values
  when a snapshot names only its overall scope;
- represent geographic level at coverage level and keep geographic role as an
  open, source-grounded string rather than a required closed vocabulary; and
- retain comparison descriptions at snapshot level, including values such as
  “Men vs Women,” “Guinea vs Sub-Saharan Africa vs low-income countries,” or
  “before vs during the crisis.”

The approved measurement structure is variable-centric: each entry in
`variables` owns its name and may carry an applicable unit, currency, and one or
more statistical forms. v1.2 will not introduce a parallel general-purpose
`measures` collection or extract numerical observations. Project-specific
`financing.measures` remains a distinct concept.

The Validation 2 hierarchy candidate is resolved within the existing
dimension/category structure. A dimension may contain ordinary ungrouped
`categories` and, when explicitly visible, non-recursive `category_groups`
whose members are categories. This preserves the observed broad-class-to-
incident-subtype relationship without modeling table cells, column spans,
coordinates, totals, or a general table layout.

The inspected Validation 2 panel candidate demonstrates that flat
lists cannot preserve panel-specific associations among titles, visualization
types, subjects, variables, and periods. A general panel object could, however,
make each panel resemble an independent snapshot by reproducing much of the
schema. The design therefore uses the narrower `panel_titles`
collection with snapshot-level `visualization_types`. Whether to introduce a
minimal panel descriptor containing only a title and visualization type is
tracked as a possible later change in [`aivin_review.md`](aivin_review.md).

## Design outcome

The concept-design phase is complete. The 35-concept semantic baseline is
preserved through the field and structural decisions recorded above. The
current application-facing names and flat panel-title representation remain
the working v1.2 baseline unless the separately tracked Aivin review produces a
change. Standard formats, identifiers, vocabularies, and value-normalization
rules are specified separately in [`normalization.md`](normalization.md).
