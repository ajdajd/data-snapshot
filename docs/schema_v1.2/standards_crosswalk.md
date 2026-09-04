# Data Snapshot Metadata Schema v1.2: Standards Crosswalk

Status: Crosswalk review complete; semantic baseline approved
Date: 2026-09-04

## Purpose and scope

This document restarts the standards-alignment exercise from the validated
Data Snapshot Metadata Schema v1.1.1. It was prepared independently of the
earlier standards crosswalk and v1.2 prototype. Those artifacts may be used
later for comparison, but they were not used as mapping authorities here.

The unit of analysis is a **data snapshot**: a self-contained table, chart,
map, dashboard, or composite figure extracted from an institutional document.
The crosswalk asks whether an established standard supplies:

- the same metadata concept;
- a close or partial semantic analogue;
- a useful structural pattern; or
- only a normalization vocabulary for field values.

It does not yet decide the final v1.2 field names, nesting, cardinalities,
Pydantic types, or validation rules. Those are downstream design decisions.
Schema.org is one reference vocabulary, not a mandatory primary anchor.

## Confirmed baseline

Schema v1.1.1 contains 36 fields. The v1.2 standards-alignment baseline has
**35 concepts** because `source_document_title` is intentionally removed.
The downstream application will maintain the snapshot-to-document relationship,
and source-document metadata will not be passed to snapshot extraction.

| Module | Concepts retained for alignment | Count |
|---|---|---:|
| Identity and discovery | `title`, `internal_identifier`, `subject_domain`, `subject_summary`, `panel_title` | 5 |
| Subject and semantics | `variable_name`, `category_dimension`, `category_labels`, `population_group` | 4 |
| Temporal context | `time_period`, `temporal_granularity` | 2 |
| Spatial context | `geographic_scope`, `geographic_entities`, `geographic_granularity`, `geographic_role`, `location_type` | 5 |
| Measurement context | `unit_of_measure`, `currency`, `measure_type`, `comparison_group` | 4 |
| Structural organization | `row_dimension`, `column_dimension`, `visualization_type` | 3 |
| Provenance and attribution | `data_source`, `language`, `interpretive_note` | 3 |
| Project and operational context | `project_name`, `project_identifier`, `project_component`, `intervention_type`, `financial_measure`, `financing_source`, `financing_instrument` | 7 |
| Analytical and methodological context | `analysis_method`, `data_collection_method` | 2 |
| **Total** |  | **35** |

The 35 concepts are a starting inventory, not a commitment to preserve 35
top-level Pydantic fields. Alignment may justify renaming, consolidating, or
nesting concepts while preserving their validated information coverage.

## Standards priority

Priority reflects breadth of adoption, closeness to this application's scope,
authority, and practical machine-readability. A high-priority standard is not
automatically preferred when a narrower standard has the better semantic fit.

