"""Check evidence-preserving mapping and official SDMX schema validation."""

import copy
import json
from pathlib import Path

import pytest

from data_snapshot.structured_data_extraction.model import (
    Profile,
    map_table,
    sdmx_messages,
)


@pytest.fixture
def profile() -> Profile:
    """Return the independently reviewed income-table interpretation."""
    path = (
        Path(__file__).parents[1]
        / "src/data_snapshot/structured_data_extraction/profiles/income.json"
    )
    return Profile.model_validate_json(path.read_text())


@pytest.fixture
def native() -> dict:
    """Represent manually transcribed image values in Docling's native cell shape."""
    rows = [
        ["", "MEAN", "MEDIAN"],
        ["Agriculture", "5930", "4800"],
        ["Manufacturing", "7496", "7000"],
        ["Construction", "6516", "5600"],
        ["Services", "9927", "8000"],
        ["Public sector", "14368", "12000"],
        ["Health and Education", "9402", "7000"],
        ["Remittances", "8581", "5833"],
        ["Total (excl. remittances)", "8529", "7000"],
    ]
    return {
        "tables": [
            {
                "data": {
                    "num_rows": len(rows),
                    "num_cols": 3,
                    "table_cells": [
                        {
                            "text": text,
                            "start_row_offset_idx": row,
                            "start_col_offset_idx": column,
                            "row_span": 1,
                            "col_span": 1,
                        }
                        for row, values in enumerate(rows)
                        for column, text in enumerate(values)
                    ],
                }
            }
        ]
    }


def test_income_long_observations_and_sdmx(native: dict, profile: Profile) -> None:
    """Preserve 16 observations and resolve SDMX indexes back to their labels."""
    original = copy.deepcopy(native)
    dataset = map_table(native, profile, Path("income.png"))
    structure, data = sdmx_messages(dataset)
    assert native == original
    assert len(dataset.observations) == 16
    assert dataset.observations[0].value == 5930
    assert dataset.observations[0].cell_ref == "#/tables/0/data/table_cells/4"
    dims = data["data"]["structures"][0]["dimensions"]["observation"]
    restored = {
        tuple(
            dims[i]["values"][int(v)]["value"] for i, v in enumerate(key.split(":"))
        ): values[0]
        for key, values in data["data"]["dataSets"][0]["observations"].items()
    }
    assert restored == {o.key: o.value for o in dataset.observations}
    assert restored["Manufacturing", "Median"] == 7000
    assert structure["data"]["dataStructures"][0]["id"] == profile.id
    assert "TIME_PERIOD" not in json.dumps(structure)


@pytest.mark.parametrize("text", ["1.2.3", "9%", "1,23", "NaN", "2***", "(0.1)"])
def test_ambiguous_values_rejected(native: dict, profile: Profile, text: str) -> None:
    """Require explicit review for units, significance marks and ambiguous numbers."""
    native["tables"][0]["data"]["table_cells"][4]["text"] = text
    with pytest.raises(ValueError, match="Ambiguous number"):
        map_table(native, profile, Path("income.png"))


def test_missing_and_zero_are_distinct(native: dict, profile: Profile) -> None:
    """Keep reported zero distinct from an explicitly empty extracted cell."""
    cells = native["tables"][0]["data"]["table_cells"]
    cells[4]["text"], cells[5]["text"] = "0", ""
    observations = map_table(native, profile, Path("income.png")).observations
    assert observations[0].value == 0
    assert observations[1].value is None


@pytest.mark.parametrize("damage", ["duplicate", "merged", "missing", "header"])
def test_structure_requires_review(native: dict, profile: Profile, damage: str) -> None:
    """Reject structures which cannot be mapped faithfully by this prototype."""
    table = native["tables"][0]["data"]
    cells = table["table_cells"]
    if damage == "duplicate":
        cells[6]["text"] = "Agriculture"
    elif damage == "merged":
        cells[4]["col_span"] = 2
    elif damage == "missing":
        cells.pop(4)
    else:
        cells[1]["text"] = "SE"
    with pytest.raises(ValueError):
        map_table(native, profile, Path("income.png"))


