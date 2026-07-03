# Canonical Metadata Schema Reference v1.1

## title

Definition:
The primary title, caption, or heading that identifies the data snapshot.

Examples:
- Inflation Rate by Country
- Annual Government Expenditure
- Monthly labor income in Afghanistan and remittances from abroad
- Table 6: Determinants of illegal land reallocation at village level

---

## internal_identifier

Definition:
A document-assigned identifier used to reference the snapshot within the source document.

Examples:
- Figure 3
- Table 4.2
- Annex B
- Exhibit 7

---

## subject_domain

Definition:
The broad thematic, policy, or sectoral domain represented by the snapshot.

Examples:
- Education
- Health
- Macroeconomics
- Agriculture
- Forced Displacement

---

## subject_summary

Definition:
A concise summary describing the primary analytical subject or purpose of the snapshot.

Examples:
- Trends in primary school enrollment
- Distribution of humanitarian funding
- Comparison of poverty rates across regions

---

## panel_title

Definition:
The title or heading of an individual panel within a multi-panel snapshot.

Populate only when panel titles are explicitly present.

Examples:
- (A) Poverty Rate
- (B) Literacy Rate
- Monthly Returns

---

## variable_name

Definition:
The primary variable, indicator, metric, or measured concept represented by the snapshot.

Examples:
- GDP Growth
- Inflation
- Literacy Rate
- Refugee Population

---

## category_dimension

Definition:
The conceptual variable or dimension used to organize, group, classify, or compare the represented values.

Examples:
- Country
- Year
- Education Level
- Industry Sector
- Scenario

---

## category_labels

Definition:
The explicit category names or labels associated with a category dimension.

Examples:
- Male, Female
- Agriculture, Manufacturing, Services
- Kenya, Uganda, Tanzania
- Low, Medium, High

---

## population_group

Definition:
The human population, beneficiary group, or demographic group that is the primary subject of the represented data. This field describes who the data are about, not how they are categorized or disaggregated.

Examples:
- Refugees
- Children under five
- Female respondents
- Host communities
- Technical education graduates

---

## time_period

Definition:
The period or date range represented by the data.

Examples:
- 2015–2020
- FY2023
- January 2024

---

## temporal_granularity

Definition:
The temporal resolution at which the represented data are reported.

Examples:
- Annual
- Monthly
- Quarterly
- Daily

---

## geographic_scope

Definition:
The primary geographic area represented by the snapshot.

Examples:
- Global
- Kenya
- Sub-Saharan Africa
- Latin America

---

## geographic_entities

Definition:
Named geographic entities explicitly represented within the snapshot.

Examples:
- Uganda
- Nairobi
- West Africa
- Burkina Faso

---

## geographic_granularity

Definition:
The administrative or spatial level at which data are reported.

Examples:
- Country
- Province
- District
- Facility

---

## geographic_role

Definition:
The semantic role played by geographic entities within the represented data.

Examples:
- Country of origin
- Host country
- Destination
- Reporting location

---

## location_type

Definition:
The type of physical location represented.

Examples:
- Refugee camp
- Hospital
- School
- District

---

## unit_of_measure

Definition:
The unit used to interpret reported quantitative values.

Examples:
- Percent
- USD
- People
- Kilometers

---

## currency

Definition:
The currency denomination used for monetary values.

Examples:
- USD
- EUR
- JPY

---

## measure_type

Definition:
The statistical form in which values are expressed.

Examples:
- Count
- Percentage
- Rate
- Index
- Average

---

## comparison_group

Definition:
The benchmark, comparator, reference group, cohort, scenario, or entity against which the represented data are compared.

Populate only when the snapshot explicitly presents a comparative relationship. This field captures the intended comparison or benchmark represented by the snapshot, not simply the categories used to organize the data.

Examples:
- Male vs Female
- Rural vs Urban
- Baseline vs Endline
- Treatment vs Control
- Before vs After
- Low-income vs Middle-income vs High-income
- Europe & Central Asia benchmark
- Sub-Saharan Africa benchmark

---

## row_dimension

Definition:
The conceptual variable represented by table rows.

Examples:
- Country
- Indicator
- Sector

---

## column_dimension

Definition:
The conceptual variable represented by table columns.

Examples:
- Year
- Region
- Funding Source

---

## visualization_type

Definition:
The primary visualization used to encode the represented data.

Examples:
- Bar chart
- Line chart
- Table
- Map
- Heatmap

---

## data_source

Definition:
The dataset, survey, publication, or other cited source from which the represented data originate.

Examples:
- World Development Indicators
- DHS
- UNHCR Registration Data
- National Census

---

## source_document_title

Definition:
The title of the parent document containing the snapshot.

Examples:
- World Development Report 2024
- Global Trends Report

---

## language

Definition:
The language used within the snapshot.

Examples:
- English
- French
- Arabic

---

## interpretive_note

Definition:
Explanatory notes, caveats, assumptions, footnotes, or methodological remarks explicitly provided within the snapshot to aid interpretation.

Populate only when such notes are explicitly present.

Examples:
- Values are provisional.
- Estimates exclude informal employment.
- Data collected using 2022 census boundaries.

---

## project_name

Definition:
The project, program, operation, or initiative associated with the snapshot.

Examples:
- Niger - COVID-19 Emergency Response Project
- Jordan Health Sector Reform Project
- Lebanon - Health Resilience Project

---

## project_identifier

Definition:
The formal identifier assigned to the associated project or operation.

Examples:
- P171254
- P178944

---

## project_component

Definition:
The project component, workstream, or results area represented by the snapshot.

Examples:
- Component 3: Project management
- Results Area 1

---

## intervention_type

Definition:
The intervention, service, policy, or operational activity represented.

Examples:
- Cash Transfer
- Vaccination
- School Construction

---

## financial_measure

Definition:
The financial quantity or funding-related measure represented by the snapshot.

Examples:
- Project Cost
- Disbursement
- Financing Gap
- Budget Allocation

---

## financing_source

Definition:
The organization or funding source providing financial support.

Examples:
- IDA
- IBRD
- Government
- European Union

---

## financing_instrument

Definition:
The financing mechanism associated with the represented activity.

Examples:
- Grant
- Loan
- Credit
- Trust Fund

---

## analysis_method

Definition:
The analytical, statistical, or computational method used to produce the reported results.

Populate only when explicitly stated.

Examples:
- Difference-in-Differences
- Regression
- Tobit model
- Cost-Benefit Analysis

---

## data_collection_method

Definition:
The method or instrument used to collect the underlying data.

Populate only when explicitly stated.

Examples:
- Household Survey
- Administrative Records
- Key Informant Interviews
- Census