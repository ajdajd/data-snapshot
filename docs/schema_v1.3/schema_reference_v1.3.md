# Data Snapshot Metadata Schema v1.3 Reference

<!-- Generated from DataSnapshotMetadata. Do not edit manually. -->

Represent canonical semantic metadata for one data snapshot.

Schema version: `1.3`

## Validation and serialization

- Python is the canonical validator. JSON Schema enforces exported structural rules; format assertions require a format-aware validator.
- Python additionally applies NFC normalization, outer whitespace trimming, and stable exact deduplication.
- Python additionally checks URI syntax before URL normalization, language-tag casing and uniqueness, calendar dates, and chronological ordering.
- Missing and null values are equivalent. Serialize records with exclude_none=True to omit unavailable values.
- External registry membership, source-grounding, and semantic correctness are not validated. Unpinned code-list metadata identifies a syntax authority only.

## Snapshot fields

Fields are grouped by the v1.3 semantic modules.

Each block is one possible field value. Examples for different fields are independent and should not be combined into a record automatically. They illustrate the schema and do not constrain accepted values. URIs under example.org are illustrative placeholders.

### Identity and discovery

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `title` | `string \| null` | no | `null` | minLength: 1; pattern: \S | [http://purl.org/dc/terms/title](http://purl.org/dc/terms/title) (exact), [https://schema.org/name](https://schema.org/name) (exact) |
| `document_label` | `string \| null` | no | `null` | minLength: 1; pattern: \S | [https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/label.html](https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/label.html) (close), [https://schema.org/identifier](https://schema.org/identifier) (standard_broader) |
| `subject_domains` | `array[string] \| null` | no | `null` | minItems: 1 | [http://purl.org/dc/terms/subject](http://purl.org/dc/terms/subject) (standard_broader), [https://schema.org/about](https://schema.org/about) (standard_broader) |
| `subject_summary` | `string \| null` | no | `null` | minLength: 1; pattern: \S | [https://schema.org/abstract](https://schema.org/abstract) (close), [http://purl.org/dc/terms/description](http://purl.org/dc/terms/description) (standard_broader) |
| `panel_titles` | `array[string] \| null` | no | `null` | minItems: 1 | [https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/fig-group.html](https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/fig-group.html) (close), [https://schema.org/hasPart](https://schema.org/hasPart) (related_structural) |

#### Field definitions and examples

##### `title`

**Definition**

The primary title, caption, or heading that identifies the data snapshot.

**Examples**

```json
"Inflation Rate by Country"
```

```json
"Annual Government Expenditure"
```

```json
"Monthly labor income in Afghanistan and remittances from abroad"
```

```json
"Table 6: Determinants of illegal land reallocation at village level"
```


##### `document_label`

**Definition**

A document-assigned identifier used to reference the snapshot within the source document.

**Examples**

```json
"Figure 3"
```

```json
"Table 4.2"
```

```json
"Annex B"
```

```json
"Exhibit 7"
```


##### `subject_domains`

**Definition**

The broad thematic, policy, or sectoral domain represented by the snapshot.

**Examples**

```json
[
  "Education"
]
```

```json
[
  "Health"
]
```

```json
[
  "Macroeconomics"
]
```

```json
[
  "Agriculture"
]
```

```json
[
  "Forced Displacement"
]
```


##### `subject_summary`

**Definition**

A concise summary describing the primary analytical subject or purpose of the snapshot.

**Examples**

```json
"Trends in primary school enrollment"
```

```json
"Distribution of humanitarian funding"
```

```json
"Comparison of poverty rates across regions"
```


##### `panel_titles`

**Definition**

The title or heading of an individual panel within a multi-panel snapshot.

Populate only when panel titles are explicitly present.

**Examples**

```json
[
  "(A) Poverty Rate"
]
```

```json
[
  "(B) Literacy Rate"
]
```

```json
[
  "Monthly Returns"
]
```


### Subject and semantics

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `variables` | `array[Variable] \| null` | no | `null` | minItems: 1 | [https://schema.org/variableMeasured](https://schema.org/variableMeasured) (close), [https://ddialliance.org/Specification/DDI-Lifecycle/3.3/](https://ddialliance.org/Specification/DDI-Lifecycle/3.3/) (close) |
| `dimensions` | `array[Dimension] \| null` | no | `null` | minItems: 1 | [https://sdmx.org/](https://sdmx.org/) (close), [https://ddialliance.org/Specification/DDI-Lifecycle/3.3/](https://ddialliance.org/Specification/DDI-Lifecycle/3.3/) (close) |
| `population_group` | `string \| null` | no | `null` | minLength: 1; pattern: \S | [https://docs.ddialliance.org/DDI-Lifecycle/3.3/xmlschema/schemas/conceptualcomponent_xsd/elements/Universe.html](https://docs.ddialliance.org/DDI-Lifecycle/3.3/xmlschema/schemas/conceptualcomponent_xsd/elements/Universe.html) (close), [https://schema.org/populationType](https://schema.org/populationType) (close) |

#### Field definitions and examples

##### `variables`

**Definition**

Measured concepts and their applicable qualifiers.

Populate `name` when the measured concept can be identified from the snapshot. Otherwise return `null` rather than using a unit, `%`, `Value`, `Unknown`, or another placeholder as the name; retain the variable only when it contains a unit, currency, or statistical form. Analytical roles and axis assignments require a named measured concept. Repeat a shared unit, currency, multiplier, or statistical form on every variable to which it applies. Do not use a variable as a shared-default object.

**Examples**

```json
[
  {
    "name": "GDP Growth"
  }
]
```

```json
[
  {
    "name": "Inflation"
  }
]
```

```json
[
  {
    "name": "Literacy Rate"
  }
]
```

```json
[
  {
    "name": "Refugee Population"
  }
]
```

```json
[
  {
    "name": null,
    "unit": {
      "source_text": "%"
    }
  }
]
```

```json
[
  {
    "currency": {
      "code": "USD",
      "source_text": "US$"
    },
    "name": "Revenue",
    "unit": {
      "multiplier_exponent": 6,
      "source_text": "US$ millions"
    }
  },
  {
    "currency": {
      "code": "USD",
      "source_text": "US$"
    },
    "name": "Operating cost",
    "unit": {
      "multiplier_exponent": 6,
      "source_text": "US$ millions"
    }
  }
]
```


##### `dimensions`

**Definition**

Classificatory dimensions and their visible organization.

**Examples**

```json
[
  {
    "name": "Country"
  }
]
```

```json
[
  {
    "name": "Year"
  }
]
```

```json
[
  {
    "name": "Education Level"
  }
]
```

```json
[
  {
    "name": "Industry Sector"
  }
]
```

```json
[
  {
    "name": "Scenario"
  }
]
```

```json
[
  {
    "name": "Country",
    "presentation_roles": [
      "row"
    ]
  }
]
```

```json
[
  {
    "name": "Indicator",
    "presentation_roles": [
      "row"
    ]
  }
]
```

```json
[
  {
    "name": "Sector",
    "presentation_roles": [
      "row"
    ]
  }
]
```

```json
[
  {
    "name": "Year",
    "presentation_roles": [
      "column"
    ]
  }
]
```

```json
[
  {
    "name": "Region",
    "presentation_roles": [
      "column"
    ]
  }
]
```

```json
[
  {
    "name": "Funding Source",
    "presentation_roles": [
      "column"
    ]
  }
]
```


##### `population_group`

**Definition**

The human population, beneficiary group, or demographic group that is the primary subject of the represented data. This field describes who the data are about, not how they are categorized or disaggregated.

**Examples**

```json
"Refugees"
```

```json
"Children under five"
```

```json
"Female respondents"
```

```json
"Host communities"
```

```json
"Technical education graduates"
```


### Temporal context

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `temporal_coverage` | `TemporalCoverage \| null` | no | `null` |  | [https://schema.org/temporalCoverage](https://schema.org/temporalCoverage) (exact), [http://purl.org/dc/terms/temporal](http://purl.org/dc/terms/temporal) (close) |

#### Field definitions and examples

##### `temporal_coverage`

**Definition**

When the represented data apply and their granularity.

**Examples**

```json
{
  "period": {
    "end": "2020",
    "precision": "year",
    "relation": "interval",
    "source_text": "2015–2020",
    "start": "2015"
  }
}
```

```json
{
  "period": {
    "source_text": "FY2023"
  }
}
```

```json
{
  "period": {
    "precision": "month",
    "relation": "point",
    "source_text": "January 2024",
    "start": "2024-01"
  }
}
```

```json
{
  "granularity": {
    "normalized_value": "annual",
    "source_text": "Annual"
  }
}
```

```json
{
  "granularity": {
    "normalized_value": "monthly",
    "source_text": "Monthly"
  }
}
```

```json
{
  "granularity": {
    "normalized_value": "quarterly",
    "source_text": "Quarterly"
  }
}
```

```json
{
  "granularity": {
    "normalized_value": "daily",
    "source_text": "Daily"
  }
}
```


### Spatial context

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `geographic_coverage` | `GeographicCoverage \| null` | no | `null` |  | [https://schema.org/spatialCoverage](https://schema.org/spatialCoverage) (exact), [http://purl.org/dc/terms/spatial](http://purl.org/dc/terms/spatial) (exact) |

#### Field definitions and examples

##### `geographic_coverage`

**Definition**

Overall geographic scope, additional locations, and level.

**Examples**

```json
{
  "scope": {
    "m49_code": "001",
    "name": "Global",
    "source_text": "Global"
  }
}
```

```json
{
  "scope": {
    "iso3_code": "KEN",
    "name": "Kenya",
    "source_text": "Kenya"
  }
}
```

```json
{
  "scope": {
    "m49_code": "202",
    "name": "Sub-Saharan Africa",
    "source_text": "Sub-Saharan Africa"
  }
}
```

```json
{
  "scope": {
    "name": "Latin America",
    "source_text": "Latin America"
  }
}
```

```json
{
  "locations": [
    {
      "iso3_code": "UGA",
      "name": "Uganda"
    }
  ]
}
```

```json
{
  "locations": [
    {
      "name": "Nairobi"
    }
  ]
}
```

```json
{
  "locations": [
    {
      "m49_code": "011",
      "name": "West Africa"
    }
  ]
}
```

```json
{
  "locations": [
    {
      "iso3_code": "BFA",
      "name": "Burkina Faso"
    }
  ]
}
```

```json
{
  "level": {
    "normalized_value": "country",
    "source_text": "Country"
  }
}
```

```json
{
  "level": {
    "source_text": "Province"
  }
}
```

```json
{
  "level": {
    "source_text": "District"
  }
}
```

```json
{
  "level": {
    "normalized_value": "site",
    "source_text": "Facility"
  }
}
```


### Measurement context

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `comparisons` | `array[string] \| null` | no | `null` | minItems: 1 |  |

#### Field definitions and examples

##### `comparisons`

**Definition**

The benchmark, comparator, reference group, cohort, scenario, or entity against which the represented data are compared.

Populate only when the snapshot explicitly presents a comparative relationship. This field captures the intended comparison or benchmark represented by the snapshot, not simply the categories used to organize the data.

**Examples**

```json
[
  "Male vs Female"
]
```

```json
[
  "Rural vs Urban"
]
```

```json
[
  "Baseline vs Endline"
]
```

```json
[
  "Treatment vs Control"
]
```

```json
[
  "Before vs After"
]
```

```json
[
  "Low-income vs Middle-income vs High-income"
]
```

```json
[
  "Europe & Central Asia benchmark"
]
```

```json
[
  "Sub-Saharan Africa benchmark"
]
```


### Structural organization

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `visualization_types` | `array[VisualizationTypeTerm] \| null` | no | `null` | minItems: 1 | [http://purl.org/dc/terms/type](http://purl.org/dc/terms/type) (standard_broader), [https://schema.org/additionalType](https://schema.org/additionalType) (standard_broader) |

#### Field definitions and examples

##### `visualization_types`

**Definition**

The primary visualization used to encode the represented data.

Use `normalized_value` when the visualization type is inferred from visual form. Use `source_text` only when wording in the snapshot explicitly names the visualization form; do not manufacture source wording from the visual design. Preserve an explicitly written unfamiliar type in `source_text` without a normalized value. If neither a listed normalized type nor an explicit unfamiliar source label is supported, return `null`; do not force a match to the closest vocabulary value. For a composite or multi-panel snapshot, record the overall visualization type when no single component type adequately describes the artifact. Use `panel_titles` for explicit panel headings.

**Examples**

```json
[
  {
    "normalized_value": "bar_chart"
  }
]
```

```json
[
  {
    "normalized_value": "bar_chart",
    "source_text": "Bar Graph"
  }
]
```

```json
[
  {
    "source_text": "Waffle chart"
  }
]
```

```json
null
```

```json
[
  {
    "normalized_value": "bar_chart",
    "source_text": "Bar chart"
  }
]
```

```json
[
  {
    "normalized_value": "line_chart",
    "source_text": "Line chart"
  }
]
```

```json
[
  {
    "normalized_value": "table",
    "source_text": "Table"
  }
]
```

```json
[
  {
    "normalized_value": "map",
    "source_text": "Map"
  }
]
```

```json
[
  {
    "normalized_value": "heatmap",
    "source_text": "Heatmap"
  }
]
```

```json
[
  {
    "normalized_value": "composite_figure",
    "source_text": "Composite figure: line charts and map"
  }
]
```


### Provenance and attribution

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `provenance` | `Provenance \| null` | no | `null` |  |  |
| `languages` | `array[Language] \| null` | no | `null` | minItems: 1 | [https://schema.org/inLanguage](https://schema.org/inLanguage) (exact), [http://purl.org/dc/terms/language](http://purl.org/dc/terms/language) (exact) |
| `interpretive_notes` | `array[string] \| null` | no | `null` | minItems: 1 | [http://purl.org/dc/terms/description](http://purl.org/dc/terms/description) (standard_broader), [https://schema.org/description](https://schema.org/description) (standard_broader) |

#### Field definitions and examples

##### `provenance`

**Definition**

The named dataset, survey, publication, organization, or credited agent from which the represented data originate or which is explicitly credited with producing the snapshot artifact.

Use `sources` for represented-data derivation sources and `attributions` for credited agents; include an attribution role when it is explicit. Do not copy the parent document's authors or publisher into this field solely because they are associated with the document; the source or attribution must be explicitly relevant to the snapshot or its represented data.

**Examples**

```json
{
  "sources": [
    {
      "name": "World Development Indicators"
    }
  ]
}
```

```json
{
  "sources": [
    {
      "name": "DHS"
    }
  ]
}
```

```json
{
  "sources": [
    {
      "name": "UNHCR Registration Data"
    }
  ]
}
```

```json
{
  "sources": [
    {
      "name": "National Census"
    }
  ]
}
```

```json
{
  "attributions": [
    {
      "name": "Map Design Unit",
      "role": {
        "source_text": "Map maker"
      }
    }
  ]
}
```


##### `languages`

**Definition**

The language used within the snapshot.

**Examples**

```json
[
  {
    "source_text": "English",
    "tag": "en"
  }
]
```

```json
[
  {
    "source_text": "French",
    "tag": "fr"
  }
]
```

```json
[
  {
    "source_text": "Arabic",
    "tag": "ar"
  }
]
```


##### `interpretive_notes`

**Definition**

Explanatory, methodological, uncertainty, or provenance statements explicitly provided within the snapshot that aid interpretation or traceability.

This field may preserve complete notes containing sample-size statements, explanations of confidence intervals, standard errors or uncertainty bands, and footer statements that include an artifact date or production credit. It retains the statement as text; it does not create separate structured fields for sample size, uncertainty representation, or artifact publication date.

Populate only when such notes are explicitly present.

**Examples**

```json
[
  "Values are provisional."
]
```

```json
[
  "Estimates exclude informal employment."
]
```

```json
[
  "Data collected using 2022 census boundaries."
]
```

```json
[
  "Sample: 1,204 respondents."
]
```

```json
[
  "Shaded areas show 95% confidence intervals."
]
```

```json
[
  "Prepared by the Map Design Unit, March 2024."
]
```


### Project and operational context

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `project` | `Project \| null` | no | `null` |  | [https://schema.org/Project](https://schema.org/Project) (standard_narrower), [https://iatistandard.org/en/iati-standard/203/activity-standard/](https://iatistandard.org/en/iati-standard/203/activity-standard/) (close) |
| `intervention_types` | `array[string] \| null` | no | `null` | minItems: 1 |  |
| `financing` | `Financing \| null` | no | `null` |  |  |

#### Field definitions and examples

##### `project`

**Definition**

Associated project, program, operation, or initiative.

**Examples**

```json
{
  "name": "Niger - COVID-19 Emergency Response Project"
}
```

```json
{
  "name": "Jordan Health Sector Reform Project"
}
```

```json
{
  "name": "Lebanon - Health Resilience Project"
}
```


##### `intervention_types`

**Definition**

The intervention, service, policy, or operational activity represented.

**Examples**

```json
[
  "Cash Transfer"
]
```

```json
[
  "Vaccination"
]
```

```json
[
  "School Construction"
]
```


##### `financing`

**Definition**

Project-financing measures, funders, and instruments.

**Examples**

```json
{
  "measures": [
    "Project Cost"
  ]
}
```

```json
{
  "measures": [
    "Disbursement"
  ]
}
```

```json
{
  "measures": [
    "Financing Gap"
  ]
}
```

```json
{
  "measures": [
    "Budget Allocation"
  ]
}
```

```json
{
  "funders": [
    {
      "name": "IDA"
    }
  ]
}
```

```json
{
  "funders": [
    {
      "name": "IBRD"
    }
  ]
}
```

```json
{
  "funders": [
    {
      "name": "Government"
    }
  ]
}
```

```json
{
  "funders": [
    {
      "name": "European Union"
    }
  ]
}
```

```json
{
  "instruments": [
    {
      "source_text": "Grant"
    }
  ]
}
```

```json
{
  "instruments": [
    {
      "source_text": "Loan"
    }
  ]
}
```

```json
{
  "instruments": [
    {
      "source_text": "Credit"
    }
  ]
}
```

```json
{
  "instruments": [
    {
      "source_text": "Trust Fund"
    }
  ]
}
```


### Analytical and methodological context

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `analysis_methods` | `array[string] \| null` | no | `null` | minItems: 1 | [https://schema.org/measurementTechnique](https://schema.org/measurementTechnique) (related_structural), [http://www.w3.org/ns/prov#Activity](http://www.w3.org/ns/prov#Activity) (related_structural) |
| `data_collection_methods` | `array[CodedTerm] \| null` | no | `null` | minItems: 1 | [https://docs.ddialliance.org/DDI-Lifecycle/3.3/model/composite-types/ModeOfCollectionType/](https://docs.ddialliance.org/DDI-Lifecycle/3.3/model/composite-types/ModeOfCollectionType/) (exact), [https://schema.org/measurementMethod](https://schema.org/measurementMethod) (close) |

#### Field definitions and examples

##### `analysis_methods`

**Definition**

The analytical, statistical, or computational method used to produce the reported results.

Populate only when explicitly stated.

**Examples**

```json
[
  "Difference-in-Differences"
]
```

```json
[
  "Regression"
]
```

```json
[
  "Tobit model"
]
```

```json
[
  "Cost-Benefit Analysis"
]
```


##### `data_collection_methods`

**Definition**

The method or instrument used to collect the underlying data.

Populate only when explicitly stated.

**Examples**

```json
[
  {
    "source_text": "Household Survey"
  }
]
```

```json
[
  {
    "source_text": "Administrative Records"
  }
]
```

```json
[
  {
    "source_text": "Key Informant Interviews"
  }
]
```

```json
[
  {
    "source_text": "Census"
  }
]
```


## Referenced Types

Each block is one possible field value. Examples for different fields are independent and should not be combined into a record automatically. They illustrate the schema and do not constrain accepted values. URIs under example.org are illustrative placeholders.

### AnalyticalRole

Identify an explicitly stated analytical or axis role.

`outcome`, `predictor`, `instrumental`, `control`, `x_axis`, `y_axis`

### Attribution

Represent a named agent and its optional explicit attribution role.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `name` | `string` | yes | — | minLength: 1; pattern: \S |  |
| `identifiers` | `array[Identifier] \| null` | no | `null` | minItems: 1 |  |
| `role` | `CodedTerm \| null` | no | `null` |  |  |

#### Field definitions and examples

##### `name`

**Definition**

Source-visible entity name.

**Examples**

```json
"Map Design Unit"
```

```json
"National Statistics Office"
```


##### `identifiers`

**Definition**

Assigned entity identifiers.

**Examples**

```json
[
  {
    "scheme": "https://example.org/entities",
    "value": "ENTITY-001"
  }
]
```


##### `role`

**Definition**

Explicit source-grounded agent role.

**Examples**

```json
{
  "source_text": "Map maker"
}
```

```json
{
  "source_text": "Producer"
}
```


### AxisAssignment

Bind a variable to one distinct axis in a multi-axis graph.

- x axes use top or bottom; y axes use left or right.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `dimension` | `AxisDimension` | yes | — |  |  |
| `position` | `AxisPosition` | yes | — |  |  |
| `position_index` | `integer` | yes | — |  |  |

#### Field definitions and examples

##### `dimension`

**Definition**

Cartesian dimension of the assigned axis.

**Examples**

```json
"x"
```

```json
"y"
```


##### `position`

**Definition**

Side of the plot where the assigned axis appears.

**Examples**

```json
"top"
```

```json
"bottom"
```

```json
"left"
```

```json
"right"
```


##### `position_index`

**Definition**

One-based order from the plotting area outward among axes on the same side.

**Examples**

```json
1
```

```json
2
```


### AxisDimension

Identify a Cartesian axis dimension.

`x`, `y`

### AxisPosition

Identify the side of a plot where an axis appears.

`top`, `bottom`, `left`, `right`

### CategoryGroup

Represent one explicit nonrecursive category grouping.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `name` | `string` | yes | — | minLength: 1; pattern: \S |  |
| `categories` | `array[CodedTerm]` | yes | — | minItems: 1 |  |

#### Field definitions and examples

##### `name`

**Definition**

Explicit category-group heading.

**Examples**

```json
"Violation of the right to liberty"
```


##### `categories`

**Definition**

Categories directly contained by the group.

**Examples**

```json
[
  {
    "source_text": "Arbitrary arrests"
  },
  {
    "source_text": "Abductions"
  }
]
```


### CodedTerm

Represent source wording with optional exact vocabulary identifiers.

- At least one of source_text, code, or uri must be non-null.

- Code and scheme must be non-null together.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `code` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `scheme` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `uri` | `uri \| null` | no | `null` | minLength: 1; pattern: ^[A-Za-z][A-Za-z0-9+.-]*:(?://(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|:)*@)?(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})*\|\[[A-Za-z0-9:.!$&'()*+,;=_~-]+\])(?::[0-9]*)?(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|/(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*)?\|(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|)(?:\?(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?(?:#(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?$; format: uri |  |

#### Field definitions and examples

##### `source_text`

**Definition**

Exact text or symbol visible in the snapshot that explicitly expresses the value represented by this object. Omit it when the value is inferred from visual form, structure, or context rather than transcribed.

**Examples**

```json
"Grant"
```

```json
"District"
```


##### `code`

**Definition**

Code in the named scheme.

**Examples**

```json
"110"
```


##### `scheme`

**Definition**

Code-list or vocabulary identifier.

**Examples**

```json
"IATI Finance Type"
```


##### `uri`

**Definition**

Authoritative URI for the represented concept.

**Examples**

```json
"https://example.org/concepts/TERM-001"
```


### Currency

Represent a displayed currency and optional ISO 4217 code.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `source_text` | `string` | yes | — | minLength: 1; pattern: \S |  |
| `code` | `string \| null` | no | `null` | pattern: ^[A-Z]{3}$ | [ISO ISO 4217](https://www.iso.org/iso-4217-currency-codes.html); release: not pinned; syntax only |

#### Field definitions and examples

##### `source_text`

**Definition**

Exact text or symbol visible in the snapshot that explicitly expresses the currency.

**Examples**

```json
"USD"
```

```json
"EUR"
```

```json
"JPY"
```


##### `code`

**Definition**

Uppercase ISO 4217 alphabetic code.

**Examples**

```json
"USD"
```

```json
"EUR"
```

```json
"JPY"
```


### Dimension

Represent a classificatory dimension and its visible organization.

- At least one non-null value is required: name, categories, category_groups.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `name` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `categories` | `array[CodedTerm] \| null` | no | `null` | minItems: 1 | [http://www.w3.org/2004/02/skos/core#Concept](http://www.w3.org/2004/02/skos/core#Concept) (related_structural) |
| `category_groups` | `array[CategoryGroup] \| null` | no | `null` | minItems: 1 | [http://www.w3.org/2004/02/skos/core#broader](http://www.w3.org/2004/02/skos/core#broader) (related_structural) |
| `presentation_roles` | `array[PresentationRole] \| null` | no | `null` | minItems: 1 |  |

#### Field definitions and examples

##### `name`

**Definition**

The conceptual variable or dimension used to organize, group, classify, or compare the represented values.

**Examples**

```json
"Country"
```

```json
"Year"
```

```json
"Education Level"
```

```json
"Industry Sector"
```

```json
"Scenario"
```


##### `categories`

**Definition**

The explicit category names or labels associated with a category dimension.

**Examples**

```json
[
  {
    "source_text": "Male"
  },
  {
    "source_text": "Female"
  }
]
```

```json
[
  {
    "source_text": "Agriculture"
  },
  {
    "source_text": "Manufacturing"
  },
  {
    "source_text": "Services"
  }
]
```

```json
[
  {
    "source_text": "Kenya"
  },
  {
    "source_text": "Uganda"
  },
  {
    "source_text": "Tanzania"
  }
]
```

```json
[
  {
    "source_text": "Low"
  },
  {
    "source_text": "Medium"
  },
  {
    "source_text": "High"
  }
]
```


##### `category_groups`

**Definition**

One level of explicit category groups.

**Examples**

```json
[
  {
    "categories": [
      {
        "source_text": "Arbitrary arrests"
      },
      {
        "source_text": "Abductions"
      }
    ],
    "name": "Violation of the right to liberty"
  }
]
```


##### `presentation_roles`

**Definition**

Explicit table-presentation roles.

`row`: The conceptual variable represented by table rows.

`column`: The conceptual variable represented by table columns.

**Examples**

```json
[
  "row"
]
```

```json
[
  "column"
]
```


### EntityReference

Represent a named project, organization, source, or component.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `name` | `string` | yes | — | minLength: 1; pattern: \S |  |
| `identifiers` | `array[Identifier] \| null` | no | `null` | minItems: 1 |  |

#### Field definitions and examples

##### `name`

**Definition**

Source-visible entity name.

**Examples**

```json
"World Development Indicators"
```

```json
"DHS"
```

```json
"UNHCR Registration Data"
```

```json
"National Census"
```

```json
"Map Design Unit"
```


##### `identifiers`

**Definition**

Assigned entity identifiers.

**Examples**

```json
[
  {
    "scheme": "https://example.org/entities",
    "value": "ENTITY-001"
  }
]
```


### Financing

Group project-financing measures, funders, and instruments.

- At least one non-null value is required: measures, funders, instruments.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `measures` | `array[string] \| null` | no | `null` | minItems: 1 |  |
| `funders` | `array[EntityReference] \| null` | no | `null` | minItems: 1 | [https://schema.org/funder](https://schema.org/funder) (exact) |
| `instruments` | `array[CodedTerm] \| null` | no | `null` | minItems: 1 | [https://reference.iatistandard.org/en/iati-standard/203/codelists/financetype/](https://reference.iatistandard.org/en/iati-standard/203/codelists/financetype/) (close) |

#### Field definitions and examples

##### `measures`

**Definition**

The financial quantity or funding-related measure represented by the snapshot.

**Examples**

```json
[
  "Project Cost"
]
```

```json
[
  "Disbursement"
]
```

```json
[
  "Financing Gap"
]
```

```json
[
  "Budget Allocation"
]
```


##### `funders`

**Definition**

The organization or funding source providing financial support.

**Examples**

```json
[
  {
    "name": "IDA"
  }
]
```

```json
[
  {
    "name": "IBRD"
  }
]
```

```json
[
  {
    "name": "Government"
  }
]
```

```json
[
  {
    "name": "European Union"
  }
]
```


##### `instruments`

**Definition**

The financing mechanism associated with the represented activity.

**Examples**

```json
[
  {
    "source_text": "Grant"
  }
]
```

```json
[
  {
    "source_text": "Loan"
  }
]
```

```json
[
  {
    "source_text": "Credit"
  }
]
```

```json
[
  {
    "source_text": "Trust Fund"
  }
]
```


### GeographicCoverage

Group overall geographic scope, locations, and reporting level.

- At least one non-null value is required: scope, locations, level.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `scope` | `Place \| null` | no | `null` |  | [https://schema.org/spatialCoverage](https://schema.org/spatialCoverage) (exact) |
| `locations` | `array[GeographicLocation] \| null` | no | `null` | minItems: 1 | [https://schema.org/spatialCoverage](https://schema.org/spatialCoverage) (related_structural) |
| `level` | `GeographicLevelTerm \| null` | no | `null` |  |  |

#### Field definitions and examples

##### `scope`

**Definition**

The primary geographic area represented by the snapshot.

**Examples**

```json
{
  "m49_code": "001",
  "name": "Global",
  "source_text": "Global"
}
```

```json
{
  "iso3_code": "KEN",
  "name": "Kenya",
  "source_text": "Kenya"
}
```

```json
{
  "m49_code": "202",
  "name": "Sub-Saharan Africa",
  "source_text": "Sub-Saharan Africa"
}
```

```json
{
  "name": "Latin America",
  "source_text": "Latin America"
}
```


##### `locations`

**Definition**

Named geographic entities explicitly represented within the snapshot.

Use this collection for additional named locations; record the overall coverage in `geographic_coverage.scope`.

**Examples**

```json
[
  {
    "iso3_code": "UGA",
    "name": "Uganda"
  }
]
```

```json
[
  {
    "name": "Nairobi"
  }
]
```

```json
[
  {
    "m49_code": "011",
    "name": "West Africa"
  }
]
```

```json
[
  {
    "iso3_code": "BFA",
    "name": "Burkina Faso"
  }
]
```


##### `level`

**Definition**

The administrative or spatial level at which data are reported.

**Examples**

```json
{
  "normalized_value": "country",
  "source_text": "Country"
}
```

```json
{
  "source_text": "Province"
}
```

```json
{
  "source_text": "District"
}
```

```json
{
  "normalized_value": "site",
  "source_text": "Facility"
}
```


### GeographicLevelTerm

Represent a known or source-only geographic reporting level.

- At least one non-null value is required: source_text, normalized_value.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `normalized_value` | `GeographicLevelValue \| null` | no | `null` |  |  |

#### Field definitions and examples

##### `source_text`

**Definition**

Exact text visible in the snapshot that explicitly states the geographic level.

**Examples**

```json
"Country"
```

```json
"Province"
```

```json
"District"
```

```json
"Facility"
```


##### `normalized_value`

**Definition**

Approved normalized geographic level.

**Examples**

```json
"country"
```

```json
"administrative_area_1"
```

```json
"site"
```


### GeographicLevelValue

Enumerate approved normalized geographic levels.

`global`, `world_region`, `country`, `administrative_area_1`, `administrative_area_2`, `administrative_area_3`, `locality`, `site`

### GeographicLocation

Represent an additional named location and its optional role and type.

- At least one non-null value is required: source_text, name, iso3_code, subdivision_code, m49_code, identifiers.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `name` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `iso3_code` | `string \| null` | no | `null` | pattern: ^[A-Z]{3}$ | [ISO ISO 3166-1](https://www.iso.org/iso-3166-country-codes.html); release: not pinned; syntax only |
| `subdivision_code` | `string \| null` | no | `null` | pattern: ^[A-Z]{2}-[A-Z0-9]{1,3}$ | [ISO ISO 3166-2](https://www.iso.org/iso-3166-country-codes.html); release: not pinned; syntax only |
| `m49_code` | `string \| null` | no | `null` | pattern: ^[0-9]{3}$ | [United Nations M49](https://unstats.un.org/unsd/methodology/m49/); release: not pinned; syntax only |
| `identifiers` | `array[Identifier] \| null` | no | `null` | minItems: 1 |  |
| `role` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `type` | `CodedTerm \| null` | no | `null` |  |  |

#### Field definitions and examples

##### `source_text`

**Definition**

Exact text visible in the snapshot that explicitly expresses the place. Omit it when the normalized place is inferred from structure or context.

**Examples**

```json
"Global"
```

```json
"Kenya"
```

```json
"Sub-Saharan Africa"
```

```json
"Latin America"
```


##### `name`

**Definition**

Preferred place name.

**Examples**

```json
"Kenya"
```

```json
"Sub-Saharan Africa"
```

```json
"Philippines"
```


##### `iso3_code`

**Definition**

ISO 3166-1 alpha-3 code for a country or area. Do not use World Bank aggregate or region codes.

**Examples**

```json
"KEN"
```

```json
"PHL"
```


##### `subdivision_code`

**Definition**

ISO 3166-2 subdivision code.

**Examples**

```json
"US-CA"
```


##### `m49_code`

**Definition**

UN M49 statistical-area code.

**Examples**

```json
"002"
```

```json
"202"
```


##### `identifiers`

**Definition**

Other authoritative identifiers.

**Examples**

```json
[
  {
    "scheme": "ISO 3166-1 alpha-3",
    "value": "KEN"
  }
]
```


##### `role`

**Definition**

The semantic role played by geographic entities within the represented data.

**Examples**

```json
"Country of origin"
```

```json
"Host country"
```

```json
"Destination"
```

```json
"Reporting location"
```


##### `type`

**Definition**

The physical or administrative type of a named geographic location represented in the snapshot. This field describes what the location is; use `geographic_coverage.level` for the administrative or spatial level at which the snapshot's data are reported.

**Examples**

```json
{
  "source_text": "Refugee camp"
}
```

```json
{
  "source_text": "Hospital"
}
```

```json
{
  "source_text": "School"
}
```

```json
{
  "source_text": "District"
}
```


### Identifier

Represent a verified identifier and its optional authority context.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `value` | `string` | yes | — | minLength: 1; pattern: \S |  |
| `scheme` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `issuer` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `uri` | `uri \| null` | no | `null` | minLength: 1; pattern: ^[A-Za-z][A-Za-z0-9+.-]*:(?://(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|:)*@)?(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})*\|\[[A-Za-z0-9:.!$&'()*+,;=_~-]+\])(?::[0-9]*)?(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|/(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*)?\|(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])+(?:/(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])*)*\|)(?:\?(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?(?:#(?:(?:(?:[A-Za-z0-9._~!$&'()*+,;=-]\|%[0-9A-Fa-f]{2})\|[:@])\|[/?])*)?$; format: uri |  |

#### Field definitions and examples

##### `value`

**Definition**

Identifier exactly as assigned in the snapshot or trusted metadata. Do not infer or manufacture it from its apparent pattern or from model knowledge.

**Examples**

```json
"P171254"
```

```json
"P178944"
```


##### `scheme`

**Definition**

Identifier scheme explicitly supplied by the snapshot, trusted metadata, or configured and verified enrichment. Do not infer it from the identifier's apparent pattern or from model knowledge.

**Examples**

```json
"World Bank project ID"
```


##### `issuer`

**Definition**

Issuing agent explicitly supplied by the snapshot, trusted metadata, or configured and verified enrichment. Do not infer it from model knowledge.

**Examples**

```json
"World Bank"
```


##### `uri`

**Definition**

Authoritative absolute URI supplied by the snapshot, trusted metadata, or configured and verified enrichment. Do not construct or infer it from model knowledge.

**Examples**

```json
"https://example.org/projects/P171254"
```


### Language

Represent a snapshot language using source text and/or BCP 47.

- At least one non-null value is required: source_text, tag.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `tag` | `string \| null` | no | `null` | minLength: 1; pattern: ^(?:(?:[A-Za-z]{2,3}(?:-[A-Za-z]{3}){0,3}\|[A-Za-z]{4}\|[A-Za-z]{5,8})(?:-[A-Za-z]{4})?(?:-(?:[A-Za-z]{2}\|[0-9]{3}))?(?:-(?:[A-Za-z0-9]{5,8}\|[0-9][A-Za-z0-9]{3}))*(?:-[0-9A-WY-Za-wy-z](?:-[A-Za-z0-9]{2,8})+)*(?:-[xX](?:-[A-Za-z0-9]{1,8})+)?\|[xX](?:-[A-Za-z0-9]{1,8})+\|en-GB-oed\|i-ami\|i-bnn\|i-default\|i-enochian\|i-hak\|i-klingon\|i-lux\|i-mingo\|i-navajo\|i-pwn\|i-tao\|i-tay\|i-tsu\|sgn-BE-FR\|sgn-BE-NL\|sgn-CH-DE\|art-lojban\|cel-gaulish\|no-bok\|no-nyn\|zh-guoyu\|zh-hakka\|zh-min\|zh-min-nan\|zh-xiang)$ | [IETF/IANA BCP 47](https://www.iana.org/assignments/language-subtag-registry/); release: not pinned; syntax only |

#### Field definitions and examples

##### `source_text`

**Definition**

Exact text visible in the snapshot that explicitly names the language. Omit it when the language is inferred from the snapshot content.

**Examples**

```json
"English"
```

```json
"French"
```

```json
"Arabic"
```


##### `tag`

**Definition**

Canonical BCP 47 language tag.

**Examples**

```json
"en"
```

```json
"fr"
```

```json
"ar"
```


### Place

Represent a source-grounded place with optional standard identifiers.

- At least one non-null value is required: source_text, name, iso3_code, subdivision_code, m49_code, identifiers.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `name` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `iso3_code` | `string \| null` | no | `null` | pattern: ^[A-Z]{3}$ | [ISO ISO 3166-1](https://www.iso.org/iso-3166-country-codes.html); release: not pinned; syntax only |
| `subdivision_code` | `string \| null` | no | `null` | pattern: ^[A-Z]{2}-[A-Z0-9]{1,3}$ | [ISO ISO 3166-2](https://www.iso.org/iso-3166-country-codes.html); release: not pinned; syntax only |
| `m49_code` | `string \| null` | no | `null` | pattern: ^[0-9]{3}$ | [United Nations M49](https://unstats.un.org/unsd/methodology/m49/); release: not pinned; syntax only |
| `identifiers` | `array[Identifier] \| null` | no | `null` | minItems: 1 |  |

#### Field definitions and examples

##### `source_text`

**Definition**

Exact text visible in the snapshot that explicitly expresses the place. Omit it when the normalized place is inferred from structure or context.

**Examples**

```json
"Global"
```

```json
"Kenya"
```

```json
"Sub-Saharan Africa"
```

```json
"Latin America"
```


##### `name`

**Definition**

Preferred place name.

**Examples**

```json
"Kenya"
```

```json
"Sub-Saharan Africa"
```

```json
"Philippines"
```


##### `iso3_code`

**Definition**

ISO 3166-1 alpha-3 code for a country or area. Do not use World Bank aggregate or region codes.

**Examples**

```json
"KEN"
```

```json
"PHL"
```


##### `subdivision_code`

**Definition**

ISO 3166-2 subdivision code.

**Examples**

```json
"US-CA"
```


##### `m49_code`

**Definition**

UN M49 statistical-area code.

**Examples**

```json
"002"
```

```json
"202"
```


##### `identifiers`

**Definition**

Other authoritative identifiers.

**Examples**

```json
[
  {
    "scheme": "ISO 3166-1 alpha-3",
    "value": "KEN"
  }
]
```


### PresentationRole

Identify a dimension's explicit table-presentation role.

`row`, `column`

### Project

Represent project, program, operation, or initiative context.

- At least one non-null value is required: name, identifiers, components.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `name` | `string \| null` | no | `null` | minLength: 1; pattern: \S | [https://schema.org/name](https://schema.org/name) (exact) |
| `identifiers` | `array[Identifier] \| null` | no | `null` | minItems: 1 | [https://schema.org/identifier](https://schema.org/identifier) (standard_broader) |
| `components` | `array[EntityReference] \| null` | no | `null` | minItems: 1 | [https://schema.org/hasPart](https://schema.org/hasPart) (related_structural) |

#### Field definitions and examples

##### `name`

**Definition**

The project, program, operation, or initiative associated with the snapshot.

**Examples**

```json
"Niger - COVID-19 Emergency Response Project"
```

```json
"Jordan Health Sector Reform Project"
```

```json
"Lebanon - Health Resilience Project"
```


##### `identifiers`

**Definition**

The formal identifier assigned to the associated project or operation.

**Examples**

```json
[
  {
    "value": "P171254"
  }
]
```

```json
[
  {
    "value": "P178944"
  }
]
```


##### `components`

**Definition**

The project component, workstream, or results area represented by the snapshot.

**Examples**

```json
[
  {
    "name": "Component 3: Project management"
  }
]
```

```json
[
  {
    "name": "Results Area 1"
  }
]
```


### Provenance

Separate derivation sources from credited agents.

- At least one non-null value is required: sources, attributions.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `sources` | `array[EntityReference] \| null` | no | `null` | minItems: 1 | [http://www.w3.org/ns/prov#wasDerivedFrom](http://www.w3.org/ns/prov#wasDerivedFrom) (related_structural), [http://purl.org/dc/terms/source](http://purl.org/dc/terms/source) (close) |
| `attributions` | `array[Attribution] \| null` | no | `null` | minItems: 1 | [http://www.w3.org/ns/prov#wasAttributedTo](http://www.w3.org/ns/prov#wasAttributedTo) (related_structural) |

#### Field definitions and examples

##### `sources`

**Definition**

Represented-data derivation sources.

**Examples**

```json
[
  {
    "name": "World Development Indicators"
  }
]
```

```json
[
  {
    "name": "DHS"
  }
]
```

```json
[
  {
    "name": "UNHCR Registration Data"
  }
]
```

```json
[
  {
    "name": "National Census"
  }
]
```


##### `attributions`

**Definition**

Agents explicitly credited for the snapshot artifact; include a role when it is explicit.

**Examples**

```json
[
  {
    "name": "Map Design Unit",
    "role": {
      "source_text": "Map maker"
    }
  }
]
```


### StatisticalFormTerm

Represent a known or source-only statistical form.

- At least one non-null value is required: source_text, normalized_value.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `normalized_value` | `StatisticalFormValue \| null` | no | `null` |  |  |

#### Field definitions and examples

##### `source_text`

**Definition**

Exact text or symbol visible in the snapshot that explicitly expresses the statistical form.

**Examples**

```json
"Count"
```

```json
"Percentage"
```

```json
"Rate"
```

```json
"Index"
```

```json
"Average"
```


##### `normalized_value`

**Definition**

Approved normalized statistical form.

**Examples**

```json
"count"
```

```json
"percentage"
```

```json
"arithmetic_mean"
```


### StatisticalFormValue

Enumerate approved normalized statistical forms.

`observed_value`, `count`, `arithmetic_mean`, `geometric_mean`, `weighted_mean`, `weighted_value`, `median`, `sum`, `weighted_sum`, `minimum`, `maximum`, `range`, `interquartile_range`, `variance`, `standard_deviation`, `standard_error`, `mean_absolute_deviation`, `median_absolute_deviation`, `skewness`, `kurtosis`, `lower_bound`, `upper_bound`, `score`, `rank`, `index`, `rate`, `harmonic_mean`, `trimmed_mean`, `mode`, `coefficient_of_variation`, `valid_cases`, `invalid_cases`, `percentage_of_valid_cases`, `percentage_of_invalid_cases`, `quartile`, `quintile`, `decile`, `percentile`, `ratio`, `proportion`, `percentage`, `confidence_interval`, `coefficient`, `p_value`, `change`

### TemporalCoverage

Group represented-data time and granularity.

- At least one non-null value is required: period, granularity.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `period` | `TemporalExpression \| null` | no | `null` |  | [https://schema.org/temporalCoverage](https://schema.org/temporalCoverage) (exact), [http://purl.org/dc/terms/temporal](http://purl.org/dc/terms/temporal) (close) |
| `granularity` | `TemporalGranularityTerm \| null` | no | `null` |  |  |

#### Field definitions and examples

##### `period`

**Definition**

The period or date range represented by the data.

This field describes **when the represented data apply**. It does not describe when the snapshot artifact or parent document was created, prepared, issued, published, revised, or retrieved. When an explicit artifact date appears only as part of a footer or provenance statement, preserve the complete statement in `interpretive_notes` rather than treating the date as `temporal_coverage.period`.

**Examples**

```json
{
  "end": "2020",
  "precision": "year",
  "relation": "interval",
  "source_text": "2015–2020",
  "start": "2015"
}
```

```json
{
  "source_text": "FY2023"
}
```

```json
{
  "precision": "month",
  "relation": "point",
  "source_text": "January 2024",
  "start": "2024-01"
}
```


##### `granularity`

**Definition**

The temporal resolution at which the represented data are reported.

**Examples**

```json
{
  "normalized_value": "annual",
  "source_text": "Annual"
}
```

```json
{
  "normalized_value": "monthly",
  "source_text": "Monthly"
}
```

```json
{
  "normalized_value": "quarterly",
  "source_text": "Quarterly"
}
```

```json
{
  "normalized_value": "daily",
  "source_text": "Daily"
}
```


### TemporalExpression

Represent source-visible time with optional normalized bounds.

- At least one of source_text, start, or end must be non-null.

- Normalized bounds require relation and precision; source-only expressions omit both.

- point and as_of require start only; interval requires both bounds; open_interval requires exactly one bound.

- Bounds must match the declared precision. Python additionally validates calendar dates and chronological ordering.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `start` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `end` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `relation` | `TemporalRelation \| null` | no | `null` |  |  |
| `precision` | `TemporalPrecision \| null` | no | `null` |  |  |

#### Field definitions and examples

##### `source_text`

**Definition**

Exact complete time expression visible in the snapshot. Omit it when normalized bounds are inferred from separate labels or structure rather than transcribed as one expression.

**Examples**

```json
"2015–2020"
```

```json
"FY2023"
```

```json
"January 2024"
```


##### `start`

**Definition**

Normalized start.

**Examples**

```json
"2015"
```

```json
"2024-01"
```

```json
"2024-01-01T12:00:00.1Z"
```


##### `end`

**Definition**

Normalized end.

**Examples**

```json
"2020"
```

```json
"2024-03"
```


##### `relation`

**Definition**

Relationship between normalized bounds.

**Examples**

```json
"interval"
```

```json
"point"
```

```json
"as_of"
```

```json
"open_interval"
```


##### `precision`

**Definition**

Precision of normalized bounds.

**Examples**

```json
"year"
```

```json
"month"
```

```json
"day"
```

```json
"datetime"
```


### TemporalGranularityTerm

Represent a known or source-only temporal granularity.

- At least one non-null value is required: source_text, normalized_value.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `normalized_value` | `TemporalGranularityValue \| null` | no | `null` |  |  |

#### Field definitions and examples

##### `source_text`

**Definition**

Exact text visible in the snapshot that explicitly states the temporal granularity.

**Examples**

```json
"Annual"
```

```json
"Monthly"
```

```json
"Quarterly"
```

```json
"Daily"
```


##### `normalized_value`

**Definition**

Approved normalized temporal granularity.

**Examples**

```json
"annual"
```

```json
"monthly"
```

```json
"quarterly"
```


### TemporalGranularityValue

Enumerate approved normalized temporal granularities.

`hourly`, `daily`, `weekly`, `monthly`, `quarterly`, `semiannual`, `annual`, `instantaneous`, `event_based`, `multi_year`, `irregular`

### TemporalPrecision

Describe the precision of normalized temporal bounds.

`year`, `month`, `day`, `datetime`

### TemporalRelation

Describe how normalized temporal bounds form an expression.

`point`, `interval`, `open_interval`, `as_of`

### Unit

Represent a displayed unit and its optional normalized qualifiers.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `source_text` | `string` | yes | — | minLength: 1; pattern: \S |  |
| `code` | `string \| null` | no | `null` | pattern: ^[A-Z0-9]{1,3}$ | [UNECE Recommendation 20](https://unece.org/trade/uncefact/cl-recommendations); release: not pinned; syntax only |
| `multiplier_exponent` | `integer \| null` | no | `null` |  | [SDMX CL_UNIT_MULT](https://registry.sdmx.org/items/codelist.html); release: 1.1 |

#### Field definitions and examples

##### `source_text`

**Definition**

Exact text or symbol visible in the snapshot that explicitly expresses the unit.

**Examples**

```json
"Percent"
```

```json
"USD"
```

```json
"People"
```

```json
"Kilometers"
```


##### `code`

**Definition**

Exact UN/CEFACT Recommendation 20 common code.

**Examples**

```json
"P1"
```

```json
"KMT"
```


##### `multiplier_exponent`

**Definition**

Base-10 SDMX unit-multiplier exponent.

**Examples**

```json
3
```

```json
6
```

```json
9
```


### Variable

Represent a measured variable and its applicable qualifiers.

- At least one non-null value is required: name, unit, currency, statistical_forms.

- Analytical roles and axis assignments require a non-null variable name.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `name` | `string \| null` | no | `null` | minLength: 1; pattern: \S | [https://schema.org/variableMeasured](https://schema.org/variableMeasured) (close) |
| `unit` | `Unit \| null` | no | `null` |  | [https://schema.org/unitCode](https://schema.org/unitCode) (related_structural) |
| `currency` | `Currency \| null` | no | `null` |  | [https://schema.org/currency](https://schema.org/currency) (close) |
| `analytical_roles` | `array[AnalyticalRole] \| null` | no | `null` | minItems: 1 |  |
| `axis_assignments` | `array[AxisAssignment] \| null` | no | `null` | minItems: 1 |  |
| `statistical_forms` | `array[StatisticalFormTerm] \| null` | no | `null` | minItems: 1 | [https://schema.org/statType](https://schema.org/statType) (close) |

#### Field definitions and examples

##### `name`

**Definition**

The primary variable, indicator, metric, or measured concept represented by the snapshot.

This field records the variable's name or measured concept, not a normalized analytical role. Use `dimensions[].name`, `dimensions[].categories`, and `dimensions[].presentation_roles` where those structural roles apply. Use `variables[].analytical_roles` for analytical roles and `variables[].axis_assignments` for distinct axes in a multi-axis graph.

**Examples**

```json
"GDP Growth"
```

```json
"Inflation"
```

```json
"Literacy Rate"
```

```json
"Refugee Population"
```


##### `unit`

**Definition**

The unit used to interpret reported quantitative values.

**Examples**

```json
{
  "code": "P1",
  "source_text": "Percent"
}
```

```json
{
  "source_text": "USD"
}
```

```json
{
  "source_text": "People"
}
```

```json
{
  "code": "KMT",
  "source_text": "Kilometers"
}
```


##### `currency`

**Definition**

The currency denomination used for monetary values.

**Examples**

```json
{
  "code": "USD",
  "source_text": "USD"
}
```

```json
{
  "code": "EUR",
  "source_text": "EUR"
}
```

```json
{
  "code": "JPY",
  "source_text": "JPY"
}
```


##### `analytical_roles`

**Definition**

Explicit analytical or axis roles.

**Examples**

```json
[
  "outcome"
]
```

```json
[
  "predictor"
]
```

```json
[
  "x_axis"
]
```


##### `axis_assignments`

**Definition**

Explicit assignments to distinct Cartesian axes in a multi-axis graph.

Use `analytical_roles` for a single or shared x- or y-axis. Use this field when variables are assigned to different axes of the same dimension. `position_index` is 1 for the axis nearest the plotting area on a given side and increases outward.

**Examples**

```json
[
  {
    "dimension": "y",
    "position": "left",
    "position_index": 1
  }
]
```

```json
[
  {
    "dimension": "y",
    "position": "right",
    "position_index": 1
  }
]
```


##### `statistical_forms`

**Definition**

The statistical form in which values are expressed.

**Examples**

```json
[
  {
    "normalized_value": "count",
    "source_text": "Count"
  }
]
```

```json
[
  {
    "normalized_value": "percentage",
    "source_text": "Percentage"
  }
]
```

```json
[
  {
    "normalized_value": "rate",
    "source_text": "Rate"
  }
]
```

```json
[
  {
    "normalized_value": "index",
    "source_text": "Index"
  }
]
```

```json
[
  {
    "source_text": "Average"
  }
]
```


### VisualizationTypeTerm

Represent a known or source-only visualization type.

- At least one non-null value is required: source_text, normalized_value.

| Field | Type | Required | Default | Constraints | Standards / code list |
|---|---|---:|---|---|---|
| `source_text` | `string \| null` | no | `null` | minLength: 1; pattern: \S |  |
| `normalized_value` | `VisualizationTypeValue \| null` | no | `null` |  |  |

#### Field definitions and examples

##### `source_text`

**Definition**

Exact text visible in the snapshot that explicitly names the visualization type.

**Examples**

```json
"Bar chart"
```

```json
"Line chart"
```

```json
"Table"
```

```json
"Map"
```

```json
"Heatmap"
```

```json
"Composite figure: line charts and map"
```


##### `normalized_value`

**Definition**

Approved normalized visualization type.

**Examples**

```json
"bar_chart"
```

```json
"table"
```

```json
"composite_figure"
```


### VisualizationTypeValue

Enumerate approved normalized visualization types.

`table`, `bar_chart`, `line_chart`, `area_chart`, `pie_chart`, `donut_chart`, `scatter_plot`, `bubble_chart`, `dot_plot`, `histogram`, `density_plot`, `heatmap`, `box_plot`, `violin_plot`, `error_bar`, `error_band`, `radar_chart`, `treemap`, `map`, `choropleth_map`, `symbol_map`, `network_diagram`, `flow_diagram`, `timeline`, `diagram`, `infographic`, `dashboard`, `composite_figure`
