"""Tests for Data Snapshot Metadata Schema v1.3."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from pydantic import BaseModel, TypeAdapter, ValidationError

import data_snapshot.metadata_schema.generation as schema_generation
import data_snapshot.metadata_schema as metadata_models
from data_snapshot.metadata_schema import (
    AxisAssignment,
    CodedTerm,
    Currency,
    DataSnapshotMetadata,
    Dimension,
    GeographicLevelTerm,
    Language,
    Identifier,
    Place,
    StatisticalFormTerm,
    TemporalExpression,
    TemporalGranularityTerm,
    Unit,
    Variable,
    VisualizationTypeTerm,
)
from data_snapshot.metadata_schema.generation import (
    render_json_schema,
    render_markdown_reference,
    serialize_metadata_schema,
    write_schema_artifacts,
)


def test_minimal_record_is_empty_and_forbids_unknown_fields() -> None:
    """The all-optional root accepts omission but rejects schema drift."""
    assert DataSnapshotMetadata().model_dump(exclude_none=True) == {}
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        DataSnapshotMetadata.model_validate({"source_document_title": "Removed"})


def test_field_examples_validate_and_are_exported() -> None:
    """Keep examples valid for every public model field and in generated JSON."""
    for name in metadata_models.__all__:
        model = getattr(metadata_models, name)
        if not issubclass(model, BaseModel):
            continue
        properties = model.model_json_schema()["properties"]
        for field_name, field in model.model_fields.items():
            assert field.examples, f"{name}.{field_name} has no examples"
            assert properties[field_name]["examples"] == field.examples
            adapter = TypeAdapter(field.rebuild_annotation())
            for example in field.examples:
                adapter.validate_python(example)
                if model is DataSnapshotMetadata:
                    model.model_validate({field_name: example})


def test_markdown_renders_every_example_as_a_json_value() -> None:
    """Preserve nested arrays, Unicode, and all field examples in the reference."""
    schema = DataSnapshotMetadata.model_json_schema()
    reference = render_markdown_reference()
    for definition in [schema, *schema["$defs"].values()]:
        for name, field in definition.get("properties", {}).items():
            assert f"#### `{name}`" in reference
            assert "**Definition**\n\n" + field["description"] + "\n" in reference
            for example in field["examples"]:
                block = (
                    "```json\n"
                    + json.dumps(example, ensure_ascii=False, indent=2)
                    + "\n```"
                )
                assert block in reference
    assert "do not constrain accepted values" in reference


def _v111_fields() -> dict[str, tuple[str, list[str]]]:
    """Read historical definitions and example text for fidelity checks."""
    path = Path(__file__).resolve().parents[1] / (
        "src/data_snapshot/metadata_extraction/schema/"
        "Data Snapshot Metadata Schema v1.1.1.md"
    )
    fields = {}
    for name, section in re.findall(
        r"^### (\w+)\n(.*?)(?=^### |\Z)", path.read_text(encoding="utf-8"), re.M | re.S
    ):
        definition, examples = section.split("**Definition**", 1)[1].split(
            "**Examples**", 1
        )
        fields[name] = (
            definition.strip(),
            re.findall(r"^- (.*)$", examples.split("\n---", 1)[0], re.M),
        )
    return fields


def test_uncontested_descriptions_match_v111_verbatim() -> None:
    """Prevent shortening historical definitions that fit the approved design."""
    destinations = {
        "title": ("DataSnapshotMetadata", "title"),
        "internal_identifier": ("DataSnapshotMetadata", "document_label"),
        "subject_domain": ("DataSnapshotMetadata", "subject_domains"),
        "subject_summary": ("DataSnapshotMetadata", "subject_summary"),
        "panel_title": ("DataSnapshotMetadata", "panel_titles"),
        "category_dimension": ("Dimension", "name"),
        "category_labels": ("Dimension", "categories"),
        "population_group": ("DataSnapshotMetadata", "population_group"),
        "temporal_granularity": ("TemporalCoverage", "granularity"),
        "geographic_scope": ("GeographicCoverage", "scope"),
        "geographic_granularity": ("GeographicCoverage", "level"),
        "geographic_role": ("GeographicLocation", "role"),
        "unit_of_measure": ("Variable", "unit"),
        "currency": ("Variable", "currency"),
        "measure_type": ("Variable", "statistical_forms"),
        "comparison_group": ("DataSnapshotMetadata", "comparisons"),
        "language": ("DataSnapshotMetadata", "languages"),
        "project_name": ("Project", "name"),
        "project_identifier": ("Project", "identifiers"),
        "project_component": ("Project", "components"),
        "intervention_type": ("DataSnapshotMetadata", "intervention_types"),
        "financial_measure": ("Financing", "measures"),
        "financing_source": ("Financing", "funders"),
        "financing_instrument": ("Financing", "instruments"),
        "analysis_method": ("DataSnapshotMetadata", "analysis_methods"),
        "data_collection_method": ("DataSnapshotMetadata", "data_collection_methods"),
    }
    legacy = _v111_fields()
    assert DataSnapshotMetadata.model_fields["interpretive_notes"].description == (
        legacy["interpretive_note"][0]
    )
    for name, (model_name, field_name) in destinations.items():
        model = getattr(metadata_models, model_name)
        assert model.model_fields[field_name].description == legacy[name][0], name


def test_uncontested_examples_preserve_all_v111_text_in_order() -> None:
    """Compare every original example at its v1.3 destination without sampling."""
    # Grouped labels and provenance use the approved structural adaptations below.
    destinations = {
        "title": ("DataSnapshotMetadata", "title", ()),
        "internal_identifier": ("DataSnapshotMetadata", "document_label", ()),
        "subject_domain": (
            "DataSnapshotMetadata",
            "subject_domains",
            (0,),
        ),
        "subject_summary": ("DataSnapshotMetadata", "subject_summary", ()),
        "panel_title": ("DataSnapshotMetadata", "panel_titles", (0,)),
        "variable_name": ("Variable", "name", ()),
        "category_dimension": ("Dimension", "name", ()),
        "population_group": (
            "DataSnapshotMetadata",
            "population_group",
            (),
        ),
        "time_period": ("TemporalCoverage", "period", ("source_text",)),
        "temporal_granularity": ("TemporalCoverage", "granularity", ("source_text",)),
        "geographic_scope": ("GeographicCoverage", "scope", ("source_text",)),
        "geographic_entities": ("GeographicCoverage", "locations", (0, "name")),
        "geographic_granularity": ("GeographicCoverage", "level", ("source_text",)),
        "geographic_role": ("GeographicLocation", "role", ()),
        "location_type": ("GeographicLocation", "type", ("source_text",)),
        "unit_of_measure": ("Variable", "unit", ("source_text",)),
        "currency": ("Variable", "currency", ("source_text",)),
        "measure_type": ("Variable", "statistical_forms", (0, "source_text")),
        "comparison_group": ("DataSnapshotMetadata", "comparisons", (0,)),
        "visualization_type": (
            "DataSnapshotMetadata",
            "visualization_types",
            (0, "source_text"),
        ),
        "language": ("DataSnapshotMetadata", "languages", (0, "source_text")),
        "interpretive_note": ("DataSnapshotMetadata", "interpretive_notes", (0,)),
        "project_name": ("Project", "name", ()),
        "project_identifier": ("Project", "identifiers", (0, "value")),
        "project_component": ("Project", "components", (0, "name")),
        "intervention_type": (
            "DataSnapshotMetadata",
            "intervention_types",
            (0,),
        ),
        "financial_measure": ("Financing", "measures", (0,)),
        "financing_source": ("Financing", "funders", (0, "name")),
        "financing_instrument": ("Financing", "instruments", (0, "source_text")),
        "analysis_method": (
            "DataSnapshotMetadata",
            "analysis_methods",
            (0,),
        ),
        "data_collection_method": (
            "DataSnapshotMetadata",
            "data_collection_methods",
            (0, "source_text"),
        ),
    }
    legacy = _v111_fields()
    for name, (model_name, field_name, path) in destinations.items():
        values = []
        for example in (
            getattr(metadata_models, model_name).model_fields[field_name].examples
        ):
            for key in path:
                example = example[key]
            values.append(example)
        assert values == legacy[name][1], name
    assert [
        ", ".join(category["source_text"] for category in example)
        for example in metadata_models.Dimension.model_fields["categories"].examples
    ] == legacy["category_labels"][1]
    provenance = DataSnapshotMetadata.model_fields["provenance"].examples
    assert [
        entity["name"]
        for example in provenance
        for entities in example.values()
        for entity in entities
    ] == legacy["data_source"][1]
    assert [
        example[0]["name"]
        for field in ("sources", "attributions")
        for example in metadata_models.Provenance.model_fields[field].examples
    ] == legacy["data_source"][1]
    dimensions = DataSnapshotMetadata.model_fields["dimensions"].examples
    for name, role in [("row_dimension", "row"), ("column_dimension", "column")]:
        assert [
            example[0]["name"]
            for example in dimensions
            if example[0].get("presentation_roles") == [role]
        ] == legacy[name][1]


def test_representative_record_preserves_nested_relationships() -> None:
    """A bounded-snapshot record keeps variable and context relationships."""
    record = DataSnapshotMetadata.model_validate(
        {
            "title": "Total project financing",
            "document_label": "Table 3",
            "subject_domains": ["Health"],
            "panel_titles": ["Credit", "Grant"],
            "variables": [
                {
                    "name": "Project cost",
                    "unit": {
                        "source_text": "US$ million",
                        "multiplier_exponent": 6,
                    },
                    "currency": {"source_text": "US$", "code": "USD"},
                    "analytical_roles": ["outcome"],
                    "statistical_forms": [
                        {
                            "source_text": "Total",
                            "normalized_value": "sum",
                        }
                    ],
                }
            ],
            "dimensions": [
                {
                    "name": "Incident typology",
                    "presentation_roles": ["column"],
                    "category_groups": [
                        {
                            "name": "Violation of the right to liberty",
                            "categories": [
                                {"source_text": "Arbitrary arrests"},
                                {"source_text": "Abductions"},
                            ],
                        }
                    ],
                }
            ],
            "population_group": "Beneficiaries",
            "visualization_types": [{"normalized_value": "table"}],
            "temporal_coverage": {
                "period": {
                    "source_text": "2020–2022",
                    "start": "2020",
                    "end": "2022",
                    "relation": "interval",
                    "precision": "year",
                },
                "granularity": {
                    "source_text": "Annual",
                    "normalized_value": "annual",
                },
            },
            "geographic_coverage": {
                "scope": {
                    "source_text": "Niger",
                    "name": "Niger",
                    "country_code": "NE",
                },
                "level": {
                    "source_text": "Country",
                    "normalized_value": "country",
                },
            },
            "comparisons": ["Credit vs Grant"],
            "provenance": {
                "sources": [{"name": "Project financing table"}],
                "attributions": [
                    {"name": "World Bank", "role": {"source_text": "producer"}}
                ],
            },
            "languages": [{"source_text": "English", "tag": "en"}],
            "interpretive_notes": ["Amounts are in US$ millions."],
            "project": {
                "name": "Niger COVID-19 Emergency Response Project",
                "identifiers": [
                    {"value": "P173846", "scheme": "World Bank project ID"}
                ],
                "components": [{"name": "Crisis Response Window"}],
            },
            "intervention_types": ["Emergency response"],
            "financing": {
                "measures": ["Financing gap"],
                "funders": [{"name": "International Development Association"}],
                "instruments": [
                    {"source_text": "Grant"},
                    {"source_text": "Credit"},
                ],
            },
            "analysis_methods": ["Authors' calculation"],
            "data_collection_methods": [{"source_text": "Administrative records"}],
        }
    )

    assert record.variables[0].currency.code == "USD"
    assert (
        record.dimensions[0].category_groups[0].categories[1].source_text
        == "Abductions"
    )
    assert record.geographic_coverage.scope.country_code == "NE"
    assert record.financing.instruments[0].source_text == "Grant"


def test_open_terms_do_not_weaken_normalized_vocabularies() -> None:
    """Unknown terms remain source-only while normalized values stay closed."""
    term = StatisticalFormTerm(source_text="Winsorized mean")
    assert term.normalized_value is None
    with pytest.raises(ValidationError, match="Input should be"):
        StatisticalFormTerm(
            source_text="Winsorized mean", normalized_value="winsorized_mean"
        )
    with pytest.raises(ValidationError, match="Input should be"):
        Variable(name="GDP", analytical_roles=["response-ish"])


def test_plain_semantic_fields_accept_inferred_values_directly() -> None:
    """Store semantic values directly when no normalization vocabulary exists."""
    record = DataSnapshotMetadata.model_validate(
        {
            "subject_domains": ["Agriculture"],
            "population_group": "K-12 students",
            "intervention_types": ["School construction"],
            "financing": {"measures": ["Liquidated budget"]},
            "analysis_methods": ["Regression"],
            "geographic_coverage": {
                "locations": [{"name": "Kenya", "role": "Country of implementation"}]
            },
        }
    )

    assert record.subject_domains == ["Agriculture"]
    assert record.geographic_coverage.locations[0].role == "Country of implementation"
    with pytest.raises(ValidationError):
        DataSnapshotMetadata(subject_domains=[{"source_text": "Agriculture"}])


def test_location_type_is_distinct_from_reporting_level() -> None:
    """Represent a named place kind separately from data reporting level."""
    record = DataSnapshotMetadata.model_validate(
        {
            "geographic_coverage": {
                "locations": [
                    {
                        "name": "Baringo District",
                        "type": {"source_text": "District"},
                    }
                ],
                "level": {"normalized_value": "administrative_area_2"},
            }
        }
    )

    assert record.geographic_coverage.locations[0].type.source_text == "District"
    assert record.geographic_coverage.level.normalized_value.value == (
        "administrative_area_2"
    )
    assert metadata_models.GeographicLocation.model_fields["type"].description == (
        "The physical or administrative type of a named geographic location "
        "represented in the snapshot. This field describes what the location is; "
        "use `geographic_coverage.level` for the administrative or spatial level at "
        "which the snapshot's data are reported."
    )


def test_normalized_terms_expose_only_source_and_closed_value() -> None:
    """Keep normalized vocabularies narrow and reject generic coding properties."""
    for model in [
        StatisticalFormTerm,
        VisualizationTypeTerm,
        TemporalGranularityTerm,
        GeographicLevelTerm,
    ]:
        assert set(model.model_fields) == {"source_text", "normalized_value"}
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            model.model_validate({"source_text": "Visible label", "code": "X"})


def test_variables_support_distinct_axes_on_any_plot_side() -> None:
    """Represent multiple x or y axes, including axes sharing one side."""
    variables = [
        Variable(
            name="Logs",
            axis_assignments=[
                {"dimension": "y", "position": "left", "position_index": 1}
            ],
        ),
        Variable(
            name="Sawnwood",
            axis_assignments=[
                {"dimension": "y", "position": "left", "position_index": 2}
            ],
        ),
        Variable(
            name="Alternate time",
            axis_assignments=[
                {"dimension": "x", "position": "top", "position_index": 1}
            ],
        ),
    ]

    assert variables[1].axis_assignments[0].position_index == 2
    assert variables[2].axis_assignments[0].position.value == "top"
    with pytest.raises(ValidationError, match="x-axis position"):
        AxisAssignment(dimension="x", position="left", position_index=1)


def test_standard_formats_and_cross_field_constraints_are_enforced() -> None:
    """Invalid codes, temporal relationships, and unqualified codes fail."""
    with pytest.raises(ValidationError, match="String should match pattern"):
        DataSnapshotMetadata(
            geographic_coverage={"scope": {"name": "Philippines", "country_code": "ph"}}
        )
    with pytest.raises(ValidationError, match="String should match pattern"):
        Currency(source_text="peso", code="php")
    with pytest.raises(ValidationError, match="String should match pattern"):
        Unit(source_text="kilograms", code="TOOLONG")
    with pytest.raises(ValidationError, match="String should match pattern"):
        Place(name="Africa", m49_code="00X")
    with pytest.raises(ValidationError, match="canonical BCP 47 casing"):
        Language(tag="EN-us")
    with pytest.raises(ValidationError, match="supplied together"):
        CodedTerm(source_text="Mean", code="MEAN")
    with pytest.raises(ValidationError, match="interval requires start and end"):
        TemporalExpression(
            source_text="Since 2020",
            start="2020",
            relation="interval",
            precision="year",
        )
    with pytest.raises(ValidationError, match="day is out of range"):
        TemporalExpression(
            source_text="31 February 2020",
            start="2020-02-31",
            relation="point",
            precision="day",
        )
    with pytest.raises(ValidationError, match="does not match datetime"):
        TemporalExpression(
            source_text="1 January 2020 at noon UTC",
            start="2020-01-01 12:00:00+00:00",
            relation="point",
            precision="datetime",
        )


def test_cardinality_nonrecursive_groups_and_deduplication() -> None:
    """Empty collections fail, group nesting fails, and exact duplicates collapse."""
    with pytest.raises(ValidationError, match="at least 1 item"):
        DataSnapshotMetadata(panel_titles=[])
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Dimension.model_validate(
            {
                "name": "Incident typology",
                "category_groups": [
                    {
                        "name": "Rights violations",
                        "categories": [{"source_text": "Arrest"}],
                        "category_groups": [{"name": "Nested"}],
                    }
                ],
            }
        )
    record = DataSnapshotMetadata(panel_titles=["1999", "1999", "2006"])
    assert record.panel_titles == ["1999", "2006"]


@pytest.mark.parametrize(
    "record",
    [
        {
            "panel_titles": ["1999", "2006"],
            "visualization_types": [{"normalized_value": "choropleth_map"}],
            "geographic_coverage": {
                "scope": {"name": "Vietnam", "country_code": "VN"},
                "level": {
                    "source_text": "Province",
                    "normalized_value": "administrative_area_1",
                },
            },
        },
        {
            "comparisons": ["Men vs Women"],
            "dimensions": [
                {
                    "name": "Gender",
                    "categories": [
                        {"source_text": "Men"},
                        {"source_text": "Women"},
                    ],
                }
            ],
        },
        {
            "geographic_coverage": {
                "scope": {"name": "Southern Africa"},
                "locations": [
                    {
                        "name": "South Sudan",
                        "country_code": "SS",
                        "role": "Country of origin",
                    }
                ],
            }
        },
    ],
)
def test_bounded_snapshot_examples_validate(record: dict[str, object]) -> None:
    """Representative map, comparison, and geographic-role cases validate."""
    assert DataSnapshotMetadata.model_validate(record)


def test_generation_is_deterministic_and_matches_written_files(tmp_path: Path) -> None:
    """JSON and Markdown derive reproducibly from the same Pydantic model."""
    first_json = render_json_schema()
    first_markdown = render_markdown_reference()
    assert first_json == render_json_schema()
    assert first_markdown == render_markdown_reference()
    schema = json.loads(first_json)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["x-schema-version"] == "1.3"
    assert len(schema["properties"]) == 20
    assert schema["properties"]["title"]["x-standards"]
    assert "source_document_title" not in first_json
    assert "<!-- Generated from DataSnapshotMetadata." in first_markdown
    assert "Parameters\n----------" not in first_markdown

    json_path = tmp_path / "schema.json"
    markdown_path = tmp_path / "reference.md"
    write_schema_artifacts(json_path, markdown_path)
    assert json_path.read_text(encoding="utf-8") == first_json
    assert markdown_path.read_text(encoding="utf-8") == first_markdown


def test_serialized_schema_is_cached_for_repeated_use() -> None:
    """Schema serialization is computed once and reused within a process."""
    schema_generation._metadata_schema.cache_clear()
    serialize_metadata_schema.cache_clear()

    first = serialize_metadata_schema()
    second = serialize_metadata_schema()
    render_json_schema()
    render_markdown_reference()

    assert first is second
    assert serialize_metadata_schema.cache_info().misses == 1
    assert serialize_metadata_schema.cache_info().hits == 1
    assert schema_generation._metadata_schema.cache_info().misses == 1
    assert schema_generation._metadata_schema.cache_info().hits == 2
    assert json.loads(first)["x-schema-version"] == "1.3"


@pytest.mark.parametrize(
    "tag",
    [
        "en-a",
        "en-US-US",
        "de-DE-1901-1901",
        "en-a-foo-a-bar",
        "en-Latn-Latn",
        "en-x",
        "en-u-x-foo",
    ],
)
def test_malformed_language_tags_are_rejected(tag: str) -> None:
    """Reject broken grammar and repeated variants or extension singletons.

    Parameters
    ----------
    tag : str
        Malformed language tag.
    """
    with pytest.raises(ValidationError):
        Language(tag=tag)


@pytest.mark.parametrize(
    "tag",
    [
        "en",
        "zh-Hant-TW",
        "de-CH-1901",
        "en-u-ca-gregory",
        "en-a-foo-b-bar",
        "x-private-private",
        "en-x-a-a",
        "i-default",
        "sgn-BE-FR",
    ],
)
def test_valid_language_tag_shapes_are_preserved(tag: str) -> None:
    """Accept ordinary, extended, private-use, and grandfathered tag shapes.

    Parameters
    ----------
    tag : str
        Well-formed tag in the expected casing.
    """
    assert Language(tag=tag).tag == tag


@pytest.mark.parametrize(
    "uri",
    [
        "https://example.org/%ZZ",
        "https://example.org/a\nb",
        "https://example.org/a b",
        " https://example.org",
        "https://example.org/%",
        "https://example.org/[x]",
        "https://example.org/a#b#c",
        "https://example.org/a\\b",
    ],
)
def test_invalid_uri_spelling_is_rejected_before_normalization(uri: str) -> None:
    """Apply the original-input URI guard to both public URI-bearing models.

    Parameters
    ----------
    uri : str
        Invalid URI spelling that must not be silently repaired.
    """
    for model, data in [
        (CodedTerm, {"uri": uri}),
        (Identifier, {"value": "id", "uri": uri}),
    ]:
        with pytest.raises(ValidationError):
            model.model_validate(data)


@pytest.mark.parametrize(
    "uri",
    [
        "https://example.org/a%20b",
        "urn:isbn:9780141036144",
        "https://[2001:db8::1]/a?b=c#d",
        "mailto:person@example.org",
    ],
)
def test_valid_absolute_uris_remain_usable(uri: str) -> None:
    """Retain ordinary absolute identifiers including non-HTTP schemes.

    Parameters
    ----------
    uri : str
        Valid absolute URI.
    """
    assert str(CodedTerm(uri=uri).uri) == uri


@pytest.mark.parametrize("fraction", [".1", ".12", ".123", ".1234", ".1234567", ",123"])
def test_fractional_timestamps_preserve_source_precision(fraction: str) -> None:
    """Accept supported fractions on Python 3.10 without changing their text.

    Parameters
    ----------
    fraction : str
        Fractional-second suffix.
    """
    start = f"2020-01-01T12:00:00{fraction}Z"
    record = TemporalExpression(
        source_text=start, start=start, relation="point", precision="datetime"
    )
    assert record.start == start


def test_fractional_interval_ordering_is_exact_across_offsets() -> None:
    """Compare sub-microsecond fractions and timezone offsets without rounding."""
    values = dict(source_text="interval", relation="interval", precision="datetime")
    TemporalExpression(
        **values,
        start="2020-01-01T08:00:00.12345671+08:00",
        end="2020-01-01T00:00:00.12345672Z",
    )
    with pytest.raises(ValidationError, match="after end"):
        TemporalExpression(
            **values,
            start="2020-01-01T08:00:00.12345672+08:00",
            end="2020-01-01T00:00:00.12345671Z",
        )


@pytest.mark.parametrize(
    "record, valid",
    [
        ({}, True),
        ({"title": None}, True),
        ({"title": "   "}, False),
        ({"project": {}}, False),
        ({"project": {"name": None}}, False),
        ({"project": {"name": "Project"}}, True),
        ({"financing": {"instruments": [{"code": "X"}]}}, False),
        (
            {"financing": {"instruments": [{"code": "X", "scheme": None}]}},
            False,
        ),
        ({"financing": {"instruments": [{"scheme": "local"}]}}, False),
        (
            {"financing": {"instruments": [{"code": "X", "scheme": "local"}]}},
            True,
        ),
        (
            {"financing": {"instruments": [{"source_text": "Grant"}]}},
            True,
        ),
        ({"geographic_coverage": {"scope": {"country_code": "PH"}}}, False),
        ({"languages": [{"source_text": None, "tag": None}]}, False),
        ({"languages": [{"tag": "en-a"}]}, False),
    ],
)
def test_exported_structural_constraints_match_python(
    record: dict[str, object], valid: bool
) -> None:
    """Check exported rules using an independent Draft 2020-12 validator.

    Parameters
    ----------
    record : dict[str, object]
        Metadata record exercising a conditional constraint.
    valid : bool
        Expected acceptance by both validators.
    """
    schema = DataSnapshotMetadata.model_json_schema()
    Draft202012Validator.check_schema(schema)
    assert (
        Draft202012Validator(schema, format_checker=FormatChecker()).is_valid(record)
        is valid
    )
    if valid:
        DataSnapshotMetadata.model_validate(record)
    else:
        with pytest.raises(ValidationError):
            DataSnapshotMetadata.model_validate(record)


def test_exported_temporal_constraints_match_python() -> None:
    """Exercise null, omission, relation, and precision combinations independently."""
    validator = Draft202012Validator(TemporalExpression.model_json_schema())
    assert not validator.is_valid({})
    with pytest.raises(ValidationError, match="source text or a bound"):
        TemporalExpression()
    normalized_only = {
        "start": "2015",
        "end": "2020",
        "relation": "interval",
        "precision": "year",
    }
    assert TemporalExpression.model_validate(normalized_only).source_text is None
    assert validator.is_valid(normalized_only)
    with pytest.raises(ValidationError, match="requires source text or a bound"):
        TemporalExpression()
    assert not validator.is_valid({})
    for relation in [None, "point", "as_of", "interval", "open_interval"]:
        for precision in [None, "year", "day"]:
            for start in [None, "2020"]:
                for end in [None, "2021"]:
                    data = dict(
                        source_text="time",
                        start=start,
                        end=end,
                        relation=relation,
                        precision=precision,
                    )
                    try:
                        TemporalExpression.model_validate(data)
                        valid = True
                    except ValidationError:
                        valid = False
                    assert validator.is_valid(data) is valid, data
                    assert (
                        validator.is_valid(
                            {k: v for k, v in data.items() if v is not None}
                        )
                        is valid
                    ), data


def test_reference_explains_constraints_and_mapping_locations() -> None:
    """Expose schema limits and preserve standards mappings on their actual fields."""
    reference = render_markdown_reference()
    for text in [
        "minItems: 1",
        "Code and scheme must be non-null together",
        "exclude_none=True",
        "calendar dates",
        "not pinned; syntax only",
        "CL_UNIT_MULT",
    ]:
        assert text in reference
    schema = DataSnapshotMetadata.model_json_schema()
    assert "x-standards" not in schema["properties"]["financing"]
    definitions = schema["$defs"]
    assert definitions["Financing"]["properties"]["funders"]["x-standards"] == [
        {"term": "https://schema.org/funder", "relationship": "exact"}
    ]
    for name, field in [
        ("Variable", "statistical_forms"),
        ("Variable", "unit"),
        ("Provenance", "sources"),
        ("Provenance", "attributions"),
    ]:
        assert definitions[name]["properties"][field]["x-standards"]
