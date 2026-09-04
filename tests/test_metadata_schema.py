"""Tests for Data Snapshot Metadata Schema v1.2."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

import data_snapshot.metadata_schema.generation as schema_generation
from data_snapshot.metadata_schema import (
    ControlledTerm,
    Currency,
    DataSnapshotMetadata,
    Dimension,
    Language,
    Place,
    StatisticalFormTerm,
    TemporalExpression,
    Unit,
    Variable,
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


def test_representative_record_preserves_nested_relationships() -> None:
    """A bounded-snapshot record keeps variable and context relationships."""
    record = DataSnapshotMetadata.model_validate(
        {
            "title": "Total project financing",
            "document_label": "Table 3",
            "subject_domains": [
                {
                    "source_text": "Health",
                    "normalized_value": "health",
                }
            ],
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
                            "code": "SUM",
                            "scheme": "SDMX CL_STATISTICAL_OPERATION 1.0",
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
                            "name": "Violation du droit à la liberté",
                            "categories": [
                                {"source_text": "Arrestations arbitraires"},
                                {"source_text": "Enlèvements"},
                            ],
                        }
                    ],
                }
            ],
            "population_group": {"source_text": "Beneficiaries"},
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
                    "code": "A",
                    "scheme": "SDMX CL_FREQ 2.1",
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
            "intervention_types": [{"source_text": "Emergency response"}],
            "financing": {
                "measures": [{"source_text": "Financing gap"}],
                "funders": [{"name": "International Development Association"}],
                "instruments": [
                    {"source_text": "Grant"},
                    {"source_text": "Credit"},
                ],
            },
            "analysis_methods": [{"source_text": "Authors' calculation"}],
            "data_collection_methods": [{"source_text": "Administrative records"}],
        }
    )

    assert record.variables[0].currency.code == "USD"
    assert (
        record.dimensions[0].category_groups[0].categories[1].source_text
        == "Enlèvements"
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
    with pytest.raises(ValidationError, match="requires a scheme"):
        ControlledTerm(source_text="Mean", code="MEAN")
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
                        "role": {"source_text": "Country of origin"},
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
    assert schema["x-schema-version"] == "1.2"
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
    assert json.loads(first)["x-schema-version"] == "1.2"
