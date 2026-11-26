"""Check per-snapshot models, proposal boundaries and local review history offline."""

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import fitz
import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from data_snapshot.structured_data_extraction import llm
from data_snapshot.structured_data_extraction.model_proposal import (
    prepare_model_request,
    run_model_proposal,
)
from data_snapshot.structured_data_extraction.model_review import (
    accept_model,
    apply_proposal,
    create_session,
    load_session,
    save_draft,
)
from data_snapshot.structured_data_extraction.working_model import (
    WorkingModel,
    model_digest,
)

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures/working_models.json").read_text()
)["examples"]


@pytest.fixture
def sources(tmp_path: Path) -> tuple[Path, Path]:
    """Write a PNG and matching native/report pair without loading Docling."""
    image = tmp_path / "country_2099_must_not_be_evidence.png"
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 8, 8), False)
    pixmap.clear_with(255)
    image.write_bytes(pixmap.tobytes("png"))
    native = tmp_path / "native.json"
    native.write_text(
        json.dumps(
            {
                "schema_name": "DoclingDocument",
                "name": image.name,
                "origin": {"filename": image.name},
                "body": {"children": [{"$ref": "#/texts/0"}]},
                "texts": [
                    {
                        "self_ref": "#/texts/0",
                        "text": "A source can contain {{INSTRUCTION}} literally",
                        "prov": [],
                    }
                ],
                "tables": [],
                "pictures": [],
                "pages": {
                    "1": {
                        "size": {"width": 8, "height": 8},
                        "image": {"uri": "data:image/png;base64,SECRET_ASSET"},
                    }
                },
            }
        )
    )
    (tmp_path / "run.json").write_text(
        json.dumps(
            {
                "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                "status": "extracted_only",
            }
        )
    )
    return image, native


@pytest.fixture
def model() -> WorkingModel:
    """Load the two-component income design with unresolved unit/questions."""
    return WorkingModel.model_validate(copy.deepcopy(FIXTURES[0]["model"]))


