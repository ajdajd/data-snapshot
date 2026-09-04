# Data Snapshot Metadata Schema v1.2 Reference

<!-- Generated from DataSnapshotMetadata. Do not edit manually. -->

Represent canonical semantic metadata for one data snapshot.

Parameters
----------
title : str | None
    Primary title, caption, or heading.
document_label : str | None
    Label assigned within the parent source document.
subject_domains : list[ControlledTerm] | None
    Broad thematic, policy, or sectoral domains.
subject_summary : str | None
    Concise analytical summary.
panel_titles : list[str] | None
    Ordered explicit panel titles.
variables : list[Variable] | None
    Measured concepts and their qualifiers.
dimensions : list[Dimension] | None
    Classificatory dimensions and visible organization.
population_group : ControlledTerm | None
    Human population represented by the data.
visualization_types : list[VisualizationTypeTerm] | None
    Visible visualization forms.
temporal_coverage : TemporalCoverage | None
    Represented-data time and granularity.
geographic_coverage : GeographicCoverage | None
    Geographic scope, locations, and level.
comparisons : list[str] | None
    Explicit comparisons or named comparators.
provenance : Provenance | None
    Derivation sources and artifact attributions.
languages : list[Language] | None
    Languages used within the snapshot.
interpretive_notes : list[str] | None
    Complete source-visible interpretive statements.
project : Project | None
    Associated project or operational context.
intervention_types : list[ControlledTerm] | None
    Represented interventions or activities.
financing : Financing | None
    Project-financing context.
analysis_methods : list[ControlledTerm] | None
    Explicit analytical methods.
data_collection_methods : list[ControlledTerm] | None
    Explicit data-collection methods.

Schema version: `1.2`