@pytest.mark.parametrize("valid", [True, False])
@pytest.mark.parametrize("pipeline,device", [("standard", "cuda:0"), ("chart", "cpu")])
def test_cli_retains_native_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    native: dict,
    profile: Profile,
    valid: bool,
    pipeline: str,
    device: str,
) -> None:
    """Preserve extraction on mapping failure and refuse to overwrite a run."""
    import sys
    from PIL import Image
    from data_snapshot.structured_data_extraction import __main__ as cli

    image = tmp_path / "income.png"
    Image.new("RGB", (10, 10)).save(image)
    mapping = tmp_path / "profile.json"
    mapping.write_text(profile.model_dump_json())
    output = tmp_path / "outputs"
    if not valid:
        native["tables"][0]["data"]["table_cells"][4]["text"] = "5930***"
    calls = []

    def extract(*args: object, **kwargs: object) -> dict:
        calls.append(kwargs)
        return native

    monkeypatch.setattr(cli, "extract_image", extract)
    monkeypatch.setattr(cli, "version", lambda _: "fake-runtime")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "extract",
            str(image),
            "--output-dir",
            str(output),
            "--profile",
            str(mapping),
            "--device",
            device,
            "--pipeline",
            pipeline,
        ],
    )
    if valid:
        cli.main()
        assert (output / "income/data.sdmx.json").exists()
    else:
        with pytest.raises(SystemExit):
            cli.main()
        assert not (output / "income/data.sdmx.json").exists()
    assert json.loads((output / "income/native.json").read_text()) == native
    assert calls == [{"pipeline": pipeline, "device": device}]
    report = json.loads((output / "income/run.json").read_text())
    if not valid:
        assert "Ambiguous number" in report["traceback"]
    assert report["chart_preset"] == (
        "granite_vision_v3_3" if pipeline == "chart" else None
    )
    assert report["chart_image_scale"] == (0.5 if pipeline == "chart" else None)
    assert image.exists()
    with pytest.raises(FileExistsError):
        cli.main()