@pytest.fixture(autouse=True)
def offline_pricing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent pricing requests and isolate every synthetic billed call."""
    monkeypatch.setattr(llm, "_DEFAULT_LEDGER", tmp_path / "spend.jsonl")
    monkeypatch.setattr(
        llm,
        "quote_request",
        lambda *args: {"allowance_usd": "0.10", "provider_max_price": {}},
    )


def fake_client(payload: dict, status: str = "completed") -> SimpleNamespace:
    """Retain the submitted request and return one synthetic billed response."""
    calls = []
    text = json.dumps(payload)
    raw = {
        "id": "offline_model_proposal",
        "status": status,
        "usage": {"input_tokens": 100, "output_tokens": 200, "cost": 0.001},
    }

    def create(**kwargs: object) -> SimpleNamespace:
        calls.append(kwargs)
        return SimpleNamespace(output_text=text, model_dump=lambda **_: raw)

    return SimpleNamespace(responses=SimpleNamespace(create=create), calls=calls)


@pytest.mark.parametrize("example", FIXTURES, ids=[f["id"] for f in FIXTURES])
def test_eight_design_models_are_representable(example: dict) -> None:
    """Exercise distinct component/type/scope requirements without model calls."""
    model = WorkingModel.model_validate(example["model"])
    assert model.components
    assert any(q.resolution == "unresolved" for q in model.questions)
    restored = WorkingModel.model_validate_json(model.model_dump_json())
    assert model_digest(restored) == model_digest(model)


def test_response_schema_requires_every_property_and_rejects_unknown_fields() -> None:
    """Keep the proposal shape usable as strict Structured Outputs."""
    schema = WorkingModel.model_json_schema()
    Draft202012Validator.check_schema(schema)

    def visit(value: object) -> None:
        if isinstance(value, dict):
            if value.get("type") == "object":
                assert value["additionalProperties"] is False
                assert set(value["required"]) == set(value["properties"])
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(schema)


@pytest.mark.parametrize(
    "damage",
    [
        "component",
        "field",
        "category",
        "unit",
        "claim",
        "user_evidence",
        "resolved_question",
        "self_relation",
        "extra",
    ],
)
def test_invalid_models_reject_dangling_context_or_false_states(damage: str) -> None:
    """Reject malformed models before saving a draft or approving a proposal."""
    data = copy.deepcopy(FIXTURES[1]["model"])
    if damage == "component":
        data["contexts"][0]["applies_to"][0]["component_id"] = "missing"
    elif damage == "field":
        data["components"][0]["fields"][0]["id"] = "value"
    elif damage == "category":
        data["contexts"][0]["applies_to"][0]["where"] = [
            {"field_id": "f1", "category_ids": ["missing"]}
        ]
    elif damage == "unit":
        data["contexts"] = [c for c in data["contexts"] if c["kind"] != "unit"]
    elif damage == "claim":
        data["contexts"][0].update(status="unresolved", value="Known dollars")
    elif damage == "user_evidence":
        data["contexts"][0].update(status="user_supplied", value="US dollars")
    elif damage == "resolved_question":
        data["questions"][0].update(resolution="source", answer="A guess")
    elif damage == "self_relation":
        data["relationships"][0]["to_ref"] = data["relationships"][0]["from_ref"]
    else:
        data["accepted"] = True
    with pytest.raises(ValidationError):
        WorkingModel.model_validate(data)


def test_offline_proposal_uses_matched_docling_without_names_or_embedded_assets(
    tmp_path: Path, sources: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prepare image-plus-Docling evidence without loading dotenv or a client."""
    import dotenv
    import openai

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Offline proposal touched client setup")

    monkeypatch.setattr(dotenv, "load_dotenv", forbidden)
    monkeypatch.setattr(openai, "OpenAI", forbidden)
    image, native = sources
    output = tmp_path / "prepared"
    report = run_model_proposal(image, native, output)
    assert report["status"] == "prepared" and report["api_attempts"] == 0
    preview = json.loads((output / "request.preview.json").read_text())
    content = json.dumps(preview)
    assert image.name not in content and "SECRET_ASSET" not in content
    assert "{{INSTRUCTION}}" in content  # Literal source text is never re-templated.
    assert "SNAPSHOT_OBSERVATIONS" not in content
    assert report["docling_sha256"] == hashlib.sha256(native.read_bytes()).hexdigest()
    assert not (output / "proposed_model.json").exists()


def test_image_only_proposal_and_review_session_have_no_docling_sources(
    tmp_path: Path, sources: tuple[Path, Path], model: WorkingModel
) -> None:
    """Support PNG-only proposals, application, acceptance and source validation."""
    image, _ = sources
    output = tmp_path / "image_proposal"
    report = run_model_proposal(
        image,
        None,
        output,
        execute=True,
        client=fake_client(model.model_dump(mode="json")),
    )
    assert report["status"] == "proposed"
    assert report["evidence_mode"] == "image_only" and report["docling_sha256"] is None
    assert json.loads((output / "docling_evidence.json").read_text()) is None
    directory = tmp_path / "session"
    create_session(image, None, directory)
    apply_proposal(directory, output, 0, "Reviewer")
    assert accept_model(directory, 1, "Reviewer").accepted_revision == 1
    assert load_session(directory).source_docling is None
    assert not (directory / "native.json").exists()
    (directory / "native.json").write_text("{}")
    with pytest.raises(ValueError, match="Unexpected Docling source"):
        load_session(directory)


def test_image_only_proposal_rejects_fabricated_docling_evidence(
    tmp_path: Path, sources: tuple[Path, Path], model: WorkingModel
) -> None:
    """Do not accept claims that absent preprocessing supports an interpretation."""
    model.components[0].evidence[0].basis = "docling"
    report = run_model_proposal(
        sources[0],
        None,
        tmp_path / "bad",
        execute=True,
        client=fake_client(model.model_dump(mode="json")),
    )
    assert report["status"] == "failed" and "cannot claim Docling" in report["error"]
    assert report["spending"]["call_cost_usd"] == "0.001"


