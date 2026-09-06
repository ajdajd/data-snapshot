"""Define the canonical Data Snapshot Metadata Schema v1.2 models."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any

from pydantic import (
    AnyUrl,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    WithJsonSchema,
    field_validator,
    model_validator,
)


def _normalize_text(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value).strip()
    return value


NonEmptyText = Annotated[
    str,
    StringConstraints(strict=True, min_length=1, pattern=r"\S"),
    BeforeValidator(_normalize_text),
]

# RFC 5646 section 2.1; registry membership remains a separate concern.
_GRANDFATHERED_TAGS = (
    "en-GB-oed",
    "i-ami",
    "i-bnn",
    "i-default",
    "i-enochian",
    "i-hak",
    "i-klingon",
    "i-lux",
    "i-mingo",
    "i-navajo",
    "i-pwn",
    "i-tao",
    "i-tay",
    "i-tsu",
    "sgn-BE-FR",
    "sgn-BE-NL",
    "sgn-CH-DE",
    "art-lojban",
    "cel-gaulish",
    "no-bok",
    "no-nyn",
    "zh-guoyu",
    "zh-hakka",
    "zh-min",
    "zh-min-nan",
    "zh-xiang",
)
_BCP47_PATTERN = re.compile(
    r"^(?:(?:[A-Za-z]{2,3}(?:-[A-Za-z]{3}){0,3}|[A-Za-z]{4}|[A-Za-z]{5,8})"
    r"(?:-[A-Za-z]{4})?(?:-(?:[A-Za-z]{2}|[0-9]{3}))?"
    r"(?:-(?:[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}))*"
    r"(?:-[0-9A-WY-Za-wy-z](?:-[A-Za-z0-9]{2,8})+)*"
    r"(?:-[xX](?:-[A-Za-z0-9]{1,8})+)?|[xX](?:-[A-Za-z0-9]{1,8})+|"
    + "|".join(_GRANDFATHERED_TAGS)
    + r")$"
)
_YEAR_PATTERN = re.compile(r"^[0-9]{4}$")
_MONTH_PATTERN = re.compile(r"^[0-9]{4}-(?:0[1-9]|1[0-2])$")
_DAY_PATTERN = re.compile(r"^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])$")
_DATETIME_PATTERN = re.compile(
    r"^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]"
    r"(?::[0-5][0-9](?:[.,][0-9]+)?)?(?:Z|[+-][0-9]{2}:[0-5][0-9])$"
)


# RFC 3986 Appendix A. AnyUrl checks IP literals after this lexical check.
_URI_ATOM = r"(?:[A-Za-z0-9._~!$&'()*+,;=-]|%[0-9A-Fa-f]{2})"
_URI_PCHAR = rf"(?:{_URI_ATOM}|[:@])"
_URI_AUTHORITY = rf"(?:{_URI_ATOM}|:)*@"
_URI_PATTERN = re.compile(
    rf"^[A-Za-z][A-Za-z0-9+.-]*:"
    rf"(?://(?:{_URI_AUTHORITY})?(?:{_URI_ATOM}*|\[[A-Za-z0-9:.!$&'()*+,;=_~-]+\])"
    rf"(?::[0-9]*)?(?:/{_URI_PCHAR}*)*"
    rf"|/(?:{_URI_PCHAR}+(?:/{_URI_PCHAR}*)*)?"
    rf"|{_URI_PCHAR}+(?:/{_URI_PCHAR}*)*|)"
    rf"(?:\?(?:{_URI_PCHAR}|[/?])*)?(?:#(?:{_URI_PCHAR}|[/?])*)?$"
)


def _validate_uri(value: Any) -> Any:
    # Check the original spelling before AnyUrl can strip controls or escape spaces.
    if not isinstance(value, (str, AnyUrl)):
        raise ValueError("URI must be a string or a validated URL.")
    if isinstance(value, str) and not _URI_PATTERN.fullmatch(value):
        raise ValueError("URI must use absolute RFC 3986 syntax and valid escapes.")
    return value


AbsoluteURI = Annotated[
    AnyUrl,
    BeforeValidator(_validate_uri),
    Field(json_schema_extra={"pattern": _URI_PATTERN.pattern}),
]


def _populated(*names: str) -> dict[str, Any]:
    return {
        "required": list(names),
        "properties": {name: {"not": {"type": "null"}} for name in names},
    }


def _content_schema(*names: str) -> dict[str, Any]:
    return {
        "anyOf": [_populated(name) for name in names],
        "x-validation-rules": [
            "At least one non-null value is required: " + ", ".join(names) + "."
        ],
    }


def _temporal_schema(schema: dict[str, Any]) -> None:
    schema["allOf"] = [
        {
            "if": {"anyOf": [_populated("start"), _populated("end")]},
            "then": _populated("relation", "precision"),
            "else": {
                "properties": {
                    name: {"type": "null"} for name in ("relation", "precision")
                }
            },
        }
    ]
    for relation, alternatives in {
        "point": [("start",)],
        "as_of": [("start",)],
        "interval": [("start", "end")],
        "open_interval": [("start",), ("end",)],
    }.items():
        branches = []
        for names in alternatives:
            branch = _populated(*names)
            branch["properties"].update(
                {
                    name: {"type": "null"}
                    for name in ("start", "end")
                    if name not in names
                }
            )
            branches.append(branch)
        schema["allOf"].append(
            {
                "if": {
                    "required": ["relation"],
                    "properties": {"relation": {"const": relation}},
                },
                "then": {"anyOf": branches},
            }
        )
    for precision, pattern in {
        "year": _YEAR_PATTERN,
        "month": _MONTH_PATTERN,
        "day": _DAY_PATTERN,
        "datetime": _DATETIME_PATTERN,
    }.items():
        schema["allOf"].append(
            {
                "if": {
                    "required": ["precision"],
                    "properties": {"precision": {"const": precision}},
                },
                "then": {
                    "properties": {
                        name: {"pattern": pattern.pattern} for name in ("start", "end")
                    }
                },
            }
        )
    schema["x-validation-rules"] = [
        "Normalized bounds require relation and precision; source-only expressions omit both.",
        "point and as_of require start only; interval requires both bounds; open_interval requires exactly one bound.",
        "Bounds must match the declared precision. Python additionally validates calendar dates and chronological ordering.",
    ]


def _standards(*mappings: tuple[str, str]) -> dict[str, object]:
    return {
        "x-standards": [
            {"term": term, "relationship": relationship}
            for term, relationship in mappings
        ]
    }


def _code_list(
    authority: str, identifier: str, uri: str, release: str | None = None
) -> dict[str, object]:
    metadata: dict[str, str] = {
        "authority": authority,
        "identifier": identifier,
        "uri": uri,
    }
    if release is not None:
        metadata["release"] = release
    return {"x-code-list": metadata}


class _SchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="after")
    @classmethod
    def _remove_exact_duplicates(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return value
        unique: list[Any] = []
        for item in value:
            if item not in unique:
                unique.append(item)
        return unique


class PresentationRole(str, Enum):
    """Identify a dimension's explicit table-presentation role."""

    ROW = "row"
    COLUMN = "column"


