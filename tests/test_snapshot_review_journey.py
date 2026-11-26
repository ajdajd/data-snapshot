"""Exercise accepted-model extraction and the independent local review journey."""

import copy
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import fitz
import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from data_snapshot.structured_data_extraction import llm
from data_snapshot.structured_data_extraction.accepted_extraction import (
    accepted_result_model,
    run_accepted_extraction,
)
from data_snapshot.structured_data_extraction.data_review import (
    load_data_review,
    reviewed_export,
    save_data_review,
)
from data_snapshot.structured_data_extraction.model_review import (
    accept_model,
    load_session,
    save_draft,
)
from data_snapshot.structured_data_extraction.working_model import WorkingModel
from data_snapshot.structured_data_extraction.spending import record_spending
from data_snapshot.structured_data_reviewer import examples


@pytest.fixture
def cases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Use real example models with tiny synthetic source files, without local datasets."""
    pack = copy.deepcopy(examples.load_examples())
    image = tmp_path / "source.png"
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 8, 8), False)
    pixmap.clear_with(255)
    image.write_bytes(pixmap.tobytes("png"))
    native = tmp_path / "native.json"
    native.write_text(
        json.dumps(
            {
                "schema_name": "DoclingDocument",
                "texts": [{"text": "Synthetic source for navigation tests"}],
                "tables": [],
                "pictures": [],
            }
        )
    )
    digest = hashlib.sha256(image.read_bytes()).hexdigest()
    (tmp_path / "run.json").write_text(
        json.dumps({"image_sha256": digest, "status": "extracted_only"})
    )
    for case in pack.values():
        case.update(
            image_path=str(image),
            image_sha256=digest,
            docling=str(native),
            proposal_dir=None,
        )
    monkeypatch.setattr(examples, "load_examples", lambda: copy.deepcopy(pack))
    monkeypatch.setattr(llm, "_DEFAULT_LEDGER", tmp_path / "spend.jsonl")
    for event in ("reserve", "settle"):
        record_spending(
            tmp_path / "spend.jsonl", "fixture", "fixture", "synthetic", "0", event
        )
    monkeypatch.setattr(
        llm,
        "quote_request",
        lambda *args: {"allowance_usd": "0.10", "provider_max_price": {}},
    )
    return pack


def _client(
    payload: dict, callback: Callable[[], None] | None = None
) -> SimpleNamespace:
    calls = []

    def create(**kwargs: object) -> SimpleNamespace:
        calls.append(kwargs)
        if callback:
            callback()
        return SimpleNamespace(
            output_text=json.dumps(payload),
            model_dump=lambda **_: {
                "id": "synthetic_no_network",
                "status": "completed",
                "usage": {"input_tokens": 100, "output_tokens": 200, "cost": 0.001},
            },
        )

    return SimpleNamespace(responses=SimpleNamespace(create=create), calls=calls)


def _session(case: dict, tmp_path: Path) -> Path:
    directory = examples.open_example(case, tmp_path / "sessions")
    accept_model(directory, 1, "Test reviewer")
    return directory


@pytest.mark.parametrize("case_id", ["income", "financing", "education"])
def test_output_schema_and_example_values(cases: dict, case_id: str) -> None:
    """Require strict objects throughout the response schema and retain missing/zero."""
    case = cases[case_id]
    validator = accepted_result_model(WorkingModel.model_validate(case["model"]))
    schema = validator.model_json_schema()
    Draft202012Validator.check_schema(schema)

    def visit(value: object) -> None:
        if isinstance(value, dict):
            if value.get("type") == "object":
                assert value["additionalProperties"] is False
                assert set(value.get("required", [])) == set(value["properties"])
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(schema)
    result = validator.model_validate(case["data"])
    if case_id == "financing":
        assert [r.value for r in result.observations] == [100, 100, 98, 0]
    elif case_id == "education":
        assert len(result.observations) == 28
        assert sum(r.value is None for r in result.observations) == 12


@pytest.mark.parametrize(
    "damage",
    [
        "duplicate",
        "category",
        "text_number",
        "bool",
        "infinite",
        "estimate",
        "missing",
        "bounds",
        "extra",
    ],
)
def test_invalid_values_stop_before_review(cases: dict, damage: str) -> None:
    """Reject ambiguous identities, unsupported estimates, malformed values and bounds."""
    data = copy.deepcopy(cases["income"]["data"])
    row = data["observations"][0]
    if damage == "duplicate":
        data["observations"].append(copy.deepcopy(row))
    elif damage == "category":
        row["dimensions"]["field_table_row"] = "unknown"
    elif damage == "text_number":
        row["value"] = "5930"
    elif damage == "bool":
        row["value"] = True
    elif damage == "infinite":
        row["value"] = float("inf")
    elif damage == "estimate":
        row["evidence"].update(method="estimated", note="Approximate geometry")
    elif damage == "missing":
        row["value"] = None
    elif damage == "bounds":
        row["bounds"] = {"lower": 6, "upper": 5, "evidence": row["evidence"]}
    else:
        row["unexpected"] = 1
    validator = accepted_result_model(
        WorkingModel.model_validate(cases["income"]["model"])
    )
    with pytest.raises(ValidationError):
        validator.model_validate(data)


def test_text_result_and_explicit_estimation(cases: dict) -> None:
    """Support nonnumeric results and evidence-backed estimates only when allowed."""
    model = WorkingModel.model_validate(cases["financing"]["model"])
    model.components[0].results[0].value_type = "text"
    data = copy.deepcopy(cases["financing"]["data"])
    for row in data["observations"]:
        row["value"] = "Yes"
    assert (
        accepted_result_model(model).model_validate(data).observations[0].value == "Yes"
    )
    model.components[0].results[0].value_type = "number"
    model.components[0].extraction_policy = "allow_estimates"
    data = copy.deepcopy(cases["financing"]["data"])
    row = data["observations"][0]
    row["evidence"].update(method="estimated", note="Approximate plotted geometry")
    row["bounds"] = {"lower": 90, "upper": 110, "evidence": row["evidence"]}
    assert (
        accepted_result_model(model).model_validate(data).observations[0].bounds.lower
        == 90
    )


def test_extraction_requires_acceptance_and_offline_preparation_has_no_client(
    cases: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Gate value extraction on acceptance; preparation must never construct a client."""
    import openai

    def forbidden(**kwargs: object) -> None:
        raise AssertionError("Unexpected real client")

    monkeypatch.setattr(openai, "OpenAI", forbidden)
    directory = examples.open_example(cases["income"], tmp_path / "sessions")
    with pytest.raises(ValueError, match="Accept the current data model"):
        run_accepted_extraction(directory, tmp_path / "blocked")
    accept_model(directory, 1, "Reviewer")
    output = tmp_path / "prepared"
    report = run_accepted_extraction(directory, output)
    assert report["status"] == "prepared" and report["api_attempts"] == 0
    assert (output / "working_model.json").exists()
    assert not (output / "observations.json").exists()