def test_wrong_source_and_failed_docling_stop_before_api(
    tmp_path: Path, sources: tuple[Path, Path], model: WorkingModel
) -> None:
    """Do not send a nearby image's native output or a failed conversion as evidence."""
    image, native = sources
    client = fake_client(model.model_dump(mode="json"))
    report_path = native.with_name("run.json")
    original = json.loads(report_path.read_text())
    report_path.write_text(json.dumps({**original, "image_sha256": "wrong"}))
    with pytest.raises(ValueError, match="different image"):
        run_model_proposal(
            image, native, tmp_path / "bad_image", execute=True, client=client
        )
    report_path.write_text(json.dumps({**original, "status": "failed"}))
    with pytest.raises(ValueError, match="did not finish"):
        run_model_proposal(
            image, native, tmp_path / "bad_conversion", execute=True, client=client
        )
    assert not client.calls


def test_revision_has_prior_model_and_explicit_instruction(
    sources: tuple[Path, Path], model: WorkingModel
) -> None:
    """Carry current draft content and reviewer text without acceptance metadata."""
    image, native = sources
    config = llm.APISettings.model_validate_json(llm._DEFAULT_CONFIG.read_text())
    with pytest.raises(ValueError, match="requires a reviewer instruction"):
        prepare_model_request(image, native, config, model)
    request, _, _ = prepare_model_request(
        image, native, config, model, "Keep the population note on labor income only."
    )
    user_text = request["input"][1]["content"][0]["text"]
    assert "Keep the population note" in user_text
    assert model.title in user_text
    assert "accepted_revision" not in user_text


def test_proposal_saves_validated_draft_and_cost_without_acceptance(
    tmp_path: Path, sources: tuple[Path, Path], model: WorkingModel
) -> None:
    """Retain the billed proposal while leaving acceptance as a separate local act."""
    image, native = sources
    client = fake_client(model.model_dump(mode="json"))
    output = tmp_path / "proposal"
    report = run_model_proposal(image, native, output, execute=True, client=client)
    assert report["status"] == "proposed" and len(client.calls) == 1
    assert report["spending"]["running_total_usd"] == "0.001"
    assert (output / "raw_output.txt").exists()
    assert (
        WorkingModel.model_validate_json((output / "proposed_model.json").read_text())
        == model
    )
    assert not (output / "session.json").exists()
    assert not list(output.glob("*.sdmx.json"))
    with pytest.raises(FileExistsError):
        run_model_proposal(image, native, output, execute=True, client=client)
    assert len(client.calls) == 1


def test_invalid_billed_proposal_keeps_evidence_without_repair(
    tmp_path: Path, sources: tuple[Path, Path], model: WorkingModel
) -> None:
    """Count invalid output's charge and retain it without accepting or retrying."""
    image, native = sources
    data = model.model_dump(mode="json")
    data["contexts"][0]["applies_to"][0]["component_id"] = "missing"
    client = fake_client(data)
    output = tmp_path / "failed"
    report = run_model_proposal(image, native, output, execute=True, client=client)
    assert report["status"] == "failed" and len(client.calls) == 1
    assert report["spending"]["call_cost_usd"] == "0.001"
    assert (output / "raw_output.txt").exists()
    assert not (output / "proposed_model.json").exists()