class AnalyticalRole(str, Enum):
    """Identify an explicitly stated analytical or axis role."""

    OUTCOME = "outcome"
    PREDICTOR = "predictor"
    INSTRUMENTAL = "instrumental"
    CONTROL = "control"
    X_AXIS = "x_axis"
    Y_AXIS = "y_axis"


class TemporalRelation(str, Enum):
    """Describe how normalized temporal bounds form an expression."""

    POINT = "point"
    INTERVAL = "interval"
    OPEN_INTERVAL = "open_interval"
    AS_OF = "as_of"


class TemporalPrecision(str, Enum):
    """Describe the precision of normalized temporal bounds."""

    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    DATETIME = "datetime"


class StatisticalFormValue(str, Enum):
    """Enumerate approved normalized statistical forms."""

    OBSERVED_VALUE = "observed_value"
    COUNT = "count"
    ARITHMETIC_MEAN = "arithmetic_mean"
    GEOMETRIC_MEAN = "geometric_mean"
    WEIGHTED_MEAN = "weighted_mean"
    WEIGHTED_VALUE = "weighted_value"
    MEDIAN = "median"
    SUM = "sum"
    WEIGHTED_SUM = "weighted_sum"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    RANGE = "range"
    INTERQUARTILE_RANGE = "interquartile_range"
    VARIANCE = "variance"
    STANDARD_DEVIATION = "standard_deviation"
    STANDARD_ERROR = "standard_error"
    MEAN_ABSOLUTE_DEVIATION = "mean_absolute_deviation"
    MEDIAN_ABSOLUTE_DEVIATION = "median_absolute_deviation"
    SKEWNESS = "skewness"
    KURTOSIS = "kurtosis"
    LOWER_BOUND = "lower_bound"
    UPPER_BOUND = "upper_bound"
    SCORE = "score"
    RANK = "rank"
    INDEX = "index"
    RATE = "rate"
    HARMONIC_MEAN = "harmonic_mean"
    TRIMMED_MEAN = "trimmed_mean"
    MODE = "mode"
    COEFFICIENT_OF_VARIATION = "coefficient_of_variation"
    VALID_CASES = "valid_cases"
    INVALID_CASES = "invalid_cases"
    PERCENTAGE_OF_VALID_CASES = "percentage_of_valid_cases"
    PERCENTAGE_OF_INVALID_CASES = "percentage_of_invalid_cases"
    QUARTILE = "quartile"
    QUINTILE = "quintile"
    DECILE = "decile"
    PERCENTILE = "percentile"
    RATIO = "ratio"
    PROPORTION = "proportion"
    PERCENTAGE = "percentage"
    CONFIDENCE_INTERVAL = "confidence_interval"
    COEFFICIENT = "coefficient"
    P_VALUE = "p_value"
    CHANGE = "change"