@pytest.mark.parametrize("changed_while_running", [False, True])
def test_fake_billed_extraction_pins_model_and_keeps_costs(
    cases: dict, tmp_path: Path, changed_while_running: bool
) -> None:
    """Retain generated values and synthetic costs even if a newer model makes them stale."""
    directory = _session(cases["income"], tmp_path)

    def revise() -> None:
        model = load_session(directory).revisions[-1].model
        model.title = "Changed while request was running"
        save_draft(directory, model, 1, "Reviewer", "Concurrent revision")

    client = _client(cases["income"]["data"], revise if changed_while_running else None)
    output = tmp_path / "values"
    report = run_accepted_extraction(directory, output, execute=True, client=client)
    assert len(client.calls) == 1
    assert report["spending"]["running_total_usd"] == "0.001"
    assert report["status"] == ("stale" if changed_while_running else "complete")
    assert len(load_data_review(output)["generated"]["observations"]) == 16
    with pytest.raises(ValueError):
        reviewed_export(directory, output)


def test_review_corrections_approval_resume_and_model_invalidation(
    cases: dict, tmp_path: Path
) -> None:
    """Keep generated values immutable, audit approval, and invalidate outdated exports."""
    directory = _session(cases["income"], tmp_path)
    output = examples.load_preloaded_values(directory, cases["income"])
    original = (output / "observations.json").read_bytes()
    data = copy.deepcopy(load_data_review(output)["working"])
    data["observations"][0]["value"] = 5931
    data["observations"][0]["evidence"]["note"] = "Synthetic review correction"
    save_data_review(directory, output, data, 0, "Draft author")
    with pytest.raises(ValueError, match="Review data"):
        reviewed_export(directory, output)
    approved = save_data_review(directory, output, data, 1, "Approver", reviewed=True)
    assert approved["review"]["reviewed_by"] == "Approver"
    assert approved["review"]["reviewed_at"]
    assert (
        reviewed_export(directory, output)["data"]["observations"][0]["value"] == 5931
    )
    assert (output / "observations.json").read_bytes() == original
    with pytest.raises(ValueError, match="reload"):
        save_data_review(directory, output, data, 0, "Stale editor")
    data["observations"][0]["value"] = 5930
    revised = save_data_review(directory, output, data, 1, "Reviewer")
    assert revised["review"]["reviewed_revision"] is None
    assert revised["review"]["reviewed_by"] is None
    save_data_review(directory, output, data, 2, "Reviewer", reviewed=True)
    model = load_session(directory).revisions[-1].model
    model.title = "New interpretation"
    save_draft(directory, model, 1, "Reviewer", "Model revision")
    accept_model(directory, 2, "Reviewer")
    with pytest.raises(ValueError, match="current accepted data model"):
        reviewed_export(directory, output)
    with pytest.raises(ValueError, match="Data model changed"):
        save_data_review(directory, output, data, 2, "Reviewer", reviewed=True)