def test_direct_edit_acceptance_and_reload_preserve_history(
    tmp_path: Path, sources: tuple[Path, Path], model: WorkingModel
) -> None:
    """Accept unknowns, retain old revisions, and clear current acceptance on change."""
    image, native = sources
    directory = tmp_path / "session"
    create_session(image, native, directory)
    with pytest.raises(ValueError, match="No data model draft"):
        accept_model(directory, 0, "Aj")
    first = save_draft(directory, model, 0, "Aj", "Initial hand-authored design")
    assert len(first.revisions) == 1 and first.accepted_revision is None
    accepted = accept_model(directory, 1, "Aj")
    assert accepted.accepted_revision == 1
    assert accepted.revisions[0].model.questions[0].resolution == "unresolved"
    unchanged = save_draft(directory, model, 1, "Aj", "No edits")
    assert len(unchanged.revisions) == 1 and unchanged.accepted_revision == 1
    changed = WorkingModel.model_validate_json(model.model_dump_json())
    changed.components[0].extraction_policy = "allow_estimates"
    second = save_draft(directory, changed, 1, "Aj", "Explicitly allow estimates")
    assert len(second.revisions) == 2 and second.accepted_revision is None
    assert second.acceptances[0].revision == 1
    assert second.revisions[0].model.components[0].extraction_policy == "printed_only"
    assert load_session(directory) == second
    with pytest.raises(ValueError, match="Draft changed"):
        accept_model(directory, 1, "Aj")
    assert accept_model(directory, 2, "Aj").accepted_revision == 2
    with pytest.raises(FileExistsError):
        create_session(image, native, directory)


def test_apply_proposal_rejects_stale_or_edited_candidates(
    tmp_path: Path, sources: tuple[Path, Path], model: WorkingModel
) -> None:
    """Apply matching proposals as drafts and never overwrite newer human edits."""
    image, native = sources
    directory = tmp_path / "session"
    create_session(image, native, directory)
    output = tmp_path / "proposal"
    run_model_proposal(
        image,
        native,
        output,
        execute=True,
        client=fake_client(model.model_dump(mode="json")),
    )
    state = apply_proposal(directory, output, 0, "Aj")
    assert state.revisions[0].origin == "model" and state.accepted_revision is None
    revised_output = tmp_path / "revision"
    run_model_proposal(
        image,
        native,
        revised_output,
        current_model=model,
        instruction="Revise the title.",
        execute=True,
        client=fake_client(
            {**model.model_dump(mode="json"), "title": "Proposed new title"}
        ),
    )
    edited = WorkingModel.model_validate_json(model.model_dump_json())
    edited.title = "Human edit made while request was running"
    save_draft(directory, edited, 1, "Aj", "Direct edit")
    with pytest.raises(ValueError, match="different draft"):
        apply_proposal(directory, revised_output, 2, "Aj")
    with pytest.raises(ValueError, match="Draft changed"):
        save_draft(directory, model, 1, "Aj", "Old editor view")
    assert load_session(directory).revisions[-1].model.title == edited.title


@pytest.mark.parametrize(
    "damage", ["source", "history", "proposal_source", "proposal_text"]
)
def test_session_and_proposal_identity_checks(
    tmp_path: Path, sources: tuple[Path, Path], model: WorkingModel, damage: str
) -> None:
    """Reject source/history tampering and wrongly attributed proposal imports."""
    image, native = sources
    directory = tmp_path / "session"
    create_session(image, native, directory)
    if damage == "source":
        (directory / "input.png").write_bytes(b"changed source")
        with pytest.raises(ValueError, match="Saved source changed"):
            load_session(directory)
    elif damage == "history":
        save_draft(directory, model, 0, "Aj", "Initial")
        path = directory / "session.json"
        state = json.loads(path.read_text())
        state["revisions"][0]["model"]["title"] = "Changed without a revision"
        path.write_text(json.dumps(state))
        with pytest.raises(ValidationError, match="hash changed"):
            load_session(directory)
    else:
        output = tmp_path / "proposal"
        run_model_proposal(
            image,
            native,
            output,
            execute=True,
            client=fake_client(model.model_dump(mode="json")),
        )
        if damage == "proposal_source":
            path = output / "run.json"
            report = json.loads(path.read_text())
            report["docling_sha256"] = "wrong"
            path.write_text(json.dumps(report))
            message = "source evidence differs"
        else:
            path = output / "proposed_model.json"
            data = json.loads(path.read_text())
            data["title"] = "Edited model file"
            path.write_text(json.dumps(data))
            message = "differs from raw output"
        with pytest.raises(ValueError, match=message):
            apply_proposal(directory, output, 0, "Aj")
        assert not load_session(directory).revisions