class VisualizationTypeValue(str, Enum):
    """Enumerate approved normalized visualization types."""

    TABLE = "table"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    AREA_CHART = "area_chart"
    PIE_CHART = "pie_chart"
    DONUT_CHART = "donut_chart"
    SCATTER_PLOT = "scatter_plot"
    BUBBLE_CHART = "bubble_chart"
    DOT_PLOT = "dot_plot"
    HISTOGRAM = "histogram"
    DENSITY_PLOT = "density_plot"
    HEATMAP = "heatmap"
    BOX_PLOT = "box_plot"
    VIOLIN_PLOT = "violin_plot"
    ERROR_BAR = "error_bar"
    ERROR_BAND = "error_band"
    RADAR_CHART = "radar_chart"
    TREEMAP = "treemap"
    MAP = "map"
    CHOROPLETH_MAP = "choropleth_map"
    SYMBOL_MAP = "symbol_map"
    NETWORK_DIAGRAM = "network_diagram"
    FLOW_DIAGRAM = "flow_diagram"
    TIMELINE = "timeline"
    DIAGRAM = "diagram"
    INFOGRAPHIC = "infographic"
    DASHBOARD = "dashboard"
    COMPOSITE_FIGURE = "composite_figure"


class TemporalGranularityValue(str, Enum):
    """Enumerate approved normalized temporal granularities."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMIANNUAL = "semiannual"
    ANNUAL = "annual"
    INSTANTANEOUS = "instantaneous"
    EVENT_BASED = "event_based"
    MULTI_YEAR = "multi_year"
    IRREGULAR = "irregular"


class GeographicLevelValue(str, Enum):
    """Enumerate approved normalized geographic levels."""

    GLOBAL = "global"
    WORLD_REGION = "world_region"
    COUNTRY = "country"
    ADMINISTRATIVE_AREA_1 = "administrative_area_1"
    ADMINISTRATIVE_AREA_2 = "administrative_area_2"
    ADMINISTRATIVE_AREA_3 = "administrative_area_3"
    LOCALITY = "locality"
    SITE = "site"


class Identifier(_SchemaModel):
    """Represent an assigned identifier and its optional authority context.

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
    """

    value: NonEmptyText = Field(description="Identifier exactly as assigned.")
    scheme: NonEmptyText | None = Field(
        default=None, description="Identifier scheme, when known."
    )
    issuer: NonEmptyText | None = Field(
        default=None, description="Issuing agent, when known."
    )
    uri: AbsoluteURI | None = Field(
        default=None, description="Authoritative absolute URI for the identifier."
    )


class ControlledTerm(_SchemaModel):
    """Represent a source-grounded term with optional normalization.

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
    """

    model_config = ConfigDict(
        json_schema_extra={
            **_content_schema("source_text", "normalized_value", "code", "uri"),
            "allOf": [{"if": _populated("code"), "then": _populated("scheme")}],
            "x-validation-rules": [
                "At least one of source_text, normalized_value, code, or uri must be non-null.",
                "A non-null code requires a non-null scheme.",
            ],
        }
    )

    source_text: NonEmptyText | None = Field(
        default=None, description="Faithful source-visible expression."
    )
    normalized_value: NonEmptyText | None = Field(
        default=None, description="Preferred application or vocabulary value."
    )
    code: NonEmptyText | None = Field(
        default=None, description="Code in the named scheme."
    )
    scheme: NonEmptyText | None = Field(
        default=None, description="Code-list or vocabulary identifier."
    )
    uri: AbsoluteURI | None = Field(
        default=None, description="Authoritative URI for the represented concept."
    )

    @model_validator(mode="after")
    def _validate_term(self) -> ControlledTerm:
        if not any((self.source_text, self.normalized_value, self.code, self.uri)):
            raise ValueError("A controlled term must contain a value.")
        if self.code is not None and self.scheme is None:
            raise ValueError("A controlled-term code requires a scheme.")
        return self


class StatisticalFormTerm(ControlledTerm):
    """Represent a known or source-only statistical form.

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
    """

    normalized_value: StatisticalFormValue | None = Field(
        default=None, description="Approved normalized statistical form."
    )


class VisualizationTypeTerm(ControlledTerm):
    """Represent a known or source-only visualization type.

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
    """

    normalized_value: VisualizationTypeValue | None = Field(
        default=None, description="Approved normalized visualization type."
    )


class TemporalGranularityTerm(ControlledTerm):
    """Represent a known or source-only temporal granularity.

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
    """

    normalized_value: TemporalGranularityValue | None = Field(
        default=None, description="Approved normalized temporal granularity."
    )


class GeographicLevelTerm(ControlledTerm):
    """Represent a known or source-only geographic reporting level.

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
    """

    normalized_value: GeographicLevelValue | None = Field(
        default=None, description="Approved normalized geographic level."
    )


class EntityReference(_SchemaModel):
    """Represent a named project, organization, source, or component.

    Parameters
    ----------
    name : str
        Source-visible entity name.
    identifiers : list[Identifier] | None
        Assigned identifiers for the entity.
    """

    name: NonEmptyText = Field(description="Source-visible entity name.")
    identifiers: list[Identifier] | None = Field(
        default=None, min_length=1, description="Assigned entity identifiers."
    )


class Attribution(EntityReference):
    """Represent a named agent and its explicit attribution role.

    Parameters
    ----------
    name : str
        Source-visible credited-agent name.
    identifiers : list[Identifier] | None
        Assigned identifiers for the agent.
    role : ControlledTerm
        Open, source-grounded attribution role.
    """

    role: ControlledTerm = Field(description="Explicit source-grounded agent role.")


class Unit(_SchemaModel):
    """Represent a displayed unit and its optional normalized qualifiers.

    Parameters
    ----------
    source_text : str
        Displayed unit expression.
    code : str | None
        Exact UN/CEFACT Recommendation 20 code.
    multiplier_exponent : int | None
        SDMX unit-multiplier exponent.
    """

    source_text: NonEmptyText = Field(description="Displayed unit expression.")
    code: (
        Annotated[str, StringConstraints(strict=True, pattern=r"^[A-Z0-9]{1,3}$")]
        | None
    ) = Field(
        default=None,
        description="Exact UN/CEFACT Recommendation 20 common code.",
        json_schema_extra=_code_list(
            "UNECE",
            "Recommendation 20",
            "https://unece.org/trade/uncefact/cl-recommendations",
        ),
    )
    multiplier_exponent: Annotated[int, Field(strict=True)] | None = Field(
        default=None,
        description="Base-10 SDMX unit-multiplier exponent.",
        json_schema_extra=_code_list(
            "SDMX",
            "CL_UNIT_MULT",
            "https://registry.sdmx.org/items/codelist.html",
            "1.1",
        ),
    )


class Currency(_SchemaModel):
    """Represent a displayed currency and optional ISO 4217 code.

    Parameters
    ----------
    source_text : str
        Displayed currency expression.
    code : str | None
        Uppercase ISO 4217 alphabetic code.
    """

    source_text: NonEmptyText = Field(description="Displayed currency expression.")
    code: (
        Annotated[str, StringConstraints(strict=True, pattern=r"^[A-Z]{3}$")] | None
    ) = Field(
        default=None,
        description="Uppercase ISO 4217 alphabetic code.",
        json_schema_extra=_code_list(
            "ISO", "ISO 4217", "https://www.iso.org/iso-4217-currency-codes.html"
        ),
    )


class Language(_SchemaModel):
    """Represent a snapshot language using source text and/or BCP 47.

    Parameters
    ----------
    source_text : str | None
        Displayed language label, when present.
    tag : str | None
        Canonical BCP 47 language tag.
    """

    model_config = ConfigDict(json_schema_extra=_content_schema("source_text", "tag"))

    source_text: NonEmptyText | None = Field(
        default=None, description="Displayed language label, when present."
    )
    tag: (
        Annotated[
            NonEmptyText,
            WithJsonSchema(
                {"type": "string", "minLength": 1, "pattern": _BCP47_PATTERN.pattern}
            ),
        ]
        | None
    ) = Field(
        default=None,
        description="Canonical BCP 47 language tag.",
        json_schema_extra=_code_list(
            "IETF/IANA",
            "BCP 47",
            "https://www.iana.org/assignments/language-subtag-registry/",
        ),
    )

    @field_validator("tag")
    @classmethod
    def _validate_tag(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _BCP47_PATTERN.fullmatch(value):
            raise ValueError("Language tag must use BCP 47 syntax.")
        if value in _GRANDFATHERED_TAGS:
            return value
        parts = value.split("-")
        variants: set[str] = set()
        singletons: set[str] = set()
        in_extension = False
        for part in [] if parts[0].lower() == "x" else parts[1:]:
            lower = part.lower()
            if lower == "x":
                break
            if len(part) == 1:
                if lower in singletons:
                    raise ValueError(
                        "Language tag cannot repeat an extension singleton."
                    )
                singletons.add(lower)
                in_extension = True
            elif not in_extension and (
                len(part) >= 5 or (len(part) == 4 and part[0].isdigit())
            ):
                if lower in variants:
                    raise ValueError("Language tag cannot repeat a variant.")
                variants.add(lower)
        if parts[0].lower() == "x":
            canonical = [part.lower() for part in parts]
            if value != "-".join(canonical):
                raise ValueError("Language tag must use canonical BCP 47 casing.")
            return value
        canonical = [parts[0].lower()]
        extension = False
        for part in parts[1:]:
            if len(part) == 1:
                extension = True
                canonical.append(part.lower())
            elif extension:
                canonical.append(part.lower())
            elif len(part) == 4 and part.isalpha():
                canonical.append(part.title())
            elif (len(part) == 2 and part.isalpha()) or (
                len(part) == 3 and part.isdigit()
            ):
                canonical.append(part.upper())
            else:
                canonical.append(part.lower())
        if value != "-".join(canonical):
            raise ValueError("Language tag must use canonical BCP 47 casing.")
        return value

    @model_validator(mode="after")
    def _validate_language(self) -> Language:
        if self.source_text is None and self.tag is None:
            raise ValueError("A language requires source_text or tag.")
        return self


class Variable(_SchemaModel):
    """Represent a measured variable and its applicable qualifiers.

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
    """

    name: NonEmptyText = Field(
        description="Explicitly named measured concept.",
        json_schema_extra=_standards(("https://schema.org/variableMeasured", "close")),
    )
    unit: Unit | None = Field(
        default=None,
        description="Applicable unit.",
        json_schema_extra=_standards(
            ("https://schema.org/unitCode", "related_structural")
        ),
    )
    currency: Currency | None = Field(
        default=None,
        description="Applicable currency.",
        json_schema_extra=_standards(("https://schema.org/currency", "close")),
    )
    analytical_roles: list[AnalyticalRole] | None = Field(
        default=None, min_length=1, description="Explicit analytical or axis roles."
    )
    statistical_forms: list[StatisticalFormTerm] | None = Field(
        default=None,
        min_length=1,
        description="Applicable statistical forms.",
        json_schema_extra=_standards(("https://schema.org/statType", "close")),
    )


class CategoryGroup(_SchemaModel):
    """Represent one explicit nonrecursive category grouping.

    Parameters
    ----------
    name : str
        Explicit group heading.
    categories : list[ControlledTerm]
        Categories directly contained by the group.
    """

    name: NonEmptyText = Field(description="Explicit category-group heading.")
    categories: list[ControlledTerm] = Field(
        min_length=1, description="Categories directly contained by the group."
    )


class Dimension(_SchemaModel):
    """Represent a classificatory dimension and its visible organization.

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
    """

    name: NonEmptyText = Field(description="Classificatory dimension name.")
    categories: list[ControlledTerm] | None = Field(
        default=None,
        min_length=1,
        description="Ordered ungrouped categories.",
        json_schema_extra=_standards(
            ("http://www.w3.org/2004/02/skos/core#Concept", "related_structural")
        ),
    )
    category_groups: list[CategoryGroup] | None = Field(
        default=None,
        min_length=1,
        description="One level of explicit category groups.",
        json_schema_extra=_standards(
            ("http://www.w3.org/2004/02/skos/core#broader", "related_structural")
        ),
    )
    presentation_roles: list[PresentationRole] | None = Field(
        default=None,
        min_length=1,
        description="Explicit table-presentation roles.",
    )


class TemporalExpression(_SchemaModel):
    """Represent source-visible time with optional normalized bounds.

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
    """

    model_config = ConfigDict(json_schema_extra=_temporal_schema)

    source_text: NonEmptyText = Field(description="Complete source time expression.")
    start: NonEmptyText | None = Field(default=None, description="Normalized start.")
    end: NonEmptyText | None = Field(default=None, description="Normalized end.")
    relation: TemporalRelation | None = Field(
        default=None, description="Relationship between normalized bounds."
    )
    precision: TemporalPrecision | None = Field(
        default=None, description="Precision of normalized bounds."
    )

    @model_validator(mode="after")
    def _validate_bounds(self) -> TemporalExpression:
        bounds = [bound for bound in (self.start, self.end) if bound is not None]
        if not bounds:
            if self.relation is not None or self.precision is not None:
                raise ValueError("Temporal relation and precision require a bound.")
            return self
        if self.relation is None or self.precision is None:
            raise ValueError(
                "Normalized temporal bounds require relation and precision."
            )
        if self.relation in {TemporalRelation.POINT, TemporalRelation.AS_OF}:
            if self.start is None or self.end is not None:
                raise ValueError("point and as_of require start only.")
        elif self.relation is TemporalRelation.INTERVAL:
            if self.start is None or self.end is None:
                raise ValueError("interval requires start and end.")
        elif len(bounds) != 1:
            raise ValueError("open_interval requires exactly one bound.")
        for bound in bounds:
            _validate_temporal_value(bound, self.precision)
        if self.start is not None and self.end is not None:
            if _temporal_sort_value(self.start, self.precision) > _temporal_sort_value(
                self.end, self.precision
            ):
                raise ValueError("Temporal start cannot be after end.")
        return self


def _validate_temporal_value(value: str, precision: TemporalPrecision) -> None:
    if precision is TemporalPrecision.YEAR and _YEAR_PATTERN.fullmatch(value):
        return
    if precision is TemporalPrecision.MONTH and _MONTH_PATTERN.fullmatch(value):
        return
    if precision is TemporalPrecision.DAY and _DAY_PATTERN.fullmatch(value):
        date.fromisoformat(value)
        return
    if precision is TemporalPrecision.DATETIME and _DATETIME_PATTERN.fullmatch(value):
        parsed, _ = _parse_datetime(value)
        if parsed.tzinfo is not None:
            return
    raise ValueError(f"Temporal value {value!r} does not match {precision.value}.")


def _parse_datetime(value: str) -> tuple[datetime, Decimal]:
    # Parse whole seconds on Python 3.10; compare the original fraction exactly.
    fraction = re.search(r"[.,]([0-9]+)(?=Z|[+-][0-9]{2}:[0-9]{2}$)", value)
    if fraction:
        seconds = Decimal("0." + fraction.group(1))
        value = value[: fraction.start()] + value[fraction.end() :]
    else:
        seconds = Decimal(0)
    return datetime.fromisoformat(value.replace("Z", "+00:00")), seconds


def _temporal_sort_value(
    value: str, precision: TemporalPrecision
) -> str | tuple[datetime, Decimal]:
    if precision is TemporalPrecision.DATETIME:
        return _parse_datetime(value)
    return value


class TemporalCoverage(_SchemaModel):
    """Group represented-data time and granularity.

    Parameters
    ----------
    period : TemporalExpression | None
        Represented-data temporal expression.
    granularity : TemporalGranularityTerm | None
        Reporting interval or temporal resolution.
    """

    model_config = ConfigDict(
        json_schema_extra=_content_schema("period", "granularity")
    )

    period: TemporalExpression | None = Field(
        default=None,
        description="Represented-data temporal expression.",
        json_schema_extra=_standards(
            ("https://schema.org/temporalCoverage", "exact"),
            ("http://purl.org/dc/terms/temporal", "close"),
        ),
    )
    granularity: TemporalGranularityTerm | None = Field(
        default=None, description="Reporting interval or temporal resolution."
    )

    @model_validator(mode="after")
    def _validate_content(self) -> TemporalCoverage:
        if self.period is None and self.granularity is None:
            raise ValueError("Temporal coverage must contain period or granularity.")
        return self


class Place(_SchemaModel):
    """Represent a source-grounded place with optional standard identifiers.

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
    """

    model_config = ConfigDict(json_schema_extra=_content_schema("source_text", "name"))

    source_text: NonEmptyText | None = Field(
        default=None, description="Displayed place expression."
    )
    name: NonEmptyText | None = Field(default=None, description="Preferred place name.")
    country_code: (
        Annotated[str, StringConstraints(strict=True, pattern=r"^[A-Z]{2}$")] | None
    ) = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country code.",
        json_schema_extra=_code_list(
            "ISO", "ISO 3166-1", "https://www.iso.org/iso-3166-country-codes.html"
        ),
    )
    subdivision_code: (
        Annotated[
            str, StringConstraints(strict=True, pattern=r"^[A-Z]{2}-[A-Z0-9]{1,3}$")
        ]
        | None
    ) = Field(
        default=None,
        description="ISO 3166-2 subdivision code.",
        json_schema_extra=_code_list(
            "ISO", "ISO 3166-2", "https://www.iso.org/iso-3166-country-codes.html"
        ),
    )
    m49_code: (
        Annotated[str, StringConstraints(strict=True, pattern=r"^[0-9]{3}$")] | None
    ) = Field(
        default=None,
        description="UN M49 statistical-area code.",
        json_schema_extra=_code_list(
            "United Nations",
            "M49",
            "https://unstats.un.org/unsd/methodology/m49/",
        ),
    )
    identifiers: list[Identifier] | None = Field(
        default=None, min_length=1, description="Other authoritative identifiers."
    )

    @model_validator(mode="after")
    def _validate_name(self) -> Place:
        if self.source_text is None and self.name is None:
            raise ValueError("A place requires source_text or name.")
        return self


class GeographicLocation(Place):
    """Represent an additional named location and its optional role and type.

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
    """

    role: ControlledTerm | None = Field(
        default=None, description="Explicit source-grounded geographic role."
    )
    type: ControlledTerm | None = Field(
        default=None, description="Physical or administrative location type."
    )


class GeographicCoverage(_SchemaModel):
    """Group overall geographic scope, locations, and reporting level.

    Parameters
    ----------
    scope : Place | None
        Overall geographic coverage or focus.
    locations : list[GeographicLocation] | None
        Additional named locations.
    level : GeographicLevelTerm | None
        Administrative, geographic, or reporting level.
    """

    model_config = ConfigDict(
        json_schema_extra=_content_schema("scope", "locations", "level")
    )

    scope: Place | None = Field(
        default=None,
        description="Overall geographic coverage or focus.",
        json_schema_extra=_standards(("https://schema.org/spatialCoverage", "exact")),
    )
    locations: list[GeographicLocation] | None = Field(
        default=None,
        min_length=1,
        description="Additional named locations.",
        json_schema_extra=_standards(
            ("https://schema.org/spatialCoverage", "related_structural")
        ),
    )
    level: GeographicLevelTerm | None = Field(
        default=None, description="Geographic or reporting level."
    )

    @model_validator(mode="after")
    def _validate_content(self) -> GeographicCoverage:
        if self.scope is None and self.locations is None and self.level is None:
            raise ValueError("Geographic coverage must contain a value.")
        return self


class Provenance(_SchemaModel):
    """Separate derivation sources from credited agents.

    Parameters
    ----------
    sources : list[EntityReference] | None
        Entities from which represented data derive.
    attributions : list[Attribution] | None
        Agents explicitly credited for the snapshot artifact.
    """

    model_config = ConfigDict(
        json_schema_extra=_content_schema("sources", "attributions")
    )

    sources: list[EntityReference] | None = Field(
        default=None,
        min_length=1,
        description="Represented-data derivation sources.",
        json_schema_extra=_standards(
            ("http://www.w3.org/ns/prov#wasDerivedFrom", "related_structural"),
            ("http://purl.org/dc/terms/source", "close"),
        ),
    )
    attributions: list[Attribution] | None = Field(
        default=None,
        min_length=1,
        description="Role-bearing credited agents.",
        json_schema_extra=_standards(
            ("http://www.w3.org/ns/prov#wasAttributedTo", "related_structural")
        ),
    )

    @model_validator(mode="after")
    def _validate_content(self) -> Provenance:
        if self.sources is None and self.attributions is None:
            raise ValueError("Provenance must contain a source or attribution.")
        return self


class Project(_SchemaModel):
    """Represent project, program, operation, or initiative context.

    Parameters
    ----------
    name : str | None
        Associated project-context name.
    identifiers : list[Identifier] | None
        Formal project or operation identifiers.
    components : list[EntityReference] | None
        Explicitly identified subordinate components.
    """

    model_config = ConfigDict(
        json_schema_extra=_content_schema("name", "identifiers", "components")
    )

    name: NonEmptyText | None = Field(
        default=None,
        description="Associated project-context name.",
        json_schema_extra=_standards(("https://schema.org/name", "exact")),
    )
    identifiers: list[Identifier] | None = Field(
        default=None,
        min_length=1,
        description="Formal project identifiers.",
        json_schema_extra=_standards(
            ("https://schema.org/identifier", "standard_broader")
        ),
    )
    components: list[EntityReference] | None = Field(
        default=None,
        min_length=1,
        description="Named project components.",
        json_schema_extra=_standards(
            ("https://schema.org/hasPart", "related_structural")
        ),
    )

    @model_validator(mode="after")
    def _validate_content(self) -> Project:
        if self.name is None and self.identifiers is None and self.components is None:
            raise ValueError("Project must contain a name, identifier, or component.")
        return self


class Financing(_SchemaModel):
    """Group project-financing measures, funders, and instruments.

    Parameters
    ----------
    measures : list[ControlledTerm] | None
        Financial quantities or funding-related measures.
    funders : list[EntityReference] | None
        Named funding sources.
    instruments : list[ControlledTerm] | None
        Financing mechanisms.
    """

    model_config = ConfigDict(
        json_schema_extra=_content_schema("measures", "funders", "instruments")
    )

    measures: list[ControlledTerm] | None = Field(
        default=None, min_length=1, description="Project-financing measures."
    )
    funders: list[EntityReference] | None = Field(
        default=None,
        min_length=1,
        description="Named funding sources.",
        json_schema_extra=_standards(("https://schema.org/funder", "exact")),
    )
    instruments: list[ControlledTerm] | None = Field(
        default=None,
        min_length=1,
        description="Financing mechanisms.",
        json_schema_extra=_standards(
            (
                "https://reference.iatistandard.org/en/iati-standard/203/codelists/financetype/",
                "close",
            )
        ),
    )

    @model_validator(mode="after")
    def _validate_content(self) -> Financing:
        if self.measures is None and self.funders is None and self.instruments is None:
            raise ValueError("Financing must contain a measure, funder, or instrument.")
        return self


class DataSnapshotMetadata(_SchemaModel):
    """Represent canonical semantic metadata for one data snapshot.

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
    """

    model_config = ConfigDict(
        extra="forbid",
        title="Data Snapshot Metadata Schema v1.2",
        json_schema_extra={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "x-schema-version": "1.2",
            "x-status": "implementation",
            "x-validation-rules": [
                "Python is the canonical validator. JSON Schema enforces exported structural rules; format assertions require a format-aware validator.",
                "Python additionally applies NFC normalization, outer whitespace trimming, and stable exact deduplication.",
                "Python additionally checks URI syntax before URL normalization, language-tag casing and uniqueness, calendar dates, and chronological ordering.",
                "Missing and null values are equivalent. Serialize records with exclude_none=True to omit unavailable values.",
                "External registry membership, source-grounding, and semantic correctness are not validated. Unpinned code-list metadata identifies a syntax authority only.",
            ],
        },
    )

    title: NonEmptyText | None = Field(
        default=None,
        description="Primary title, caption, or heading identifying the snapshot.",
        json_schema_extra=_standards(
            ("http://purl.org/dc/terms/title", "exact"),
            ("https://schema.org/name", "exact"),
        ),
    )
    document_label: NonEmptyText | None = Field(
        default=None,
        description="Label assigned within the parent source document.",
        json_schema_extra=_standards(
            (
                "https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/label.html",
                "close",
            ),
            ("https://schema.org/identifier", "standard_broader"),
        ),
    )
    subject_domains: list[ControlledTerm] | None = Field(
        default=None,
        min_length=1,
        description="Broad thematic, policy, or sectoral domains.",
        json_schema_extra=_standards(
            ("http://purl.org/dc/terms/subject", "standard_broader"),
            ("https://schema.org/about", "standard_broader"),
        ),
    )
    subject_summary: NonEmptyText | None = Field(
        default=None,
        description="Concise summary of the primary analytical subject or purpose.",
        json_schema_extra=_standards(
            ("https://schema.org/abstract", "close"),
            ("http://purl.org/dc/terms/description", "standard_broader"),
        ),
    )
    panel_titles: list[NonEmptyText] | None = Field(
        default=None,
        min_length=1,
        description="Ordered titles explicitly shown for individual panels.",
        json_schema_extra=_standards(
            (
                "https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/fig-group.html",
                "close",
            ),
            ("https://schema.org/hasPart", "related_structural"),
        ),
    )
    variables: list[Variable] | None = Field(
        default=None,
        min_length=1,
        description="Explicitly named measured concepts and their qualifiers.",
        json_schema_extra=_standards(
            ("https://schema.org/variableMeasured", "close"),
            ("https://ddialliance.org/Specification/DDI-Lifecycle/3.3/", "close"),
        ),
    )
    dimensions: list[Dimension] | None = Field(
        default=None,
        min_length=1,
        description="Classificatory dimensions and their visible organization.",
        json_schema_extra=_standards(
            ("https://sdmx.org/", "close"),
            ("https://ddialliance.org/Specification/DDI-Lifecycle/3.3/", "close"),
        ),
    )
    population_group: ControlledTerm | None = Field(
        default=None,
        description="Human population or beneficiary group represented by the data.",
        json_schema_extra=_standards(
            (
                "https://docs.ddialliance.org/DDI-Lifecycle/3.3/xmlschema/schemas/conceptualcomponent_xsd/elements/Universe.html",
                "close",
            ),
            ("https://schema.org/populationType", "close"),
        ),
    )
    visualization_types: list[VisualizationTypeTerm] | None = Field(
        default=None,
        min_length=1,
        description="Explicitly visible visualization forms used by the snapshot.",
        json_schema_extra=_standards(
            ("http://purl.org/dc/terms/type", "standard_broader"),
            ("https://schema.org/additionalType", "standard_broader"),
        ),
    )
    temporal_coverage: TemporalCoverage | None = Field(
        default=None,
        description="When the represented data apply and their granularity.",
        json_schema_extra=_standards(
            ("https://schema.org/temporalCoverage", "exact"),
            ("http://purl.org/dc/terms/temporal", "close"),
        ),
    )
    geographic_coverage: GeographicCoverage | None = Field(
        default=None,
        description="Overall geographic scope, additional locations, and level.",
        json_schema_extra=_standards(
            ("https://schema.org/spatialCoverage", "exact"),
            ("http://purl.org/dc/terms/spatial", "exact"),
        ),
    )
    comparisons: list[NonEmptyText] | None = Field(
        default=None,
        min_length=1,
        description="Explicit comparative expressions or named comparators.",
    )
    provenance: Provenance | None = Field(
        default=None,
        description="Represented-data sources and artifact attributions.",
    )
    languages: list[Language] | None = Field(
        default=None,
        min_length=1,
        description="Languages explicitly used within the snapshot.",
        json_schema_extra=_standards(
            ("https://schema.org/inLanguage", "exact"),
            ("http://purl.org/dc/terms/language", "exact"),
        ),
    )
    interpretive_notes: list[NonEmptyText] | None = Field(
        default=None,
        min_length=1,
        description="Complete explanatory, methodological, uncertainty, sample-size, or provenance statements.",
        json_schema_extra=_standards(
            ("http://purl.org/dc/terms/description", "standard_broader"),
            ("https://schema.org/description", "standard_broader"),
        ),
    )
    project: Project | None = Field(
        default=None,
        description="Associated project, program, operation, or initiative.",
        json_schema_extra=_standards(
            ("https://schema.org/Project", "standard_narrower"),
            (
                "https://iatistandard.org/en/iati-standard/203/activity-standard/",
                "close",
            ),
        ),
    )
    intervention_types: list[ControlledTerm] | None = Field(
        default=None,
        min_length=1,
        description="Explicit interventions, services, policies, or operational activities.",
    )
    financing: Financing | None = Field(
        default=None,
        description="Project-financing measures, funders, and instruments.",
    )
    analysis_methods: list[ControlledTerm] | None = Field(
        default=None,
        min_length=1,
        description="Explicit analytical, statistical, or computational methods.",
        json_schema_extra=_standards(
            ("https://schema.org/measurementTechnique", "related_structural"),
            ("http://www.w3.org/ns/prov#Activity", "related_structural"),
        ),
    )
    data_collection_methods: list[ControlledTerm] | None = Field(
        default=None,
        min_length=1,
        description="Explicit methods or instruments used to collect underlying data.",
        json_schema_extra=_standards(
            (
                "https://docs.ddialliance.org/DDI-Lifecycle/3.3/model/composite-types/ModeOfCollectionType/",
                "exact",
            ),
            ("https://schema.org/measurementMethod", "close"),
        ),
    )
