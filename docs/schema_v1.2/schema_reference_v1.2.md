# Data Snapshot Metadata Schema v1.2 Reference

<!-- Generated from DataSnapshotMetadata. Do not edit manually. -->

Represent canonical semantic metadata for one data snapshot.

Schema version: `1.2`

## Validation and serialization

- Python is the canonical validator. JSON Schema enforces exported structural rules; format assertions require a format-aware validator.
- Python additionally applies NFC normalization, outer whitespace trimming, and stable exact deduplication.
- Python additionally checks URI syntax before URL normalization, language-tag casing and uniqueness, calendar dates, and chronological ordering.
- Missing and null values are equivalent. Serialize records with exclude_none=True to omit unavailable values.
- External registry membership, source-grounding, and semantic correctness are not validated. Unpinned code-list metadata identifies a syntax authority only.

## Snapshot fields

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `title` | `string \| null` | no | `null` | Primary title, caption, or heading identifying the snapshot. | minLength: 1; pattern: \S | [http://purl.org/dc/terms/title](http://purl.org/dc/terms/title) (exact), [https://schema.org/name](https://schema.org/name) (exact) |
| `document_label` | `string \| null` | no | `null` | Label assigned within the parent source document. | minLength: 1; pattern: \S | [https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/label.html](https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/label.html) (close), [https://schema.org/identifier](https://schema.org/identifier) (standard_broader) |
| `subject_domains` | `array[ControlledTerm] \| null` | no | `null` | Broad thematic, policy, or sectoral domains. | minItems: 1 | [http://purl.org/dc/terms/subject](http://purl.org/dc/terms/subject) (standard_broader), [https://schema.org/about](https://schema.org/about) (standard_broader) |
| `subject_summary` | `string \| null` | no | `null` | Concise summary of the primary analytical subject or purpose. | minLength: 1; pattern: \S | [https://schema.org/abstract](https://schema.org/abstract) (close), [http://purl.org/dc/terms/description](http://purl.org/dc/terms/description) (standard_broader) |
| `panel_titles` | `array[string] \| null` | no | `null` | Ordered titles explicitly shown for individual panels. | minItems: 1 | [https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/fig-group.html](https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/fig-group.html) (close), [https://schema.org/hasPart](https://schema.org/hasPart) (related_structural) |
| `variables` | `array[Variable] \| null` | no | `null` | Explicitly named measured concepts and their qualifiers. | minItems: 1 | [https://schema.org/variableMeasured](https://schema.org/variableMeasured) (close), [https://ddialliance.org/Specification/DDI-Lifecycle/3.3/](https://ddialliance.org/Specification/DDI-Lifecycle/3.3/) (close) |
| `dimensions` | `array[Dimension] \| null` | no | `null` | Classificatory dimensions and their visible organization. | minItems: 1 | [https://sdmx.org/](https://sdmx.org/) (close), [https://ddialliance.org/Specification/DDI-Lifecycle/3.3/](https://ddialliance.org/Specification/DDI-Lifecycle/3.3/) (close) |
| `population_group` | `ControlledTerm \| null` | no | `null` | Human population or beneficiary group represented by the data. |  | [https://docs.ddialliance.org/DDI-Lifecycle/3.3/xmlschema/schemas/conceptualcomponent_xsd/elements/Universe.html](https://docs.ddialliance.org/DDI-Lifecycle/3.3/xmlschema/schemas/conceptualcomponent_xsd/elements/Universe.html) (close), [https://schema.org/populationType](https://schema.org/populationType) (close) |
| `visualization_types` | `array[VisualizationTypeTerm] \| null` | no | `null` | Explicitly visible visualization forms used by the snapshot. | minItems: 1 | [http://purl.org/dc/terms/type](http://purl.org/dc/terms/type) (standard_broader), [https://schema.org/additionalType](https://schema.org/additionalType) (standard_broader) |
| `temporal_coverage` | `TemporalCoverage \| null` | no | `null` | When the represented data apply and their granularity. |  | [https://schema.org/temporalCoverage](https://schema.org/temporalCoverage) (exact), [http://purl.org/dc/terms/temporal](http://purl.org/dc/terms/temporal) (close) |
| `geographic_coverage` | `GeographicCoverage \| null` | no | `null` | Overall geographic scope, additional locations, and level. |  | [https://schema.org/spatialCoverage](https://schema.org/spatialCoverage) (exact), [http://purl.org/dc/terms/spatial](http://purl.org/dc/terms/spatial) (exact) |
| `comparisons` | `array[string] \| null` | no | `null` | Explicit comparative expressions or named comparators. | minItems: 1 |  |
| `provenance` | `Provenance \| null` | no | `null` | Represented-data sources and artifact attributions. |  |  |
| `languages` | `array[Language] \| null` | no | `null` | Languages explicitly used within the snapshot. | minItems: 1 | [https://schema.org/inLanguage](https://schema.org/inLanguage) (exact), [http://purl.org/dc/terms/language](http://purl.org/dc/terms/language) (exact) |
| `interpretive_notes` | `array[string] \| null` | no | `null` | Complete explanatory, methodological, uncertainty, sample-size, or provenance statements. | minItems: 1 | [http://purl.org/dc/terms/description](http://purl.org/dc/terms/description) (standard_broader), [https://schema.org/description](https://schema.org/description) (standard_broader) |
| `project` | `Project \| null` | no | `null` | Associated project, program, operation, or initiative. |  | [https://schema.org/Project](https://schema.org/Project) (standard_narrower), [https://iatistandard.org/en/iati-standard/203/activity-standard/](https://iatistandard.org/en/iati-standard/203/activity-standard/) (close) |
| `intervention_types` | `array[ControlledTerm] \| null` | no | `null` | Explicit interventions, services, policies, or operational activities. | minItems: 1 |  |
| `financing` | `Financing \| null` | no | `null` | Project-financing measures, funders, and instruments. |  |  |
| `analysis_methods` | `array[ControlledTerm] \| null` | no | `null` | Explicit analytical, statistical, or computational methods. | minItems: 1 | [https://schema.org/measurementTechnique](https://schema.org/measurementTechnique) (related_structural), [http://www.w3.org/ns/prov#Activity](http://www.w3.org/ns/prov#Activity) (related_structural) |
| `data_collection_methods` | `array[ControlledTerm] \| null` | no | `null` | Explicit methods or instruments used to collect underlying data. | minItems: 1 | [https://docs.ddialliance.org/DDI-Lifecycle/3.3/model/composite-types/ModeOfCollectionType/](https://docs.ddialliance.org/DDI-Lifecycle/3.3/model/composite-types/ModeOfCollectionType/) (exact), [https://schema.org/measurementMethod](https://schema.org/measurementMethod) (close) |

## AnalyticalRole

Identify an explicitly stated analytical or axis role.

`outcome`, `predictor`, `instrumental`, `control`, `x_axis`, `y_axis`

## Attribution

Represent a named agent and its explicit attribution role.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `name` | `string` | yes | — | Source-visible entity name. | minLength: 1; pattern: \S |  |
| `identifiers` | `array[Identifier] \| null` | no | `null` | Assigned entity identifiers. | minItems: 1 |  |
| `role` | `ControlledTerm` | yes | — | Explicit source-grounded agent role. |  |  |

## CategoryGroup

Represent one explicit nonrecursive category grouping.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `name` | `string` | yes | — | Explicit category-group heading. | minLength: 1; pattern: \S |  |
| `categories` | `array[ControlledTerm]` | yes | — | Categories directly contained by the group. | minItems: 1 |  |

## ControlledTerm

Represent a source-grounded term with optional normalization.

- At least one of source_text, normalized_value, code, or uri must be non-null.

- A non-null code requires a non-null scheme.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `source_text` | `string \| null` | no | `null` | Faithful source-visible expression. | minLength: 1; pattern: \S |  |
| `normalized_value` | `string \| null` | no | `null` | Preferred application or vocabulary value. | minLength: 1; pattern: \S |  |
| `code` | `string \| null` | no | `null` | Code in the named scheme. | minLength: 1; pattern: \S |  |
| `scheme` | `string \| null` | no | `null` | Code-list or vocabulary identifier. | minLength: 1; pattern: \S |  |
| `uri` | `uri \| null` | no | `null` | Authoritative URI for the represented concept. | minLength: 1; pattern: ^[A-Za-z][A-Za-z0-9+.-]*:(?://(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|:)*@)?(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})*\|\[[A-Za-z0-9:.!$&'()*+,;=_~-]+\])(?::[0-9]*)?(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|/(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*)?\|(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|)(?:\?(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?(?:#(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?$; format: uri |  |

## Currency

Represent a displayed currency and optional ISO 4217 code.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `source_text` | `string` | yes | — | Displayed currency expression. | minLength: 1; pattern: \S |  |
| `code` | `string \| null` | no | `null` | Uppercase ISO 4217 alphabetic code. | pattern: ^[A-Z]{3}$ | [ISO ISO 4217](https://www.iso.org/iso-4217-currency-codes.html); release: not pinned; syntax only |

## Dimension

Represent a classificatory dimension and its visible organization.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `name` | `string` | yes | — | Classificatory dimension name. | minLength: 1; pattern: \S |  |
| `categories` | `array[ControlledTerm] \| null` | no | `null` | Ordered ungrouped categories. | minItems: 1 | [http://www.w3.org/2004/02/skos/core#Concept](http://www.w3.org/2004/02/skos/core#Concept) (related_structural) |
| `category_groups` | `array[CategoryGroup] \| null` | no | `null` | One level of explicit category groups. | minItems: 1 | [http://www.w3.org/2004/02/skos/core#broader](http://www.w3.org/2004/02/skos/core#broader) (related_structural) |
| `presentation_roles` | `array[PresentationRole] \| null` | no | `null` | Explicit table-presentation roles. | minItems: 1 |  |

## EntityReference

Represent a named project, organization, source, or component.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `name` | `string` | yes | — | Source-visible entity name. | minLength: 1; pattern: \S |  |
| `identifiers` | `array[Identifier] \| null` | no | `null` | Assigned entity identifiers. | minItems: 1 |  |

## Financing

Group project-financing measures, funders, and instruments.

- At least one non-null value is required: measures, funders, instruments.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `measures` | `array[ControlledTerm] \| null` | no | `null` | Project-financing measures. | minItems: 1 |  |
| `funders` | `array[EntityReference] \| null` | no | `null` | Named funding sources. | minItems: 1 | [https://schema.org/funder](https://schema.org/funder) (exact) |
| `instruments` | `array[ControlledTerm] \| null` | no | `null` | Financing mechanisms. | minItems: 1 | [https://reference.iatistandard.org/en/iati-standard/203/codelists/financetype/](https://reference.iatistandard.org/en/iati-standard/203/codelists/financetype/) (close) |

## GeographicCoverage

Group overall geographic scope, locations, and reporting level.

- At least one non-null value is required: scope, locations, level.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `scope` | `Place \| null` | no | `null` | Overall geographic coverage or focus. |  | [https://schema.org/spatialCoverage](https://schema.org/spatialCoverage) (exact) |
| `locations` | `array[GeographicLocation] \| null` | no | `null` | Additional named locations. | minItems: 1 | [https://schema.org/spatialCoverage](https://schema.org/spatialCoverage) (related_structural) |
| `level` | `GeographicLevelTerm \| null` | no | `null` | Geographic or reporting level. |  |  |

## GeographicLevelTerm

Represent a known or source-only geographic reporting level.

- At least one of source_text, normalized_value, code, or uri must be non-null.

- A non-null code requires a non-null scheme.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `source_text` | `string \| null` | no | `null` | Faithful source-visible expression. | minLength: 1; pattern: \S |  |
| `normalized_value` | `GeographicLevelValue \| null` | no | `null` | Approved normalized geographic level. |  |  |
| `code` | `string \| null` | no | `null` | Code in the named scheme. | minLength: 1; pattern: \S |  |
| `scheme` | `string \| null` | no | `null` | Code-list or vocabulary identifier. | minLength: 1; pattern: \S |  |
| `uri` | `uri \| null` | no | `null` | Authoritative URI for the represented concept. | minLength: 1; pattern: ^[A-Za-z][A-Za-z0-9+.-]*:(?://(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|:)*@)?(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})*\|\[[A-Za-z0-9:.!$&'()*+,;=_~-]+\])(?::[0-9]*)?(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|/(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*)?\|(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|)(?:\?(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?(?:#(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?$; format: uri |  |

## GeographicLevelValue

Enumerate approved normalized geographic levels.

`global`, `world_region`, `country`, `administrative_area_1`, `administrative_area_2`, `administrative_area_3`, `locality`, `site`

## GeographicLocation

Represent an additional named location and its optional role and type.

- At least one non-null value is required: source_text, name.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `source_text` | `string \| null` | no | `null` | Displayed place expression. | minLength: 1; pattern: \S |  |
| `name` | `string \| null` | no | `null` | Preferred place name. | minLength: 1; pattern: \S |  |
| `country_code` | `string \| null` | no | `null` | ISO 3166-1 alpha-2 country code. | pattern: ^[A-Z]{2}$ | [ISO ISO 3166-1](https://www.iso.org/iso-3166-country-codes.html); release: not pinned; syntax only |
| `subdivision_code` | `string \| null` | no | `null` | ISO 3166-2 subdivision code. | pattern: ^[A-Z]{2}-[A-Z0-9]{1,3}$ | [ISO ISO 3166-2](https://www.iso.org/iso-3166-country-codes.html); release: not pinned; syntax only |
| `m49_code` | `string \| null` | no | `null` | UN M49 statistical-area code. | pattern: ^[0-9]{3}$ | [United Nations M49](https://unstats.un.org/unsd/methodology/m49/); release: not pinned; syntax only |
| `identifiers` | `array[Identifier] \| null` | no | `null` | Other authoritative identifiers. | minItems: 1 |  |
| `role` | `ControlledTerm \| null` | no | `null` | Explicit source-grounded geographic role. |  |  |
| `type` | `ControlledTerm \| null` | no | `null` | Physical or administrative location type. |  |  |

## Identifier

Represent an assigned identifier and its optional authority context.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `value` | `string` | yes | — | Identifier exactly as assigned. | minLength: 1; pattern: \S |  |
| `scheme` | `string \| null` | no | `null` | Identifier scheme, when known. | minLength: 1; pattern: \S |  |
| `issuer` | `string \| null` | no | `null` | Issuing agent, when known. | minLength: 1; pattern: \S |  |
| `uri` | `uri \| null` | no | `null` | Authoritative absolute URI for the identifier. | minLength: 1; pattern: ^[A-Za-z][A-Za-z0-9+.-]*:(?://(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|:)*@)?(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})*\|\[[A-Za-z0-9:.!$&'()*+,;=_~-]+\])(?::[0-9]*)?(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|/(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*)?\|(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|)(?:\?(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?(?:#(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?$; format: uri |  |

## Language

Represent a snapshot language using source text and/or BCP 47.

- At least one non-null value is required: source_text, tag.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `source_text` | `string \| null` | no | `null` | Displayed language label, when present. | minLength: 1; pattern: \S |  |
| `tag` | `string \| null` | no | `null` | Canonical BCP 47 language tag. | minLength: 1; pattern: ^(?:(?:[A-Za-z]{2,3}(?:-[A-Za-z]{3}){0,3}\|[A-Za-z]{4}\|[A-Za-z]{5,8})(?:-[A-Za-z]{4})?(?:-(?:[A-Za-z]{2}\|[0-9]{3}))?(?:-(?:[A-Za-z0-9]{5,8}\|[0-9][A-Za-z0-9]{3}))*(?:-[0-9A-WY-Za-wy-z](?:-[A-Za-z0-9]{2,8})+)*(?:-[xX](?:-[A-Za-z0-9]{1,8})+)?\|[xX](?:-[A-Za-z0-9]{1,8})+\|en-GB-oed\|i-ami\|i-bnn\|i-default\|i-enochian\|i-hak\|i-klingon\|i-lux\|i-mingo\|i-navajo\|i-pwn\|i-tao\|i-tay\|i-tsu\|sgn-BE-FR\|sgn-BE-NL\|sgn-CH-DE\|art-lojban\|cel-gaulish\|no-bok\|no-nyn\|zh-guoyu\|zh-hakka\|zh-min\|zh-min-nan\|zh-xiang)$ | [IETF/IANA BCP 47](https://www.iana.org/assignments/language-subtag-registry/); release: not pinned; syntax only |

## Place

Represent a source-grounded place with optional standard identifiers.

- At least one non-null value is required: source_text, name.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `source_text` | `string \| null` | no | `null` | Displayed place expression. | minLength: 1; pattern: \S |  |
| `name` | `string \| null` | no | `null` | Preferred place name. | minLength: 1; pattern: \S |  |
| `country_code` | `string \| null` | no | `null` | ISO 3166-1 alpha-2 country code. | pattern: ^[A-Z]{2}$ | [ISO ISO 3166-1](https://www.iso.org/iso-3166-country-codes.html); release: not pinned; syntax only |
| `subdivision_code` | `string \| null` | no | `null` | ISO 3166-2 subdivision code. | pattern: ^[A-Z]{2}-[A-Z0-9]{1,3}$ | [ISO ISO 3166-2](https://www.iso.org/iso-3166-country-codes.html); release: not pinned; syntax only |
| `m49_code` | `string \| null` | no | `null` | UN M49 statistical-area code. | pattern: ^[0-9]{3}$ | [United Nations M49](https://unstats.un.org/unsd/methodology/m49/); release: not pinned; syntax only |
| `identifiers` | `array[Identifier] \| null` | no | `null` | Other authoritative identifiers. | minItems: 1 |  |

## PresentationRole

Identify a dimension's explicit table-presentation role.

`row`, `column`

## Project

Represent project, program, operation, or initiative context.

- At least one non-null value is required: name, identifiers, components.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `name` | `string \| null` | no | `null` | Associated project-context name. | minLength: 1; pattern: \S | [https://schema.org/name](https://schema.org/name) (exact) |
| `identifiers` | `array[Identifier] \| null` | no | `null` | Formal project identifiers. | minItems: 1 | [https://schema.org/identifier](https://schema.org/identifier) (standard_broader) |
| `components` | `array[EntityReference] \| null` | no | `null` | Named project components. | minItems: 1 | [https://schema.org/hasPart](https://schema.org/hasPart) (related_structural) |

## Provenance

Separate derivation sources from credited agents.

- At least one non-null value is required: sources, attributions.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `sources` | `array[EntityReference] \| null` | no | `null` | Represented-data derivation sources. | minItems: 1 | [http://www.w3.org/ns/prov#wasDerivedFrom](http://www.w3.org/ns/prov#wasDerivedFrom) (related_structural), [http://purl.org/dc/terms/source](http://purl.org/dc/terms/source) (close) |
| `attributions` | `array[Attribution] \| null` | no | `null` | Role-bearing credited agents. | minItems: 1 | [http://www.w3.org/ns/prov#wasAttributedTo](http://www.w3.org/ns/prov#wasAttributedTo) (related_structural) |

## StatisticalFormTerm

Represent a known or source-only statistical form.

- At least one of source_text, normalized_value, code, or uri must be non-null.

- A non-null code requires a non-null scheme.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `source_text` | `string \| null` | no | `null` | Faithful source-visible expression. | minLength: 1; pattern: \S |  |
| `normalized_value` | `StatisticalFormValue \| null` | no | `null` | Approved normalized statistical form. |  |  |
| `code` | `string \| null` | no | `null` | Code in the named scheme. | minLength: 1; pattern: \S |  |
| `scheme` | `string \| null` | no | `null` | Code-list or vocabulary identifier. | minLength: 1; pattern: \S |  |
| `uri` | `uri \| null` | no | `null` | Authoritative URI for the represented concept. | minLength: 1; pattern: ^[A-Za-z][A-Za-z0-9+.-]*:(?://(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|:)*@)?(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})*\|\[[A-Za-z0-9:.!$&'()*+,;=_~-]+\])(?::[0-9]*)?(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|/(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*)?\|(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|)(?:\?(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?(?:#(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?$; format: uri |  |

## StatisticalFormValue

Enumerate approved normalized statistical forms.

`observed_value`, `count`, `arithmetic_mean`, `geometric_mean`, `weighted_mean`, `weighted_value`, `median`, `sum`, `weighted_sum`, `minimum`, `maximum`, `range`, `interquartile_range`, `variance`, `standard_deviation`, `standard_error`, `mean_absolute_deviation`, `median_absolute_deviation`, `skewness`, `kurtosis`, `lower_bound`, `upper_bound`, `score`, `rank`, `index`, `rate`, `harmonic_mean`, `trimmed_mean`, `mode`, `coefficient_of_variation`, `valid_cases`, `invalid_cases`, `percentage_of_valid_cases`, `percentage_of_invalid_cases`, `quartile`, `quintile`, `decile`, `percentile`, `ratio`, `proportion`, `percentage`, `confidence_interval`, `coefficient`, `p_value`, `change`

## TemporalCoverage

Group represented-data time and granularity.

- At least one non-null value is required: period, granularity.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `period` | `TemporalExpression \| null` | no | `null` | Represented-data temporal expression. |  | [https://schema.org/temporalCoverage](https://schema.org/temporalCoverage) (exact), [http://purl.org/dc/terms/temporal](http://purl.org/dc/terms/temporal) (close) |
| `granularity` | `TemporalGranularityTerm \| null` | no | `null` | Reporting interval or temporal resolution. |  |  |

## TemporalExpression

Represent source-visible time with optional normalized bounds.

- Normalized bounds require relation and precision; source-only expressions omit both.

- point and as_of require start only; interval requires both bounds; open_interval requires exactly one bound.

- Bounds must match the declared precision. Python additionally validates calendar dates and chronological ordering.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `source_text` | `string` | yes | — | Complete source time expression. | minLength: 1; pattern: \S |  |
| `start` | `string \| null` | no | `null` | Normalized start. | minLength: 1; pattern: \S |  |
| `end` | `string \| null` | no | `null` | Normalized end. | minLength: 1; pattern: \S |  |
| `relation` | `TemporalRelation \| null` | no | `null` | Relationship between normalized bounds. |  |  |
| `precision` | `TemporalPrecision \| null` | no | `null` | Precision of normalized bounds. |  |  |

## TemporalGranularityTerm

Represent a known or source-only temporal granularity.

- At least one of source_text, normalized_value, code, or uri must be non-null.

- A non-null code requires a non-null scheme.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `source_text` | `string \| null` | no | `null` | Faithful source-visible expression. | minLength: 1; pattern: \S |  |
| `normalized_value` | `TemporalGranularityValue \| null` | no | `null` | Approved normalized temporal granularity. |  |  |
| `code` | `string \| null` | no | `null` | Code in the named scheme. | minLength: 1; pattern: \S |  |
| `scheme` | `string \| null` | no | `null` | Code-list or vocabulary identifier. | minLength: 1; pattern: \S |  |
| `uri` | `uri \| null` | no | `null` | Authoritative URI for the represented concept. | minLength: 1; pattern: ^[A-Za-z][A-Za-z0-9+.-]*:(?://(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|:)*@)?(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})*\|\[[A-Za-z0-9:.!$&'()*+,;=_~-]+\])(?::[0-9]*)?(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|/(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*)?\|(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|)(?:\?(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?(?:#(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?$; format: uri |  |

## TemporalGranularityValue

Enumerate approved normalized temporal granularities.

`hourly`, `daily`, `weekly`, `monthly`, `quarterly`, `semiannual`, `annual`, `instantaneous`, `event_based`, `multi_year`, `irregular`

## TemporalPrecision

Describe the precision of normalized temporal bounds.

`year`, `month`, `day`, `datetime`

## TemporalRelation

Describe how normalized temporal bounds form an expression.

`point`, `interval`, `open_interval`, `as_of`

## Unit

Represent a displayed unit and its optional normalized qualifiers.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `source_text` | `string` | yes | — | Displayed unit expression. | minLength: 1; pattern: \S |  |
| `code` | `string \| null` | no | `null` | Exact UN/CEFACT Recommendation 20 common code. | pattern: ^[A-Z0-9]{1,3}$ | [UNECE Recommendation 20](https://unece.org/trade/uncefact/cl-recommendations); release: not pinned; syntax only |
| `multiplier_exponent` | `integer \| null` | no | `null` | Base-10 SDMX unit-multiplier exponent. |  | [SDMX CL_UNIT_MULT](https://registry.sdmx.org/items/codelist.html); release: 1.1 |

## Variable

Represent a measured variable and its applicable qualifiers.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `name` | `string` | yes | — | Explicitly named measured concept. | minLength: 1; pattern: \S | [https://schema.org/variableMeasured](https://schema.org/variableMeasured) (close) |
| `unit` | `Unit \| null` | no | `null` | Applicable unit. |  | [https://schema.org/unitCode](https://schema.org/unitCode) (related_structural) |
| `currency` | `Currency \| null` | no | `null` | Applicable currency. |  | [https://schema.org/currency](https://schema.org/currency) (close) |
| `analytical_roles` | `array[AnalyticalRole] \| null` | no | `null` | Explicit analytical or axis roles. | minItems: 1 |  |
| `statistical_forms` | `array[StatisticalFormTerm] \| null` | no | `null` | Applicable statistical forms. | minItems: 1 | [https://schema.org/statType](https://schema.org/statType) (close) |

## VisualizationTypeTerm

Represent a known or source-only visualization type.

- At least one of source_text, normalized_value, code, or uri must be non-null.

- A non-null code requires a non-null scheme.

| Field | Type | Required | Default | Description | Constraints | Standards / code list |
|---|---|---:|---|---|---|---|
| `source_text` | `string \| null` | no | `null` | Faithful source-visible expression. | minLength: 1; pattern: \S |  |
| `normalized_value` | `VisualizationTypeValue \| null` | no | `null` | Approved normalized visualization type. |  |  |
| `code` | `string \| null` | no | `null` | Code in the named scheme. | minLength: 1; pattern: \S |  |
| `scheme` | `string \| null` | no | `null` | Code-list or vocabulary identifier. | minLength: 1; pattern: \S |  |
| `uri` | `uri \| null` | no | `null` | Authoritative URI for the represented concept. | minLength: 1; pattern: ^[A-Za-z][A-Za-z0-9+.-]*:(?://(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|:)*@)?(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})*\|\[[A-Za-z0-9:.!$&'()*+,;=_~-]+\])(?::[0-9]*)?(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|/(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*)?\|(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|)(?:\?(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?(?:#(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?$; format: uri |  |

## VisualizationTypeValue

Enumerate approved normalized visualization types.

`table`, `bar_chart`, `line_chart`, `area_chart`, `pie_chart`, `donut_chart`, `scatter_plot`, `bubble_chart`, `dot_plot`, `histogram`, `density_plot`, `heatmap`, `box_plot`, `violin_plot`, `error_bar`, `error_band`, `radar_chart`, `treemap`, `map`, `choropleth_map`, `symbol_map`, `network_diagram`, `flow_diagram`, `timeline`, `diagram`, `infographic`, `dashboard`, `composite_figure`