## Snapshot fields

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `title` | `string \| null` | no | `null` | Primary title, caption, or heading identifying the snapshot. | [http://purl.org/dc/terms/title](http://purl.org/dc/terms/title) (exact), [https://schema.org/name](https://schema.org/name) (exact) |
| `document_label` | `string \| null` | no | `null` | Label assigned within the parent source document. | [https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/label.html](https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/label.html) (close), [https://schema.org/identifier](https://schema.org/identifier) (standard_broader) |
| `subject_domains` | `array[ControlledTerm] \| null` | no | `null` | Broad thematic, policy, or sectoral domains. | [http://purl.org/dc/terms/subject](http://purl.org/dc/terms/subject) (standard_broader), [https://schema.org/about](https://schema.org/about) (standard_broader) |
| `subject_summary` | `string \| null` | no | `null` | Concise summary of the primary analytical subject or purpose. | [https://schema.org/abstract](https://schema.org/abstract) (close), [http://purl.org/dc/terms/description](http://purl.org/dc/terms/description) (standard_broader) |
| `panel_titles` | `array[string] \| null` | no | `null` | Ordered titles explicitly shown for individual panels. | [https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/fig-group.html](https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/fig-group.html) (close), [https://schema.org/hasPart](https://schema.org/hasPart) (related_structural) |
| `variables` | `array[Variable] \| null` | no | `null` | Explicitly named measured concepts and their qualifiers. | [https://schema.org/variableMeasured](https://schema.org/variableMeasured) (close), [https://ddialliance.org/Specification/DDI-Lifecycle/3.3/](https://ddialliance.org/Specification/DDI-Lifecycle/3.3/) (close) |
| `dimensions` | `array[Dimension] \| null` | no | `null` | Classificatory dimensions and their visible organization. | [https://sdmx.org/](https://sdmx.org/) (close), [https://ddialliance.org/Specification/DDI-Lifecycle/3.3/](https://ddialliance.org/Specification/DDI-Lifecycle/3.3/) (close) |
| `population_group` | `ControlledTerm \| null` | no | `null` | Human population or beneficiary group represented by the data. | [https://docs.ddialliance.org/DDI-Lifecycle/3.3/xmlschema/schemas/conceptualcomponent_xsd/elements/Universe.html](https://docs.ddialliance.org/DDI-Lifecycle/3.3/xmlschema/schemas/conceptualcomponent_xsd/elements/Universe.html) (close), [https://schema.org/populationType](https://schema.org/populationType) (close) |
| `visualization_types` | `array[VisualizationTypeTerm] \| null` | no | `null` | Explicitly visible visualization forms used by the snapshot. | [http://purl.org/dc/terms/type](http://purl.org/dc/terms/type) (standard_broader), [https://schema.org/additionalType](https://schema.org/additionalType) (standard_broader) |
| `temporal_coverage` | `TemporalCoverage \| null` | no | `null` | When the represented data apply and their granularity. | [https://schema.org/temporalCoverage](https://schema.org/temporalCoverage) (exact), [http://purl.org/dc/terms/temporal](http://purl.org/dc/terms/temporal) (close) |
| `geographic_coverage` | `GeographicCoverage \| null` | no | `null` | Overall geographic scope, additional locations, and level. | [https://schema.org/spatialCoverage](https://schema.org/spatialCoverage) (exact), [http://purl.org/dc/terms/spatial](http://purl.org/dc/terms/spatial) (exact) |
| `comparisons` | `array[string] \| null` | no | `null` | Explicit comparative expressions or named comparators. |  |
| `provenance` | `Provenance \| null` | no | `null` | Represented-data sources and artifact attributions. | [http://www.w3.org/ns/prov#wasDerivedFrom](http://www.w3.org/ns/prov#wasDerivedFrom) (related_structural), [http://www.w3.org/ns/prov#wasAttributedTo](http://www.w3.org/ns/prov#wasAttributedTo) (related_structural) |
| `languages` | `array[Language] \| null` | no | `null` | Languages explicitly used within the snapshot. | [https://schema.org/inLanguage](https://schema.org/inLanguage) (exact), [http://purl.org/dc/terms/language](http://purl.org/dc/terms/language) (exact) |
| `interpretive_notes` | `array[string] \| null` | no | `null` | Complete explanatory, methodological, uncertainty, sample-size, or provenance statements. | [http://purl.org/dc/terms/description](http://purl.org/dc/terms/description) (standard_broader), [https://schema.org/description](https://schema.org/description) (standard_broader) |
| `project` | `Project \| null` | no | `null` | Associated project, program, operation, or initiative. | [https://schema.org/Project](https://schema.org/Project) (standard_narrower), [https://iatistandard.org/en/iati-standard/203/activity-standard/](https://iatistandard.org/en/iati-standard/203/activity-standard/) (close) |
| `intervention_types` | `array[ControlledTerm] \| null` | no | `null` | Explicit interventions, services, policies, or operational activities. |  |
| `financing` | `Financing \| null` | no | `null` | Project-financing measures, funders, and instruments. | [https://schema.org/funder](https://schema.org/funder) (exact), [https://reference.codeforiati.org/codelists/FinanceType/](https://reference.codeforiati.org/codelists/FinanceType/) (close) |
| `analysis_methods` | `array[ControlledTerm] \| null` | no | `null` | Explicit analytical, statistical, or computational methods. | [https://schema.org/measurementTechnique](https://schema.org/measurementTechnique) (related_structural), [http://www.w3.org/ns/prov#Activity](http://www.w3.org/ns/prov#Activity) (related_structural) |
| `data_collection_methods` | `array[ControlledTerm] \| null` | no | `null` | Explicit methods or instruments used to collect underlying data. | [https://docs.ddialliance.org/DDI-Lifecycle/3.3/model/composite-types/ModeOfCollectionType/](https://docs.ddialliance.org/DDI-Lifecycle/3.3/model/composite-types/ModeOfCollectionType/) (exact), [https://schema.org/measurementMethod](https://schema.org/measurementMethod) (close) |

## AnalyticalRole

Identify an explicitly stated analytical or axis role.

`outcome`, `predictor`, `instrumental`, `control`, `x_axis`, `y_axis`

## Attribution

Represent a named agent and its explicit attribution role.

Parameters
----------
name : str
    Source-visible credited-agent name.
identifiers : list[Identifier] | None
    Assigned identifiers for the agent.
role : ControlledTerm
    Open, source-grounded attribution role.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `name` | `string` | yes | — | Source-visible entity name. |  |
| `identifiers` | `array[Identifier] \| null` | no | `null` | Assigned entity identifiers. |  |
| `role` | `ControlledTerm` | yes | — | Explicit source-grounded agent role. |  |

## CategoryGroup

Represent one explicit nonrecursive category grouping.

Parameters
----------
name : str
    Explicit group heading.
categories : list[ControlledTerm]
    Categories directly contained by the group.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `name` | `string` | yes | — | Explicit category-group heading. |  |
| `categories` | `array[ControlledTerm]` | yes | — | Categories directly contained by the group. |  |

## ControlledTerm

Represent a source-grounded term with optional normalization.

Parameters
----------
source_text : str | None
    Faithful source-visible expression.
normalized_value : str | None
    Preferred application or vocabulary value.
code : str | None
    Code in the named scheme.
scheme : str | None
    Code-list or vocabulary identifier.
uri : AnyUrl | None
    Authoritative URI for the represented concept.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | Faithful source-visible expression. |  |
| `normalized_value` | `string \| null` | no | `null` | Preferred application or vocabulary value. |  |
| `code` | `string \| null` | no | `null` | Code in the named scheme. |  |
| `scheme` | `string \| null` | no | `null` | Code-list or vocabulary identifier. |  |
| `uri` | `uri \| null` | no | `null` | Authoritative URI for the represented concept. |  |

## Currency

Represent a displayed currency and optional ISO 4217 code.

Parameters
----------
source_text : str
    Displayed currency expression.
code : str | None
    Uppercase ISO 4217 alphabetic code.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `source_text` | `string` | yes | — | Displayed currency expression. |  |
| `code` | `string \| null` | no | `null` | Uppercase ISO 4217 alphabetic code. |  |

## Dimension

Represent a classificatory dimension and its visible organization.

Parameters
----------
name : str
    Dimension name.
categories : list[ControlledTerm] | None
    Ordered ungrouped categories.
category_groups : list[CategoryGroup] | None
    One level of explicit category groups.
presentation_roles : list[PresentationRole] | None
    Explicit row and/or column roles.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `name` | `string` | yes | — | Classificatory dimension name. |  |
| `categories` | `array[ControlledTerm] \| null` | no | `null` | Ordered ungrouped categories. |  |
| `category_groups` | `array[CategoryGroup] \| null` | no | `null` | One level of explicit category groups. |  |
| `presentation_roles` | `array[PresentationRole] \| null` | no | `null` | Explicit table-presentation roles. |  |

## EntityReference

Represent a named project, organization, source, or component.

Parameters
----------
name : str
    Source-visible entity name.
identifiers : list[Identifier] | None
    Assigned identifiers for the entity.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `name` | `string` | yes | — | Source-visible entity name. |  |
| `identifiers` | `array[Identifier] \| null` | no | `null` | Assigned entity identifiers. |  |

## Financing

Group project-financing measures, funders, and instruments.

Parameters
----------
measures : list[ControlledTerm] | None
    Financial quantities or funding-related measures.
funders : list[EntityReference] | None
    Named funding sources.
instruments : list[ControlledTerm] | None
    Financing mechanisms.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `measures` | `array[ControlledTerm] \| null` | no | `null` | Project-financing measures. |  |
| `funders` | `array[EntityReference] \| null` | no | `null` | Named funding sources. |  |
| `instruments` | `array[ControlledTerm] \| null` | no | `null` | Financing mechanisms. |  |

## GeographicCoverage

Group overall geographic scope, locations, and reporting level.

Parameters
----------
scope : Place | None
    Overall geographic coverage or focus.
locations : list[GeographicLocation] | None
    Additional named locations.
level : GeographicLevelTerm | None
    Administrative, geographic, or reporting level.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `scope` | `Place \| null` | no | `null` | Overall geographic coverage or focus. |  |
| `locations` | `array[GeographicLocation] \| null` | no | `null` | Additional named locations. |  |
| `level` | `GeographicLevelTerm \| null` | no | `null` | Geographic or reporting level. |  |

## GeographicLevelTerm

Represent a known or source-only geographic reporting level.

Parameters
----------
source_text : str | None
    Faithful source-visible expression.
normalized_value : GeographicLevelValue | None
    Approved normalized geographic level.
code : str | None
    Code in the named scheme.
scheme : str | None
    Code-list or vocabulary identifier.
uri : AnyUrl | None
    Authoritative URI for the represented concept.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | Faithful source-visible expression. |  |
| `normalized_value` | `GeographicLevelValue \| null` | no | `null` | Approved normalized geographic level. |  |
| `code` | `string \| null` | no | `null` | Code in the named scheme. |  |
| `scheme` | `string \| null` | no | `null` | Code-list or vocabulary identifier. |  |
| `uri` | `uri \| null` | no | `null` | Authoritative URI for the represented concept. |  |

## GeographicLevelValue

Enumerate approved normalized geographic levels.

`global`, `world_region`, `country`, `administrative_area_1`, `administrative_area_2`, `administrative_area_3`, `locality`, `site`

## GeographicLocation

Represent an additional named location and its optional role and type.

Parameters
----------
source_text : str | None
    Displayed place expression.
name : str | None
    Preferred place name.
country_code : str | None
    ISO 3166-1 alpha-2 country code.
subdivision_code : str | None
    ISO 3166-2 subdivision code.
m49_code : str | None
    UN M49 statistical-area code.
identifiers : list[Identifier] | None
    Other authoritative identifiers.
role : ControlledTerm | None
    Explicit source-grounded geographic role.
type : ControlledTerm | None
    Physical or administrative location type.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | Displayed place expression. |  |
| `name` | `string \| null` | no | `null` | Preferred place name. |  |
| `country_code` | `string \| null` | no | `null` | ISO 3166-1 alpha-2 country code. |  |
| `subdivision_code` | `string \| null` | no | `null` | ISO 3166-2 subdivision code. |  |
| `m49_code` | `string \| null` | no | `null` | UN M49 statistical-area code. |  |
| `identifiers` | `array[Identifier] \| null` | no | `null` | Other authoritative identifiers. |  |
| `role` | `ControlledTerm \| null` | no | `null` | Explicit source-grounded geographic role. |  |
| `type` | `ControlledTerm \| null` | no | `null` | Physical or administrative location type. |  |

## Identifier

Represent an assigned identifier and its optional authority context.

Parameters
----------
value : str
    Identifier exactly as assigned.
scheme : str | None
    Identifier scheme, when known.
issuer : str | None
    Issuing agent, when known.
uri : AnyUrl | None
    Authoritative absolute URI for the identifier.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `value` | `string` | yes | — | Identifier exactly as assigned. |  |
| `scheme` | `string \| null` | no | `null` | Identifier scheme, when known. |  |
| `issuer` | `string \| null` | no | `null` | Issuing agent, when known. |  |
| `uri` | `uri \| null` | no | `null` | Authoritative absolute URI for the identifier. |  |

## Language

Represent a snapshot language using source text and/or BCP 47.

Parameters
----------
source_text : str | None
    Displayed language label, when present.
tag : str | None
    Canonical BCP 47 language tag.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | Displayed language label, when present. |  |
| `tag` | `string \| null` | no | `null` | Canonical BCP 47 language tag. |  |

## Place

Represent a source-grounded place with optional standard identifiers.

Parameters
----------
source_text : str | None
    Displayed place expression.
name : str | None
    Preferred place name.
country_code : str | None
    ISO 3166-1 alpha-2 country code.
subdivision_code : str | None
    ISO 3166-2 subdivision code.
m49_code : str | None
    UN M49 statistical-area code.
identifiers : list[Identifier] | None
    Other authoritative identifiers.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | Displayed place expression. |  |
| `name` | `string \| null` | no | `null` | Preferred place name. |  |
| `country_code` | `string \| null` | no | `null` | ISO 3166-1 alpha-2 country code. |  |
| `subdivision_code` | `string \| null` | no | `null` | ISO 3166-2 subdivision code. |  |
| `m49_code` | `string \| null` | no | `null` | UN M49 statistical-area code. |  |
| `identifiers` | `array[Identifier] \| null` | no | `null` | Other authoritative identifiers. |  |

## PresentationRole

Identify a dimension's explicit table-presentation role.

`row`, `column`

## Project

Represent project, program, operation, or initiative context.

Parameters
----------
name : str | None
    Associated project-context name.
identifiers : list[Identifier] | None
    Formal project or operation identifiers.
components : list[EntityReference] | None
    Explicitly identified subordinate components.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `name` | `string \| null` | no | `null` | Associated project-context name. |  |
| `identifiers` | `array[Identifier] \| null` | no | `null` | Formal project identifiers. |  |
| `components` | `array[EntityReference] \| null` | no | `null` | Named project components. |  |

## Provenance

Separate derivation sources from credited agents.

Parameters
----------
sources : list[EntityReference] | None
    Entities from which represented data derive.
attributions : list[Attribution] | None
    Agents explicitly credited for the snapshot artifact.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `sources` | `array[EntityReference] \| null` | no | `null` | Represented-data derivation sources. |  |
| `attributions` | `array[Attribution] \| null` | no | `null` | Role-bearing credited agents. |  |

## StatisticalFormTerm

Represent a known or source-only statistical form.

Parameters
----------
source_text : str | None
    Faithful source-visible expression.
normalized_value : StatisticalFormValue | None
    Approved normalized statistical form.
code : str | None
    Code in the named scheme.
scheme : str | None
    Code-list or vocabulary identifier.
uri : AnyUrl | None
    Authoritative URI for the represented concept.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | Faithful source-visible expression. |  |
| `normalized_value` | `StatisticalFormValue \| null` | no | `null` | Approved normalized statistical form. |  |
| `code` | `string \| null` | no | `null` | Code in the named scheme. |  |
| `scheme` | `string \| null` | no | `null` | Code-list or vocabulary identifier. |  |
| `uri` | `uri \| null` | no | `null` | Authoritative URI for the represented concept. |  |

## StatisticalFormValue

Enumerate approved normalized statistical forms.

`observed_value`, `count`, `arithmetic_mean`, `geometric_mean`, `weighted_mean`, `weighted_value`, `median`, `sum`, `weighted_sum`, `minimum`, `maximum`, `range`, `interquartile_range`, `variance`, `standard_deviation`, `standard_error`, `mean_absolute_deviation`, `median_absolute_deviation`, `skewness`, `kurtosis`, `lower_bound`, `upper_bound`, `score`, `rank`, `index`, `rate`, `harmonic_mean`, `trimmed_mean`, `mode`, `coefficient_of_variation`, `valid_cases`, `invalid_cases`, `percentage_of_valid_cases`, `percentage_of_invalid_cases`, `quartile`, `quintile`, `decile`, `percentile`, `ratio`, `proportion`, `percentage`, `confidence_interval`, `coefficient`, `p_value`, `change`

## TemporalCoverage

Group represented-data time and granularity.

Parameters
----------
period : TemporalExpression | None
    Represented-data temporal expression.
granularity : TemporalGranularityTerm | None
    Reporting interval or temporal resolution.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `period` | `TemporalExpression \| null` | no | `null` | Represented-data temporal expression. |  |
| `granularity` | `TemporalGranularityTerm \| null` | no | `null` | Reporting interval or temporal resolution. |  |

## TemporalExpression

Represent source-visible time with optional normalized bounds.

Parameters
----------
source_text : str
    Complete source expression.
start : str | None
    Normalized starting value.
end : str | None
    Normalized ending value.
relation : TemporalRelation | None
    Relationship between the normalized bounds.
precision : TemporalPrecision | None
    Precision shared by the normalized bounds.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `source_text` | `string` | yes | — | Complete source time expression. |  |
| `start` | `string \| null` | no | `null` | Normalized start. |  |
| `end` | `string \| null` | no | `null` | Normalized end. |  |
| `relation` | `TemporalRelation \| null` | no | `null` | Relationship between normalized bounds. |  |
| `precision` | `TemporalPrecision \| null` | no | `null` | Precision of normalized bounds. |  |

## TemporalGranularityTerm

Represent a known or source-only temporal granularity.

Parameters
----------
source_text : str | None
    Faithful source-visible expression.
normalized_value : TemporalGranularityValue | None
    Approved normalized temporal granularity.
code : str | None
    Code in the named scheme.
scheme : str | None
    Code-list or vocabulary identifier.
uri : AnyUrl | None
    Authoritative URI for the represented concept.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | Faithful source-visible expression. |  |
| `normalized_value` | `TemporalGranularityValue \| null` | no | `null` | Approved normalized temporal granularity. |  |
| `code` | `string \| null` | no | `null` | Code in the named scheme. |  |
| `scheme` | `string \| null` | no | `null` | Code-list or vocabulary identifier. |  |
| `uri` | `uri \| null` | no | `null` | Authoritative URI for the represented concept. |  |

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

Parameters
----------
source_text : str
    Displayed unit expression.
code : str | None
    Exact UN/CEFACT Recommendation 20 code.
multiplier_exponent : int | None
    SDMX unit-multiplier exponent.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `source_text` | `string` | yes | — | Displayed unit expression. |  |
| `code` | `string \| null` | no | `null` | Exact UN/CEFACT Recommendation 20 common code. |  |
| `multiplier_exponent` | `integer \| null` | no | `null` | Base-10 SDMX unit-multiplier exponent. |  |

## Variable

Represent a measured variable and its applicable qualifiers.

Parameters
----------
name : str
    Explicitly named variable, indicator, metric, or measured concept.
unit : Unit | None
    Applicable unit.
currency : Currency | None
    Applicable currency.
analytical_roles : list[AnalyticalRole] | None
    Explicit analytical or axis roles.
statistical_forms : list[StatisticalFormTerm] | None
    Applicable statistical forms.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `name` | `string` | yes | — | Explicitly named measured concept. |  |
| `unit` | `Unit \| null` | no | `null` | Applicable unit. |  |
| `currency` | `Currency \| null` | no | `null` | Applicable currency. |  |
| `analytical_roles` | `array[AnalyticalRole] \| null` | no | `null` | Explicit analytical or axis roles. |  |
| `statistical_forms` | `array[StatisticalFormTerm] \| null` | no | `null` | Applicable statistical forms. |  |

## VisualizationTypeTerm

Represent a known or source-only visualization type.

Parameters
----------
source_text : str | None
    Faithful source-visible expression.
normalized_value : VisualizationTypeValue | None
    Approved normalized visualization type.
code : str | None
    Code in the named scheme.
scheme : str | None
    Code-list or vocabulary identifier.
uri : AnyUrl | None
    Authoritative URI for the represented concept.

| Field | Type | Required | Default | Description | Standards |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | Faithful source-visible expression. |  |
| `normalized_value` | `VisualizationTypeValue \| null` | no | `null` | Approved normalized visualization type. |  |
| `code` | `string \| null` | no | `null` | Code in the named scheme. |  |
| `scheme` | `string \| null` | no | `null` | Code-list or vocabulary identifier. |  |
| `uri` | `uri \| null` | no | `null` | Authoritative URI for the represented concept. |  |

## VisualizationTypeValue

Enumerate approved normalized visualization types.

`table`, `bar_chart`, `line_chart`, `area_chart`, `pie_chart`, `donut_chart`, `scatter_plot`, `bubble_chart`, `dot_plot`, `histogram`, `density_plot`, `heatmap`, `box_plot`, `violin_plot`, `error_bar`, `error_band`, `radar_chart`, `treemap`, `map`, `choropleth_map`, `symbol_map`, `network_diagram`, `flow_diagram`, `timeline`, `diagram`, `infographic`, `dashboard`, `composite_figure`