def test_scope_edit_preserves_original_labels_and_prior_acceptance(
    tmp_path: Path, sources: tuple[Path, Path], model: WorkingModel
) -> None:
    """Exercise the income note correction that motivated direct model editing."""
    image, native = sources
    directory = tmp_path / "session"
    create_session(image, native, directory)
    population = next(c for c in model.contexts if c.id == "note_c1_2")
    population.applies_to.append(
        population.applies_to[0].model_copy(update={"component_id": "c2"})
    )
    save_draft(
        directory, model, 0, "test-reviewer", "Illustrative over-broad note scope"
    )
    accept_model(directory, 1, "test-reviewer")
    edited = WorkingModel.model_validate_json(model.model_dump_json())
    next(c for c in edited.contexts if c.id == "note_c1_2").applies_to = [
        population.applies_to[0]
    ]
    edited.components[0].fields[0].categories[0].display_label = "Farming"
    state = save_draft(
        directory, edited, 1, "test-reviewer", "Scope note to labor income only"
    )
    assert state.accepted_revision is None and state.acceptances[0].revision == 1
    old_scope = next(
        c for c in state.revisions[0].model.contexts if c.id == "note_c1_2"
    )
    new_scope = next(
        c for c in state.revisions[1].model.contexts if c.id == "note_c1_2"
    )
    assert len(old_scope.applies_to) == 2 and len(new_scope.applies_to) == 1
    assert new_scope.applies_to[0].component_id == "c1"
    assert (
        state.revisions[1].model.components[0].fields[0].categories[0].source_label
        == "Agriculture"
    )


@pytest.mark.parametrize("damage", ["estimates", "user_evidence"])
def test_uninstructed_initial_proposal_cannot_enable_estimates_or_invent_user_context(
    tmp_path: Path, sources: tuple[Path, Path], model: WorkingModel, damage: str
) -> None:
    """Enforce conservative initial defaults before exposing a valid proposal."""
    image, native = sources
    data = model.model_dump(mode="json")
    if damage == "estimates":
        data["components"][0]["extraction_policy"] = "allow_estimates"
    else:
        data["components"][0]["evidence"].append(
            {
                "basis": "user",
                "text": "Made-up clarification",
                "location": "Unprovided reviewer message",
            }
        )
    output = tmp_path / "proposal"
    report = run_model_proposal(
        image, native, output, execute=True, client=fake_client(data)
    )
    assert (
        report["status"] == "failed" and report["spending"]["call_cost_usd"] == "0.001"
    )
    assert not (output / "proposed_model.json").exists()


def test_failed_atomic_save_leaves_previous_draft_and_acceptance_intact(
    tmp_path: Path,
    sources: tuple[Path, Path],
    model: WorkingModel,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Do not lose accepted work if replacing the saved session fails."""
    image, native = sources
    directory = tmp_path / "session"
    create_session(image, native, directory)
    save_draft(directory, model, 0, "test-reviewer", "Initial")
    accept_model(directory, 1, "test-reviewer")
    before = (directory / "session.json").read_bytes()
    original_replace = Path.replace

    def failed_replace(path: Path, target: Path) -> Path:
        if path.name == "session.tmp.json":
            raise OSError("Simulated interrupted save")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", failed_replace)
    model.title = "Unsaved change"
    with pytest.raises(OSError, match="interrupted save"):
        save_draft(directory, model, 1, "test-reviewer", "Must not replace prior data")
    assert (directory / "session.json").read_bytes() == before
    assert load_session(directory).accepted_revision == 1