def test_interruption_is_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep a cancelled inference distinguishable from a completed extraction."""
    import sys
    from PIL import Image
    from data_snapshot.structured_data_extraction import __main__ as cli

    image = tmp_path / "income.png"
    Image.new("RGB", (10, 10)).save(image)
    output = tmp_path / "output"

    def interrupt(*args: object, **kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "extract_image", interrupt)
    monkeypatch.setattr(cli, "version", lambda _: "fake-runtime")
    monkeypatch.setattr(
        sys, "argv", ["extract", str(image), "--output-dir", str(output)]
    )
    with pytest.raises(KeyboardInterrupt):
        cli.main()
    report = json.loads((output / "income/run.json").read_text())
    assert report["status"] == "interrupted"
    assert not (output / "income/data.sdmx.json").exists()


def test_chart_configuration_and_missing_models(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Require local CPU BF16 chart inference and explicit model prefetching."""
    from types import SimpleNamespace

    from docling.datamodel.base_models import ConversionStatus, InputFormat
    from docling.datamodel.settings import settings
    import docling.document_converter as converters

    from data_snapshot.structured_data_extraction.docling import extract_image

    monkeypatch.setattr(settings, "cache_dir", tmp_path)
    artifacts = tmp_path / "models"
    artifacts.mkdir()
    with pytest.raises(FileNotFoundError, match="models download picture_classifier"):
        extract_image(Path("chart.png"), pipeline="chart")
    for folder in (
        "ibm-granite--granite-vision-3.3-2b-chart2csv-preview",
        "docling-project--DocumentFigureClassifier-v2.5",
    ):
        (artifacts / folder).mkdir()
    captured = {}

    def converter(**kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace(
            convert=lambda _: SimpleNamespace(
                status=ConversionStatus.SUCCESS,
                document=SimpleNamespace(export_to_dict=lambda: {"pictures": []}),
            )
        )

    monkeypatch.setattr(converters, "DocumentConverter", converter)
    assert extract_image(Path("chart.png"), pipeline="chart") == {"pictures": []}
    options = captured["format_options"][InputFormat.IMAGE].pipeline_options
    chart = options.chart_extraction_options
    assert options.do_chart_extraction and options.generate_picture_images
    assert options.images_scale == 0.5
    assert not options.enable_remote_services
    assert chart.chart2csv and not chart.chart2summary and not chart.chart2code
    assert chart.engine_options.device.value == "cpu"
    assert chart.engine_options.torch_dtype == "bfloat16"
    assert not chart.engine_options.load_in_8bit
    assert not chart.engine_options.compile_model
    assert chart.model_spec.max_new_tokens == 2048
    import torch

    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    with pytest.raises(RuntimeError, match="CUDA is unavailable"):
        extract_image(Path("chart.png"), pipeline="chart", device="cuda:0")


def test_chart_offload_preloads_functional_attention_weights(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise offload hooks on attention that reads its child weights directly."""
    from types import SimpleNamespace

    import torch
    import docling.document_converter as converters
    from docling.datamodel.base_models import ConversionStatus
    from docling.datamodel.settings import settings
    from docling.models.inference_engines.vlm.transformers_engine import (
        TransformersVlmEngine,
    )
    from docling.models.stages.chart_extraction.granite_vision import (
        ChartExtractionVlmEngineModel,
    )
    from data_snapshot.structured_data_extraction import docling as adapter

    monkeypatch.setattr(settings, "cache_dir", tmp_path)
    for folder in (
        "ibm-granite--granite-vision-3.3-2b-chart2csv-preview",
        "docling-project--DocumentFigureClassifier-v2.5",
    ):
        (tmp_path / "models" / folder).mkdir(parents=True)
    attention = torch.nn.MultiheadAttention(4, 1, batch_first=True).eval()
    multimodal = torch.nn.Module()
    multimodal.register_parameter("image_newline", torch.nn.Parameter(torch.ones(4)))
    multimodal.add_module("attention", attention)
    model = SimpleNamespace(model=multimodal, lm_head=torch.nn.Identity())
    sample = torch.ones(1, 2, 4)
    with torch.no_grad():
        expected = attention(sample, sample, sample)[0] + multimodal.image_newline
    engine = object.__new__(TransformersVlmEngine)
    engine.vlm_model = model
    engine.device = "cpu"
    stage = object.__new__(ChartExtractionVlmEngineModel)
    stage.engine = engine
    offload = adapter._offload_chart_model

    def configure_offload(model: object, device: str) -> None:
        assert device == "cuda:0"
        offload(model, "cpu")

    def convert(_: Path) -> SimpleNamespace:
        for _ in range(2):
            with torch.no_grad():
                actual = attention(sample, sample, sample)[0] + multimodal.image_newline
            torch.testing.assert_close(actual, expected)
        assert multimodal.image_newline.device.type == "cpu"
        return SimpleNamespace(
            status=ConversionStatus.SUCCESS,
            document=SimpleNamespace(export_to_dict=lambda: {"pictures": []}),
        )

    converter = SimpleNamespace(
        initialize_pipeline=lambda _: None,
        initialized_pipelines={"chart": SimpleNamespace(enrichment_pipe=[stage])},
        convert=convert,
    )
    monkeypatch.setattr(converters, "DocumentConverter", lambda **_: converter)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(adapter, "_offload_chart_model", configure_offload)
    assert adapter.extract_image(
        Path("chart.png"), pipeline="chart", device="cuda:0"
    ) == {"pictures": []}
    assert engine.device == "cuda:0"