| Priority | Standard or vocabulary | Primary use in this crosswalk | Treatment |
|---|---|---|---|
| 1 | [Schema.org](https://schema.org/docs/datamodel.html) | Web discovery, broadly recognizable properties, JSON-LD-compatible semantics | Broad reference vocabulary; reuse suitable terms but do not force all concepts into it |
| 1 | [DCMI Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/) | General resource description and discovery | Prefer for stable, generic descriptive concepts |
| 1 | [DCAT 3](https://www.w3.org/TR/vocab-dcat-3/) | Dataset catalog discovery, temporal and spatial coverage | Apply selectively because a snapshot is not necessarily a dataset or catalog record |
| 1 | [SDMX 3.1](https://sdmx.org/standards-2/) and [cross-domain concepts/code lists](https://sdmx.org/sdmx_cdcl/) | Statistical dimensions, measures, time, frequency, units, and codelists | Primary statistical reference; borrow semantics without adopting the full exchange model |
| 2 | [DDI Lifecycle 3.3](https://docs.ddialliance.org/DDI-Lifecycle/3.3/) | Variables, universes/populations, categories, geography, and data collection | Targeted research-data reference |
| 2 | [PROV-O](https://www.w3.org/TR/prov-o/) | Derivation, sources, agents, and role-bearing attribution | Structural reference for the validated provenance gap |
| 2 | [SKOS](https://www.w3.org/TR/skos-reference/) | Controlled concepts, labels, schemes, and hierarchical relations | Representation pattern for local or external controlled vocabularies |
| 2 | [IATI 2.03](https://reference.iatistandard.org/en/iati-standard/203/) | Development projects, funding organizations, transactions, and finance types | Domain-specific reference; use only where its development-finance semantics fit |
| 2 | [NISO JATS 1.3](https://jats.nlm.nih.gov/publishing/1.3/) | Figure identifiers, captions, labels, and figure groups | Targeted source-artifact reference, especially for figures and panels |
| 3 | ISO, IETF, and UN code standards | Deterministic value normalization | Use as value constraints or code systems, not as substitutes for metadata concepts |

Tier 3 currently includes [ISO 8601-1](https://www.iso.org/standard/70907.html)
for dates and intervals, [ISO 3166](https://www.iso.org/iso-3166-country-codes.html)
and [UN M49](https://unstats.un.org/unsd/methodology/m49/) for countries and
statistical regions, [ISO 4217](https://www.iso.org/iso-4217-currency-codes.html)
for currencies, [IETF BCP 47](https://www.rfc-editor.org/info/bcp47) for
languages, and [UN/CEFACT Recommendation 20](https://unece.org/code-list-recommendations)
for units of measure.

## Relationship labels

These labels record the reviewed semantic relationship between each v1.1.1
concept and its best current standards alignment.

- **Exact**: the standard term has the same essential meaning and intended use.
- **Close**: the meanings substantially overlap, with a bounded difference in
  scope or application.
- **Standard broader**: the standard term covers the local concept plus other
  meanings.
- **Standard narrower**: the standard term covers only part of the local
  concept.
- **Related/structural**: the standard offers a useful relationship or modeling
  pattern but is not a semantic equivalent.
- **No direct match**: no reviewed standard term is defensibly equivalent; the
  local concept may still be represented using standard carriers and local
  controlled values.

## Concept crosswalk

The alignment definitions below are concise paraphrases of the linked
authoritative sources, limited to the meaning relevant to this comparison.

| # | v1.1.1 concept | v1.1.1 Definition | Best current alignment | Alignment definition (abridged) | Reviewed relationship | Other useful references | Research interpretation for v1.2 |
|---:|---|---|---|---|---|---|---|
| 1 | `title` | The primary title, caption, or heading that identifies the data snapshot. | [`dcterms:title`](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#http://purl.org/dc/terms/title) | A name given to a resource. | Exact | [`schema:name`](https://schema.org/name); SDMX `TITLE` | Retain the snapshot title concept. A v1.2 name may follow the local API's clarity needs while publishing an interoperability alias. |
| 2 | `internal_identifier` | A document-assigned identifier used to reference the snapshot within the source document. | [`schema:identifier`](https://schema.org/identifier) / `dcterms:identifier` | Any reference that unambiguously identifies a resource or thing within a given context. | Standard broader | JATS [`label`](https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/label.html) | Keep the qualifier that this is the document-assigned snapshot label, such as “Figure 3,” rather than any identifier. A structured identifier could record its scheme or local context later. |
| 3 | `subject_domain` | The broad thematic, policy, or sectoral domain represented by the snapshot. | [`dcterms:subject`](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#http://purl.org/dc/terms/subject) | A topic of the described resource, preferably identified using a controlled vocabulary. | Standard broader | [`schema:about`](https://schema.org/about); `dcat:theme`; SKOS concept/scheme | Model the value as a controlled concept where possible. The schema still needs the local distinction between a broad domain and the more specific subject summary. |
| 4 | `subject_summary` | A concise summary describing the primary analytical subject or purpose of the snapshot. | [`schema:abstract`](https://schema.org/abstract) | A short description that summarizes a creative work. | Close | `dcterms:description` (standard broader) | Preserve a concise analytical summary. `schema:abstract` is closer than generic `description`, but the snapshot scope must remain explicit. |
| 5 | `panel_title` | The title or heading of an individual panel within a multi-panel snapshot.<br><br>Populate only when panel titles are explicitly present. | JATS [`fig-group`](https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/fig-group.html), `fig`, and `caption/title` | A figure group can contain individual figures, each capable of carrying its own label and caption title. | Close | [`schema:hasPart`](https://schema.org/hasPart) + `schema:name` (structural) | Preserve explicit panel titles as an ordered list for now. Standards support titled parts, but do not require the project to create panel objects before other composite-field relationships are designed. |
| 6 | `variable_name` | The primary variable, indicator, metric, or measured concept represented by the snapshot.<br><br>In v1.1.1, this field records the variable's name or measured concept, not a normalized analytical role. Use `category_dimension`, `category_labels`, `row_dimension`, and `column_dimension` where those structural roles apply. Dedicated outcome, predictor, control, or axis-assignment fields are not part of v1.1.1. | [`schema:variableMeasured`](https://schema.org/variableMeasured) | A variable measured in a dataset or observation, represented as text or a structured variable description. | Close | Schema.org `StatisticalVariable`; DDI `Variable`/`RepresentedVariable`; SDMX measure concept | The field may evolve from a string into a typed variable object. Schema.org explicitly allows text, `PropertyValue`, or `StatisticalVariable`, making it a useful interoperability pattern. |
| 7 | `category_dimension` | The conceptual variable or dimension used to organize, group, classify, or compare the represented values. | SDMX `Dimension` | An identifying or classificatory component in a multidimensional statistical structure. | Close | DDI `RepresentedVariable`; RDF Data Cube `qb:DimensionProperty` | Treat as a statistical/classificatory dimension. Do not assume that every dimension is visibly assigned to a table axis or chart channel. |
| 8 | `category_labels` | The explicit category names or labels associated with a category dimension. | SDMX `Code` / `Codelist` | Codes and their labels that define the permissible values for a coded statistical concept. | Close | DDI `Category`/`CodeList`; [`skos:prefLabel`](https://www.w3.org/TR/skos-reference/#labels) | Preserve original displayed labels and optionally attach codes and a scheme. Labels should remain linked to their dimension rather than stored as one unqualified global list. |
| 9 | `population_group` | The human population, beneficiary group, or demographic group that is the primary subject of the represented data. This field describes who the data are about, not how they are categorized or disaggregated. | DDI [`Universe`](https://docs.ddialliance.org/DDI-Lifecycle/3.3/xmlschema/schemas/conceptualcomponent_xsd/elements/Universe.html) | The population or set of units to which data collection or analytical results refer. | Close | Schema.org `StatisticalVariable.populationType` | DDI is the strongest semantic model: the concept describes who or what the results concern, not the categories used to disaggregate them. |
| 10 | `time_period` | The period or date range represented by the data.<br><br>This field describes **when the represented data apply**. It does not describe when the snapshot artifact or parent document was created, prepared, issued, published, revised, or retrieved. When an explicit artifact date appears only as part of a footer or provenance statement, preserve the complete statement in `interpretive_note` rather than treating the date as `time_period`. | [`schema:temporalCoverage`](https://schema.org/temporalCoverage) | The period to which a creative work's content applies, often expressed as a date or ISO 8601 interval. | Exact | `dcterms:temporal`; SDMX `TIME_PERIOD`; ISO 8601 | Retain the represented-data period and keep it distinct from artifact or document dates. Normalize unambiguous dates/intervals while retaining the source expression where useful. |
| 11 | `temporal_granularity` | The temporal resolution at which the represented data are reported. | SDMX `FREQ` / `CL_FREQ` | The interval at which observations occur, such as annual, quarterly, monthly, or daily. | Close | `dcat:temporalResolution`; OWL-Time temporal units | SDMX frequency matches annual, quarterly, monthly, and similar reporting intervals. DCAT temporal resolution is useful when an ISO 8601 duration is appropriate, but should not erase the original label. |
| 12 | `geographic_scope` | The primary geographic area represented by the snapshot. | [`schema:spatialCoverage`](https://schema.org/spatialCoverage) / `dcterms:spatial` | The place or geographic area that is the focus or coverage of a creative work or dataset. | Exact | DCAT spatial coverage | Use this for the overall geographic coverage or focus. It may point to a named place, region, or resolvable identifier. In v1.2, fold it into one coherent geographic structure with `geographic_entities`, `geographic_granularity`, `geographic_role`, and `location_type`, while preserving the distinct meaning of each facet. |
| 13 | `geographic_entities` | Named geographic entities explicitly represented within the snapshot. | [`schema:spatialCoverage`](https://schema.org/spatialCoverage) with repeated `Place` values | One or more places that the content describes or geographically covers. | Close | DDI `GeographicLocation`; SEMIC Core Location Vocabulary | Preserve the distinct list of explicitly represented places. In v1.2, each entity can carry its displayed name and, when deterministic, a standard code or URI. |
| 14 | `geographic_granularity` | The administrative or spatial level at which data are reported. | DDI `GeographicLevel` | A level in a geographic hierarchy used to organize or classify geographic locations. | Close | ISO 3166-2 for coded principal subdivisions; local level vocabulary | Administrative or reporting level is not DCAT `spatialResolutionInMeters`; that term measures minimum spatial separation. Keep a separate level concept and define a small controlled vocabulary. |
| 15 | `geographic_role` | The semantic role played by geographic entities within the represented data. | No direct cross-domain match | No reviewed term generally distinguishes roles such as origin, host, destination, and reporting location. | No direct match | DDI geography structures; IATI recipient country/region and location roles (domain-specific); SKOS value scheme | Keep a local role vocabulary such as origin, host, destination, or reporting location. Attach the role to each geographic entity so the relationship is not lost. |
| 16 | `location_type` | The type of physical location represented. | No direct cross-domain match | No reviewed cross-domain property defines this concept; IATI provides a domain-specific feature-designation codelist. | No direct match | IATI [`LocationType`](https://reference.codeforiati.org/codelists/LocationType/); Schema.org `additionalType` or `DefinedTerm`; SKOS value scheme | Keep the semantic distinction between a place and its type (camp, hospital, school, district). Use a typed term object that can carry a local or external scheme. IATI location-type codes can be supported when applicable, but they do not define the domain-agnostic concept. |
| 17 | `unit_of_measure` | The unit used to interpret reported quantitative values. | SDMX `UNIT_MEASURE` | The unit in which associated observation values are measured or expressed. | Exact | [`schema:unitCode`](https://schema.org/unitCode); UN/CEFACT Recommendation 20 | The semantic mapping is exact even though value normalization may be partial. Separate the displayed unit label from an optional normalized code; not every project unit (for example, “people”) will map cleanly without policy decisions. |
| 18 | `currency` | The currency denomination used for monetary values. | [`schema:currency`](https://schema.org/currency) | The currency in which a monetary amount is expressed. | Exact | [ISO 4217](https://www.iso.org/iso-4217-currency-codes.html); SDMX `CL_CURRENCY` | Keep the semantic property separate from its value standard. Use the three-letter ISO 4217 code when the currency is explicit or can be normalized deterministically, and keep currency separate from the broader unit concept. |
| 19 | `measure_type` | The statistical form in which values are expressed. | [`schema:statType`](https://schema.org/statType) | The kind of statistic represented by a statistical variable, such as a mean or count. | Close | SDMX measure/unit concepts; local controlled vocabulary | `statType` covers kinds of statistic such as mean and count, but v1.1.1 also includes rate, percentage, and index. Retain a local controlled vocabulary and cross-map individual values where defensible. |
| 20 | `comparison_group` | The benchmark, comparator, reference group, cohort, scenario, or entity against which the represented data are compared.<br><br>Populate only when the snapshot explicitly presents a comparative relationship. This field captures the intended comparison or benchmark represented by the snapshot, not simply the categories used to organize the data. | No direct cross-domain match | No reviewed term generally represents the explicit benchmark or comparator role used here. | No direct match | DDI comparison/group structures; Schema.org `measurementQualifier` (narrow/related) | Preserve as an explicit comparison relation rather than collapsing it into ordinary category labels. Later design must decide how comparator and reference roles attach to variables or observations. |
| 21 | `row_dimension` | The conceptual variable represented by table rows. | SDMX `Dimension` | An identifying or classificatory statistical component; SDMX does not assign it a table-row role. | Standard broader | DDI variable/dimension structures | “Row” is a presentation role, not a statistical concept in SDMX. Represent the underlying dimension with a local layout role so semantics survive independently of rendering. |
| 22 | `column_dimension` | The conceptual variable represented by table columns. | SDMX `Dimension` | An identifying or classificatory statistical component; SDMX does not assign it a table-column role. | Standard broader | DDI variable/dimension structures | Apply the same pattern as `row_dimension`: standard dimension semantics plus a local presentation role. |
| 23 | `visualization_type` | The primary visualization used to encode the represented data.<br><br>For a composite or multi-panel snapshot, record a concise description of the overall visualization type or visible combination when no single type adequately describes the artifact. Use `panel_title` for explicit panel headings. v1.1.1 does not separately encode component-to-type relationships or `panel_count`; those are normalization concerns for v1.2. | `dcterms:type` | The nature or genre of a resource, normally expressed using a controlled vocabulary. | Standard broader | Schema.org `additionalType`; JATS `fig`/`table-wrap`; local SKOS scheme | No reviewed broad standard supplies the required chart/table/map taxonomy. Retain a local controlled vocabulary that can be published as a SKOS concept scheme. |
| 24 | `data_source` | The named dataset, survey, publication, organization, or credited agent from which the represented data originate or which is explicitly credited with producing the snapshot artifact.<br><br>In v1.1.1, `data_source` may retain multiple names but does not structurally distinguish roles such as data source, data producer, map maker, preparer, or contributor. A role-bearing representation is deferred to v1.2. Do not copy the parent document's authors or publisher into this field solely because they are associated with the document; the source or attribution must be explicitly relevant to the snapshot or its represented data. | [`prov:wasDerivedFrom`](https://www.w3.org/TR/prov-o/#wasDerivedFrom) and [`prov:wasAttributedTo`](https://www.w3.org/TR/prov-o/#wasAttributedTo) | Links an entity to a source entity from which it was derived, or to an agent credited with it. | Related/structural | `dcterms:source`; Schema.org `creator`, `provider`, `creditText`; PROV qualified relations | Replace the overloaded flat list with role-bearing provenance entries. A represented-data source is an entity involved in derivation; a map maker or producer is an attributed agent. Parent-document metadata remains outside this snapshot structure. |
| 25 | `language` | The language used within the snapshot. | [`schema:inLanguage`](https://schema.org/inLanguage) / `dcterms:language` | The language of a creative work or resource, commonly represented with a standard language tag. | Exact | [IETF BCP 47](https://www.rfc-editor.org/info/bcp47) | Preserve displayed language labels if useful and normalize to BCP 47 tags when deterministically identifiable. Support multiple languages. |
| 26 | `interpretive_note` | Explanatory, methodological, uncertainty, or provenance statements explicitly provided within the snapshot that aid interpretation or traceability.<br><br>This field may preserve complete notes containing sample-size statements, explanations of confidence intervals, standard errors or uncertainty bands, and footer statements that include an artifact date or production credit. It retains the statement as text; it does not create separate structured fields for sample size, uncertainty representation, or artifact publication date.<br><br>Populate only when such notes are explicitly present. | `dcterms:description` / `schema:description` | A general textual account or description of a resource. | Standard broader | SDMX data attributes and annotations (related) | Keep a local note concept for explicit methodological, uncertainty, sample-size, and provenance statements. A generic description property can expose it interoperably but should not dictate its internal semantics. |
| 27 | `project_name` | The project, program, operation, or initiative associated with the snapshot. | [`schema:Project`](https://schema.org/Project) + `schema:name` | The name of an enterprise planned to achieve a particular aim. | Standard narrower | IATI activity `title` | `schema:Project` is a strong fit for projects but does not explicitly cover every program, operation, or initiative allowed locally. Retain the broader application concept and map project-shaped cases directly. |
| 28 | `project_identifier` | The formal identifier assigned to the associated project or operation. | `schema:Project` + [`schema:identifier`](https://schema.org/identifier) | An identifier assigned to a project, represented as text, a URL, or a structured property value. | Exact | IATI [`iati-identifier`](https://reference.iatistandard.org/en/iati-standard/203/activity-standard/iati-activities/iati-activity/iati-identifier/) (standard narrower) | Represent the value with an optional identifier scheme or issuing organization. Do not assume all project identifiers are IATI identifiers. |
| 29 | `project_component` | The project component, workstream, or results area represented by the snapshot. | `schema:Project` + `schema:subOrganization`/`parentOrganization` | A relationship for expressing organizational substructures within a project modeled as an organization. | Standard narrower | `schema:hasPart`; IATI [`related-activity`](https://reference.codeforiati.org/activity-standard/iati-activities/iati-activity/related-activity/) parent/child relations | Schema.org covers only components modeled as project organizations, while IATI covers components reported as related activities. Retain a general local component object and map only compatible cases. |
| 30 | `intervention_type` | The intervention, service, policy, or operational activity represented. | No direct cross-domain match | No reviewed term generally classifies interventions, services, policies, and operational activities together. | No direct match | IATI activity/aid/sector classifications (narrow); Schema.org `DefinedTerm`; SKOS | Preserve a local controlled concept for intervention, service, policy, or operational activity. Attach a vocabulary identifier when the source uses IATI or another recognized scheme. |
| 31 | `financial_measure` | The financial quantity or funding-related measure represented by the snapshot. | IATI transaction types and budget elements | Transaction classifications distinguish kinds of financial flows, while budget elements describe planned financial resources. | Standard narrower | SDMX measure concepts; Schema.org `MonetaryAmount` (value structure, not measure type) | The local concept spans project cost, disbursement, gap, and allocation. Use a local measure concept, with targeted mappings for values that match IATI transaction or budget semantics. |
| 32 | `financing_source` | The organization or funding source providing financial support. | [`schema:funder`](https://schema.org/funder) | A person or organization that supports something through a financial contribution. | Exact | IATI [`participating-org` with funding role](https://reference.iatistandard.org/en/iati-standard/203/codelists/organisationrole/) | Model the funder as an organization or agent with an explicit funding role. IATI supplies a precise domain-specific role code where applicable. |
| 33 | `financing_instrument` | The financing mechanism associated with the represented activity. | IATI [`FinanceType`](https://reference.iatistandard.org/en/iati-standard/203/codelists/financetype/) | A DAC/CRS classification that distinguishes financial instruments such as grants and loans. | Close | Schema.org `Grant` and `LoanOrCredit` types (narrow) | IATI/OECD DAC offers an established finance-type list, but it is development-finance specific and more detailed than the current examples. Permit a local label plus an optional scheme/code. |
| 34 | `analysis_method` | The analytical, statistical, or computational method used to produce the reported results.<br><br>Populate only when explicitly stated. | No direct cross-domain match | No reviewed term generally represents analytical, statistical, and computational methods used to produce results. | No direct match | Schema.org `measurementTechnique` (related, often narrower in purpose); PROV `Activity` structure | Do not equate regression or difference-in-differences with data-collection or measurement technique. Preserve a local analytical-method term and allow an external URI or scheme when available. |
| 35 | `data_collection_method` | The method or instrument used to collect the underlying data.<br><br>Populate only when explicitly stated. | DDI [`ModeOfCollection`](https://docs.ddialliance.org/DDI-Lifecycle/3.3/xmlschema/schemas/datacollection_xsd/complexTypes/ModeOfCollectionType.html) | The mode used to collect data, such as a questionnaire, observation, interview, or automated harvesting. | Exact | [`schema:measurementMethod`](https://schema.org/measurementMethod); SDMX collection-method concepts | DDI supplies the closest definition and controlled vocabulary pattern. Schema.org offers a useful broader publishing property but does not distinguish collection from analysis by itself. |

## Crosswalk conclusions

The reviewed crosswalk establishes the concept-level baseline for v1.2: the
information distinctions to preserve and their relationships to external
standards. It supports the following conclusions:

1. **Preserve the coverage of all 35 concepts, but do not assume a flat
   35-field model.** Typed or nested structures may better preserve
   relationships among variables, dimensions, geography, provenance, projects,
   and controlled terms.
2. **Use a multi-standard application profile.** DCMI, Schema.org, and DCAT
   support general discovery; SDMX and DDI support statistical semantics;
   PROV-O supports provenance; and IATI supports selected development-project
   and finance concepts. No single standard governs the complete application.
3. **Keep application naming independent of standards naming.** Standard terms
   may inform definitions and interoperability aliases without becoming the
   Python field names when a clearer application-facing name is available.
4. **Keep semantic alignment separate from value normalization.** ISO 8601,
   ISO 3166, UN M49, ISO 4217, BCP 47, UN/CEFACT Recommendation 20, and selected
   SDMX or IATI code lists may normalize values without replacing the metadata
   concepts that carry them. Source-visible labels should be retained where
   useful.
5. **Retain justified local concepts.** `geographic_role`, `location_type`,
   `comparison_group`, `visualization_type`, `intervention_type`,
   `financial_measure`, `interpretive_note`, and `analysis_method` do not have
   clean general equivalents and should not be forced into loosely related
   standard terms.
6. **Fold geography into a coherent structure while preserving its distinct
   facets.** Coverage, named entities, granularity, role, and location type
   remain separate meanings even when represented together.
7. **Represent provenance with explicit roles.** Derivation sources are
   entities from which represented data originate, while credited producers or
   makers are attributed agents. Parent-document metadata remains outside the
   snapshot metadata.
8. **Continue to preserve panel titles without requiring panel objects.** A
   richer composite representation is justified only if later design work
   shows that another validated concept loses its relationship or meaning.

The crosswalk does not determine final v1.2 names, definitions, nesting,
cardinalities, validators, controlled values, or serialization aliases. Those
decisions are taken forward in the
[`concept_design.md`](concept_design.md) disposition and design matrix.

## Authoritative sources consulted

- Schema.org: [data model](https://schema.org/docs/datamodel.html),
  [Dataset](https://schema.org/Dataset), and term pages linked in the crosswalk.
- DCMI: [DCMI Metadata Terms](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/).
- W3C: [DCAT 3](https://www.w3.org/TR/vocab-dcat-3/),
  [PROV-O](https://www.w3.org/TR/prov-o/),
  [SKOS](https://www.w3.org/TR/skos-reference/), and
  [OWL-Time](https://www.w3.org/TR/owl-time/).
- SDMX: [technical standards](https://sdmx.org/standards-2/),
  [glossary](https://sdmx.org/wp-content/uploads/SDMX_Glossary_Version_2_0_October_2018.htm),
  and [cross-domain code lists](https://sdmx.org/sdmx_cdcl/).
- DDI Alliance: [DDI Lifecycle 3.3 documentation](https://docs.ddialliance.org/DDI-Lifecycle/3.3/).
- IATI: [Standard 2.03 reference](https://reference.iatistandard.org/en/iati-standard/203/).
- NISO/NLM: [JATS 1.3](https://jats.nlm.nih.gov/publishing/1.3/).
- ISO: [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html),
  [ISO 3166](https://www.iso.org/iso-3166-country-codes.html), and
  [ISO 4217](https://www.iso.org/iso-4217-currency-codes.html).
- United Nations: [UN M49](https://unstats.un.org/unsd/methodology/m49/) and
  [UN/CEFACT Recommendation 20](https://unece.org/code-list-recommendations).
- IETF: [BCP 47](https://www.rfc-editor.org/info/bcp47).