def test_changed_generated_values_are_not_silently_reviewed(
    cases: dict, tmp_path: Path
) -> None:
    """Catch alterations to either original results or saved correction history."""
    directory = _session(cases["income"], tmp_path)
    output = examples.load_preloaded_values(directory, cases["income"])
    data = load_data_review(output)["working"]
    save_data_review(directory, output, data, 0, "Reviewer")
    data["observations"][0]["value"] = 123
    (output / "observations.json").write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Generated data changed"):
        load_data_review(output)


def test_upload_uses_offline_docling_and_retains_failure_logs(
    cases: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Validate PNGs before subprocess work and retain useful preprocessing failures."""
    calls = []

    def failed(command: list, **kwargs: object) -> SimpleNamespace:
        calls.append((command, kwargs))
        return SimpleNamespace(
            returncode=1, stdout="Local conversion started", stderr="Synthetic failure"
        )

    monkeypatch.setattr(examples.subprocess, "run", failed)
    with pytest.raises(ValueError, match="upload a PNG"):
        examples.preprocess_upload(b"not a PNG", tmp_path / "workspace")
    assert not calls
    with pytest.raises(ValueError, match="preprocessing failed"):
        examples.preprocess_upload(
            Path(cases["income"]["image_path"]).read_bytes(), tmp_path / "workspace"
        )
    command, options = calls[0]
    assert command[command.index("--pipeline") + 1] == "standard"
    assert command[command.index("--device") + 1] == "cpu"
    assert options["env"]["HF_HUB_OFFLINE"] == "1"
    log = next((tmp_path / "workspace").rglob("docling.log"))
    assert "Synthetic failure" in log.read_text()


@pytest.fixture
def app(cases: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Run the app in a temporary workspace and forbid genuine model calls."""
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    from data_snapshot.structured_data_extraction import (
        accepted_extraction,
        model_proposal,
    )

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Unexpected paid model action")

    monkeypatch.setattr(accepted_extraction, "run_accepted_extraction", forbidden)
    monkeypatch.setattr(model_proposal, "run_model_proposal", forbidden)
    monkeypatch.setenv("DATA_SNAPSHOT_REVIEW_WORKSPACE", str(tmp_path / "workspace"))
    monkeypatch.setattr(sys, "argv", ["app.py"])
    script = Path(examples.__file__).with_name("app.py")
    instance = AppTest.from_file(str(script), default_timeout=20).run()
    # The data cache is process-wide; each test must get its own source fixtures.
    import streamlit as st

    st.cache_data.clear()
    instance.run()
    assert not instance.exception
    return instance


def _select_label(app, label: str, value: object) -> None:
    next(w for w in app.selectbox if w.label == label).select(value).run()
    assert not app.exception


def test_income_model_scope_edit_to_reviewed_download(app) -> None:
    """Complete the motivating scope correction using readable controls, without JSON."""
    assert [
        option.content for option in app.segmented_control(key="stage").proto.options
    ] == ["Input", "Data Model", "Data", "Export"]
    app.button(key="open_example").click().run()
    assert app.button(key="save_model").label == "Save data model draft"
    assert app.button(key="accept_model").label == "Accept data model"
    assert "Original example review notes" not in [item.label for item in app.expander]
    _select_label(app, "Edit data model", "Units, time and qualifications")
    _select_label(app, "Data model detail", "context_age_sex_qualification")
    next(
        w for w in app.checkbox if w.label.startswith("All ") and "values" in w.label
    ).uncheck().run()
    selected = next(w for w in app.multiselect if w.label.startswith("Choose "))
    selected.set_value([v for v in selected.value if v != "cat_remittances"]).run()
    assert not app.exception
    assert app.button(key="accept_model").disabled
    app.button(key="save_model").click().run()
    assert not app.exception
    directory = Path(app.session_state["active_session"])
    context = next(
        c
        for c in load_session(directory).revisions[-1].model.contexts
        if c.id == "context_age_sex_qualification"
    )
    assert "cat_remittances" not in context.applies_to[0].where[0].category_ids
    app.button(key="accept_model").click().run()
    assert app.button(key="extract_live").label == "Extract values with LLM"
    assert app.button(key="extract_live").disabled
    app.button(key="load_preloaded").click().run()
    assert not app.exception and len(app.dataframe[0].value) == 8
    app.button(key="approve_data").click().run()
    assert not app.exception and len(app.get("download_button")) == 1
    assert not app.error
    assert load_session(directory).accepted_revision == 2


@pytest.mark.parametrize("case_id", ["financing", "education"])
def test_multiple_components_and_resume(app, case_id: str) -> None:
    """Exercise the other example shapes and recover accepted decisions after reopening."""
    app.selectbox(key="example_choice").select(case_id).run()
    app.button(key="open_example").click().run()
    assert not app.exception
    app.button(key="accept_model").click().run()
    app.button(key="load_preloaded").click().run()
    assert not app.exception
    if case_id == "financing":
        assert app.dataframe[0].value["Value"].tolist() == [100, 100, 98, 0]
    else:
        _select_label(app, "Data component", "c2")
        assert app.dataframe[0].value["Value"].tolist() == [4, 17, 18, 22, 27, 40]
    app.button(key="approve_data").click().run()
    assert not app.exception and app.get("download_button")
    app.session_state["stage"] = "Input"
    app.run()
    app.button(key="resume_session").click().run()
    assert not app.exception
    app.session_state["stage"] = "Export"
    app.run()
    assert not app.exception and app.get("download_button")


def test_unsaved_model_changes_block_export_and_paid_reruns(app) -> None:
    """Navigating or rerunning never triggers the assistant or exports unsaved edits."""
    app.button(key="open_example").click().run()
    app.button(key="accept_model").click().run()
    app.button(key="load_preloaded").click().run()
    app.button(key="approve_data").click().run()
    app.session_state["stage"] = "Model"
    app.run()
    next(w for w in app.text_input if w.label == "Snapshot title").set_value(
        "Unsaved title"
    ).run()
    app.session_state["stage"] = "Export"
    app.run()
    assert not app.exception and not app.get("download_button")
    assert any("unsaved" in w.value for w in app.warning)
    app.run()
    assert not app.exception


def test_grid_correction_save_and_discard(app) -> None:
    """Carry a native grid edit through validation, saved review, and discarded changes."""
    app.button(key="open_example").click().run()
    app.button(key="accept_model").click().run()
    app.button(key="load_preloaded").click().run()
    grid = next(k for k in app.session_state.filtered_state if ":grid:" in k)
    # AppTest has no grid-cell setter; inject the native editor's pending delta.
    app.session_state[grid] = {
        "edited_rows": {0: {"Value": 5931.0, "Review note": "Synthetic correction"}},
        "added_rows": [],
        "deleted_rows": [],
    }
    app.run()
    assert not app.exception and any("Unsaved data" in w.value for w in app.warning)
    app.button(key="save_data").click().run()
    directory = Path(app.session_state["active_session"])
    extraction = next((directory / "extractions").iterdir())
    assert load_data_review(extraction)["working"]["observations"][0]["value"] == 5931
    assert load_data_review(extraction)["generated"]["observations"][0]["value"] == 5930
    grid = next(
        k for k in app.session_state.filtered_state if ":grid:" in k and ":1:grid:" in k
    )
    app.session_state[grid] = {
        "edited_rows": {0: {"Value": 999.0}},
        "added_rows": [],
        "deleted_rows": [],
    }
    app.run()
    app.button(key="discard_data").click().run()
    assert not app.exception and not app.warning
    app.button(key="approve_data").click().run()
    assert not app.exception and app.get("download_button")


def test_duplicate_display_labels_preserve_original_categories(app) -> None:
    """A harmless display rename must never silently reassign an observation's key."""
    app.button(key="open_example").click().run()
    directory = Path(app.session_state["active_session"])
    model = load_session(directory).revisions[-1].model
    categories = model.components[0].fields[0].categories
    categories[0].display_label = categories[1].display_label = "Same name"
    save_draft(directory, model, 1, "Reviewer", "Display names may overlap")
    app.run()
    app.button(key="accept_model").click().run()
    app.button(key="load_preloaded").click().run()
    assert not app.exception
    assert app.dataframe[0].value["field_table_row"].tolist()[:2] == [
        "Same name (1)",
        "Same name (2)",
    ]
    assert not app.warning
    app.button(key="approve_data").click().run()
    assert not app.exception and app.get("download_button")


def test_assistant_requests_only_on_explicit_click_and_no_duplicate_rerun(
    app, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulate a failed paid action without an actual API request or automatic retry."""
    from data_snapshot.structured_data_extraction import model_proposal

    calls = []

    def fake(*args: object, **kwargs: object) -> dict:
        calls.append(kwargs)
        return {"status": "failed", "error": "Synthetic API failure"}

    monkeypatch.setattr(model_proposal, "run_model_proposal", fake)
    app.button(key="open_example").click().run()
    app.checkbox(key="enable_live").check().run()
    next(
        w
        for w in app.text_area
        if w.label == "How should the LLM revise the data model?"
    ).set_value("Scope the population note to labor income").run()
    assert not calls
    app.button(key="request_proposal").click().run()
    assert len(calls) == 1 and calls[0]["execute"] is True
    app.run()
    app.button(key="request_proposal").click().run()
    assert not app.exception and len(calls) == 1
