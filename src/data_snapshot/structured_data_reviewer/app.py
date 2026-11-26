"""Local snapshot-review journey; run with streamlit run and the review extra."""

import argparse
import copy
import hashlib
import json
import math
import os
import uuid
from pathlib import Path
from typing import Any

import streamlit as st
from pydantic import ValidationError

from data_snapshot.structured_data_extraction.accepted_extraction import (
    accepted_result_model,
    current_model_matches,
    run_accepted_extraction,
)
from data_snapshot.structured_data_extraction.data_review import (
    load_data_review,
    reviewed_export,
    save_data_review,
)
from data_snapshot.structured_data_extraction.llm import _DEFAULT_LEDGER, _write_json
from data_snapshot.structured_data_extraction.model_proposal import run_model_proposal
from data_snapshot.structured_data_extraction.model_review import (
    accept_model,
    apply_proposal,
    load_session,
    save_draft,
)
from data_snapshot.structured_data_extraction.working_model import (
    WorkingModel,
    model_digest,
)
from data_snapshot.structured_data_reviewer.examples import (
    REPO,
    load_examples,
    load_preloaded_values,
    open_example,
    preprocess_upload,
)
from data_snapshot.structured_data_reviewer.model_forms import edit_model
from data_snapshot.structured_data_reviewer.session_names import (
    session_name,
    save_session_name,
)


@st.cache_data(max_entries=1)
def _examples() -> dict[str, dict[str, Any]]:
    return load_examples()


def _money() -> dict[str, Any]:
    import fcntl

    with _DEFAULT_LEDGER.open() as file:
        fcntl.flock(file, fcntl.LOCK_SH)
        rows = [json.loads(line) for line in file if line.strip()]
    if not rows:
        raise ValueError("The existing spending journal must not be reset")
    return rows[-1]


def _error(error: Exception) -> None:
    if isinstance(error, ValidationError):
        for item in error.errors()[:5]:
            st.error(f"{' → '.join(map(str,item['loc']))}: {item['msg']}")
    else:
        st.error(str(error))


def _rename_session(directory: Path, key: str) -> None:
    try:
        st.session_state[key] = save_session_name(directory, st.session_state[key])
    except (ValueError, OSError) as error:
        st.session_state[key] = session_name(directory)
        _error(error)


def _reload_editor(directory: Path) -> None:
    for key in list(st.session_state):
        if key.startswith("edit:"):
            del st.session_state[key]
    st.session_state.get("working_models", {}).pop(str(directory), None)


def _working(directory: Path) -> tuple[Any, dict[str, Any], str]:
    session = load_session(directory)
    current = len(session.revisions)
    saved = session.revisions[-1].model.model_dump(mode="json")
    models = st.session_state["working_models"]
    entry = models.get(str(directory))
    if entry is None or entry["revision"] != current:
        models[str(directory)] = {"revision": current, "model": saved}
    return (
        session,
        models[str(directory)]["model"],
        f"edit:{hashlib.sha256(str(directory).encode()).hexdigest()[:12]}:{current}",
    )


def _dirty(directory: Path) -> bool:
    session = load_session(directory)
    entry = st.session_state["working_models"].get(str(directory))
    return bool(
        entry
        and session.revisions
        and entry["model"] != session.revisions[-1].model.model_dump(mode="json")
    )


def _live_allowed() -> bool:
    if not st.session_state["enable_live"]:
        return False
    try:
        money = _money()
    except (ValueError, OSError):
        return False
    return (
        bool(st.session_state["enable_live"])
        and float(money["reserved_usd"]) == 0
        and float(money["remaining_usd"]) > 0
    )


def _data_dirty(directory: Path) -> bool:
    for prefix, data in st.session_state["working_data"].items():
        if prefix.startswith("data:" + str(directory) + "/"):
            source = Path(prefix[5:].rsplit(":", 1)[0])
            if data != load_data_review(source)["working"]:
                return True
    return False


def _input(workspace: Path) -> None:
    examples = _examples()
    st.subheader("Upload")
    upload = st.file_uploader("Upload one PNG", type=["png"], key="png_upload")
    use_docling = st.checkbox("Preprocess with Docling", value=False, key="use_docling")
    if (
        st.button(
            "Generate Data Model",
            disabled=upload is None or not _live_allowed(),
            key="preprocess_upload",
            type="primary",
        )
        and _live_allowed()
    ):
        active = st.session_state.get("active_session")
        if active and (_dirty(Path(active)) or _data_dirty(Path(active))):
            st.error("Save or discard the current data model draft first.")
        else:
            try:
                with st.spinner("Generating the data model…"):
                    directory = preprocess_upload(
                        upload.getvalue(), workspace, use_docling
                    )
                    proposal = directory / "proposals" / uuid.uuid4().hex
                    report = run_model_proposal(
                        directory / "input.png",
                        directory / "native.json" if use_docling else None,
                        proposal,
                        execute=True,
                        batch_id="interactive_model_review",
                    )
                    st.session_state["last_api_report"] = report
                    if report["status"] == "proposed":
                        apply_proposal(
                            directory, proposal, 0, st.session_state["reviewer"]
                        )
                st.session_state.update(
                    active_session=str(directory),
                    active_example=None,
                    next_stage="Model",
                )
                st.rerun()
            except (ValueError, OSError, TimeoutError) as error:
                _error(error)
    if upload is not None and not _live_allowed():
        st.caption("Enable paid LLM actions to generate a data model.")

    existing = (
        sorted(p.parent for p in workspace.rglob("session.json"))
        if workspace.exists()
        else []
    )
    st.subheader("Resume saved work")
    if existing:
        labels = {}
        for path in existing:
            name = session_name(path)
            label, index = name, 2
            while label in labels.values():
                label = f"{name} ({index})"
                index += 1
            labels[path] = label
        selected = st.selectbox(
            "Select session",
            existing,
            format_func=labels.get,
            key="resume_choice",
        )
        if st.button("Resume session", key="resume_session"):
            active = st.session_state.get("active_session")
            if active and (_dirty(Path(active)) or _data_dirty(Path(active))):
                st.error("Save or discard the current draft first.")
            else:
                st.session_state.update(
                    active_session=str(selected),
                    active_example=selected.name if selected.name in examples else None,
                    next_stage="Model",
                )
                st.rerun()
    else:
        st.caption("No saved sessions yet.")

    with st.expander("Open an example"):
        case_id = st.selectbox(
            "Working example",
            list(examples),
            format_func=lambda key: examples[key]["name"],
            key="example_choice",
        )
        case = examples[case_id]
        st.caption(
            case["model_origin"]
            + ". Example values are manually transcribed and labeled separately from live extraction."
        )
        if st.button("Open example", key="open_example"):
            active = st.session_state.get("active_session")
            if active and (_dirty(Path(active)) or _data_dirty(Path(active))):
                st.error(
                    "Save or discard your data model or data draft before opening another snapshot."
                )
            else:
                try:
                    directory = open_example(case, workspace)
                    st.session_state.update(
                        active_session=str(directory),
                        active_example=case_id,
                        next_stage="Model",
                    )
                    st.rerun()
                except (ValueError, OSError, ValidationError) as error:
                    _error(error)


def _proposal(directory: Path, session: Any) -> None:
    current = session.revisions[-1].model if session.revisions else None
    instruction = st.text_area(
        "How should the LLM revise the data model?",
        key="assistant_instruction:" + str(directory),
        placeholder="For example: apply the population note to labor income only.",
    )
    label = "Ask for a data model revision" if current else "Propose a data model"
    st.caption(
        "This sends the image and Docling evidence to the configured LLM and uses the shared research budget. You accept the data model separately."
    )
    if (
        st.button(
            label,
            key="request_proposal",
            disabled=not _live_allowed()
            or (current is not None and not instruction.strip()),
        )
        and _live_allowed()
    ):
        if _dirty(directory) or _data_dirty(directory):
            st.error(
                "Save or discard your data model or data edits before requesting a revision."
            )
        else:
            output = directory / "proposals" / uuid.uuid4().hex
            try:
                # The same pending action is never submitted again on a widget rerun.
                signature = (
                    str(directory),
                    session.revisions[-1].sha256 if current else None,
                    instruction,
                )
                if st.session_state.get("last_proposal_action") == signature:
                    st.info(
                        "That request has already been sent. Inspect its result or change the instruction before another call."
                    )
                else:
                    st.session_state["last_proposal_action"] = signature
                    with st.spinner("Preparing a data model proposal…"):
                        report = run_model_proposal(
                            directory / "input.png",
                            (
                                directory / "native.json"
                                if session.docling_sha256 is not None
                                else None
                            ),
                            output,
                            current_model=current,
                            instruction=instruction.strip() or None,
                            execute=True,
                            batch_id="interactive_model_review",
                        )
                    st.session_state["proposal_output"] = str(output)
                    st.session_state["last_api_report"] = report
                    st.rerun()
            except (ValueError, OSError, ValidationError) as error:
                _error(error)
    proposal_path = st.session_state.get("proposal_output")
    if proposal_path and Path(proposal_path).parent.parent == directory:
        proposal = Path(proposal_path)
        if (proposal / "proposed_model.json").exists():
            candidate = WorkingModel.model_validate_json(
                (proposal / "proposed_model.json").read_text()
            )
            st.markdown("**Suggested data model revision — inspect before applying**")
            for c in candidate.components:
                st.write(f"{c.name}: {c.one_result_means}")
            st.caption(
                f"{len(candidate.contexts)} scoped data model details; {len(candidate.questions)} questions. Applying only creates a draft."
            )
            if st.button(
                "Apply proposed data model revision as draft", key="apply_revision"
            ):
                try:
                    if _dirty(directory) or _data_dirty(directory):
                        raise ValueError(
                            "Save or discard your data model or data edits before applying a revision."
                        )
                    apply_proposal(
                        directory,
                        proposal,
                        len(session.revisions),
                        st.session_state["reviewer"],
                    )
                    _reload_editor(directory)
                    st.session_state.pop("proposal_output", None)
                    st.rerun()
                except (ValueError, OSError, ValidationError) as error:
                    _error(error)


def _model(directory: Path) -> None:
    session = load_session(directory)
    st.subheader("Review the data model")
    if not session.revisions:
        st.info(
            "The snapshot is saved. Ask the LLM to propose a data model, then inspect it before accepting."
        )
        _proposal(directory, session)
        return
    case = _examples().get(st.session_state.get("active_example"))
    if case:
        st.caption(case["model_origin"])
    session, working, prefix = _working(directory)
    for component in working["components"]:
        st.markdown(f"**{component['name']}**")
        st.write(component["one_result_means"])
    with st.expander("Units, time and qualifications at a glance", expanded=True):
        for context in working["contexts"]:
            st.write(
                f"{context['name']}: {context['value'] or ('Unknown' if context['status']=='unresolved' else 'Not applicable')}"
            )
            scopes = []
            for scope in context["applies_to"]:
                component = next(
                    c for c in working["components"] if c["id"] == scope["component_id"]
                )
                selections = []
                for condition in scope["where"]:
                    field = next(
                        f
                        for f in component["fields"]
                        if f["id"] == condition["field_id"]
                    )
                    labels = {
                        c["id"]: c["display_label"] or c["source_label"]
                        for c in field["categories"]
                    }
                    selections.append(
                        field["name"]
                        + ": "
                        + ", ".join(labels[c] for c in condition["category_ids"])
                    )
                scopes.append(
                    component["name"]
                    + " — "
                    + ("; ".join(selections) if selections else "all rows")
                )
            st.caption("Applies to: " + "; ".join(scopes))
    candidate, errors = edit_model(working, prefix)
    st.session_state["working_models"][str(directory)]["model"] = candidate
    checked = None
    try:
        checked = WorkingModel.model_validate(candidate)
    except ValidationError as error:
        _error(error)
    for error in errors:
        st.error(error)
    dirty = candidate != session.revisions[-1].model.model_dump(mode="json")
    if dirty:
        st.warning(
            "Unsaved data model changes. Save the draft, then accept the updated data model. Previous extracted data will need review again."
        )
    elif session.accepted_revision is not None:
        st.success(
            f"Data model revision {session.accepted_revision} accepted. You can review or extract data."
        )
    else:
        st.caption(
            f"Draft revision {len(session.revisions)} is not accepted yet. Unknown information can stay unknown."
        )
    with st.container(horizontal=True):
        if st.button(
            "Save data model draft",
            key="save_model",
            disabled=checked is None or bool(errors),
        ):
            try:
                if _data_dirty(directory):
                    raise ValueError(
                        "Save or discard your data edits before saving a different data model."
                    )
                save_draft(
                    directory,
                    checked,
                    len(session.revisions),
                    st.session_state["reviewer"],
                    "Direct edits in snapshot reviewer",
                )
                _reload_editor(directory)
                st.rerun()
            except (ValueError, OSError, ValidationError) as error:
                _error(error)
        if st.button(
            "Discard unsaved data model changes",
            key="discard_model",
            disabled=not dirty,
        ):
            _reload_editor(directory)
            st.rerun()
        if st.button(
            "Accept data model",
            key="accept_model",
            type="primary",
            disabled=dirty or checked is None or bool(errors),
        ):
            try:
                accept_model(
                    directory, len(session.revisions), st.session_state["reviewer"]
                )
                st.session_state["next_stage"] = "Data"
                st.rerun()
            except (ValueError, OSError, ValidationError) as error:
                _error(error)
    with st.expander("Ask the LLM to revise the data model"):
        _proposal(directory, session)


def _select_extraction(directory: Path) -> Path | None:
    session = load_session(directory)
    case = _examples().get(st.session_state.get("active_example"))
    if (
        case
        and session.accepted_revision is not None
        and session.revisions[0].sha256
        == model_digest(WorkingModel.model_validate(case["model"]))
    ):
        try:
            load_preloaded_values(directory, case)
        except ValidationError:
            # Example fixtures may not fit a structurally revised data model.
            pass
    folders = []
    reports = {}
    for path in sorted(
        (directory / "extractions").glob("*/run.json"),
        key=lambda p: p.stat().st_mtime_ns,
    ):
        report = json.loads(path.read_text())
        if report.get("status") in {
            "complete",
            "partial",
            "unsupported",
            "stale",
            "preloaded",
        }:
            folders.append(path.parent)
            reports[path.parent] = report
    if not folders:
        return None
    widget_key = "data_set:" + str(directory)
    requested = st.session_state.pop("new_extraction", None)
    if requested and Path(requested) in folders:
        st.session_state[widget_key] = Path(requested)
    labels = {
        path: (
            "Preloaded example"
            if reports[path]["status"] == "preloaded"
            else "LLM extraction"
        )
        + f" {index} · data model revision {reports[path]['model_revision']}"
        for index, path in enumerate(folders, 1)
    }
    live = [
        path
        for path in folders
        if reports[path]["status"] != "preloaded"
        and reports[path]["model_revision"] == session.accepted_revision
    ]
    selected = st.selectbox(
        "Saved result set",
        folders,
        index=folders.index(live[-1]) if live else len(folders) - 1,
        format_func=labels.get,
        key=widget_key,
    )
    if selected not in folders:
        raise ValueError("Unknown result set")
    return selected


def _edit_values(state: dict[str, Any], prefix: str) -> dict[str, Any]:
    data = copy.deepcopy(
        st.session_state["working_data"].setdefault(
            prefix, copy.deepcopy(state["working"])
        )
    )
    model = state["model"]
    components = {c.id: c for c in model.components}
    cid = st.selectbox(
        "Data component",
        list(components),
        format_func=lambda key: components[key].name,
        key=prefix + ":component",
    )
    component = components[cid]
    results = {r.id: r for r in component.results}
    rid = st.selectbox(
        "Result to review",
        list(results),
        format_func=lambda key: results[key].name,
        key=prefix + ":result",
    )
    indexes = [
        i
        for i, row in enumerate(data["observations"])
        if row["component_id"] == cid and row["result_id"] == rid
    ]
    records = []
    fields = {f.id: f for f in component.fields}
    choices = {}
    for field in component.fields:
        labels = [c.display_label or c.source_label for c in field.categories]
        duplicates = len(set(labels)) != len(labels)
        choices[field.id] = {
            category.id: f"{label} ({index})" if duplicates else label
            for index, (category, label) in enumerate(zip(field.categories, labels), 1)
        }
    for index in indexes:
        row = data["observations"][index]
        records.append(
            {
                **{
                    field_id: choices[field_id].get(value, value)
                    for field_id, value in row["dimensions"].items()
                },
                "Value": row["value"],
                "Source text": row["evidence"]["raw_text"],
                "Method": row["evidence"]["method"],
                "Location": row["evidence"]["location"],
                "Review note": row["evidence"]["note"],
            }
        )
    columns = {
        f.id: (
            st.column_config.SelectboxColumn(
                f.name, options=list(choices[f.id].values())
            )
            if choices[f.id]
            else st.column_config.TextColumn(f.name)
        )
        for f in component.fields
    }
    columns["Method"] = st.column_config.SelectboxColumn(
        "How obtained", options=["printed", "estimated", "missing"]
    )
    columns["Value"] = (
        st.column_config.NumberColumn("Value")
        if results[rid].value_type == "number"
        else st.column_config.TextColumn("Value")
    )
    if records:
        edited = st.data_editor(
            records,
            key=prefix + ":grid:" + cid + ":" + rid,
            column_config=columns,
            hide_index=True,
            width="stretch",
        )
        for index, record in zip(indexes, edited):
            row = data["observations"][index]
            for field_id in fields:
                reverse = {label: key for key, label in choices[field_id].items()}
                value = record[field_id]
                row["dimensions"][field_id] = (
                    reverse.get(value, value) if value else None
                )
            value = record["Value"]
            row["value"] = (
                None
                if value is None or isinstance(value, float) and math.isnan(value)
                else value
            )
            row["evidence"] = {
                "raw_text": record["Source text"] or None,
                "method": record["Method"],
                "location": record["Location"],
                "note": record["Review note"] or None,
            }
    else:
        st.info("No results for this component/result type. Check omissions below.")
    if data["omissions"]:
        st.markdown("**Unresolved / omitted content**")
        for item in data["omissions"]:
            st.write(f"{item['location']}: {item['reason']}")
    if any(data["observations"][i]["bounds"] for i in indexes):
        with st.expander(
            "Extracted bounds — review alongside the values", expanded=True
        ):
            for index in indexes:
                row = data["observations"][index]
                if row["bounds"]:
                    labels = ", ".join(
                        str(choices[f].get(v, v)) for f, v in row["dimensions"].items()
                    )
                    bounds = row["bounds"]
                    st.write(f"{labels}: {bounds['lower']} to {bounds['upper']}")
                    st.write(
                        bounds["evidence"]["raw_text"] or bounds["evidence"]["note"]
                    )
                    st.caption(
                        bounds["evidence"]["method"]
                        + " · "
                        + bounds["evidence"]["location"]
                    )
            # shortcut: bounds are visible but read-only until the chart-review increment.
            st.caption(
                "Bounds are retained in export. Bounds editing is not available in this prototype."
            )
    st.caption(
        "Source text and method need review alongside values. Original generated values are retained. Editing a number does not prove it matches the image."
    )
    st.session_state["working_data"][prefix] = data
    return data


def _data(directory: Path) -> None:
    st.subheader("Review the extracted values")
    session = load_session(directory)
    if session.accepted_revision is None or _dirty(directory):
        st.info(
            "Save and accept the current data model before extracting or reviewing new data."
        )
        return
    with st.container(horizontal=True):
        if (
            st.button(
                "Extract values with LLM",
                key="extract_live",
                disabled=not _live_allowed(),
            )
            and _live_allowed()
        ):
            signature = (
                str(directory),
                session.accepted_revision,
                session.revisions[-1].sha256,
            )
            if st.session_state.get("last_extraction_action") == signature:
                st.info(
                    "This accepted revision has already been submitted. Its saved result or failure report is retained; no duplicate call was made."
                )
            else:
                st.session_state["last_extraction_action"] = signature
                output = directory / "extractions" / uuid.uuid4().hex
                try:
                    with st.spinner(
                        "Extracting with the LLM against your accepted data model…"
                    ):
                        report = run_accepted_extraction(
                            directory,
                            output,
                            execute=True,
                            batch_id="interactive_value_extraction",
                        )
                    st.session_state["last_api_report"] = report
                    if report["status"] not in {"failed", "stale"}:
                        st.session_state["new_extraction"] = str(output)
                    st.rerun()
                except (ValueError, OSError, ValidationError) as error:
                    _error(error)
    extraction = _select_extraction(directory)
    if extraction is None:
        return
    try:
        state = load_data_review(extraction)
        st.caption(
            "Data origin: " + state["report"].get("data_origin", "Live LLM extraction")
        )
        if not current_model_matches(directory, state["report"]):
            st.warning(
                "These data belong to an older data model. They remain saved, but need extraction/review against the current data model before export."
            )
            return
        review = state["review"]
        prefix = f'data:{extraction}:{len(review["revisions"])}'
        edited = _edit_values(state, prefix)
        dirty = edited != state["working"]
        if dirty:
            st.warning(
                "Unsaved data changes. Save a draft or save the reviewed revision before closing or exporting."
            )
        checked = None
        try:
            checked = (
                accepted_result_model(state["model"])
                .model_validate(edited)
                .model_dump(mode="json")
            )
        except ValidationError as error:
            _error(error)
        with st.container(horizontal=True):
            if st.button("Save data draft", key="save_data", disabled=checked is None):
                save_data_review(
                    directory,
                    extraction,
                    checked,
                    len(review["revisions"]),
                    st.session_state["reviewer"],
                )
                st.session_state["working_data"].pop(prefix, None)
                st.rerun()
            if st.button(
                "Save reviewed data",
                key="approve_data",
                type="primary",
                disabled=checked is None,
            ):
                save_data_review(
                    directory,
                    extraction,
                    checked,
                    len(review["revisions"]),
                    st.session_state["reviewer"],
                    reviewed=True,
                )
                st.session_state["working_data"].pop(prefix, None)
                st.session_state["next_stage"] = "Export"
                st.rerun()
            if st.button(
                "Discard unsaved data changes", key="discard_data", disabled=not dirty
            ):
                st.session_state["working_data"].pop(prefix, None)
                for widget in list(st.session_state):
                    if widget.startswith(prefix + ":grid:"):
                        del st.session_state[widget]
                st.rerun()
        if review["reviewed_revision"] is not None:
            st.success(
                "This data revision has been reviewed. Any stated omissions remain visible."
            )
    except (ValueError, OSError, ValidationError) as error:
        _error(error)


def _export(directory: Path) -> None:
    st.subheader("Save a reviewed result")
    st.write(
        "The export includes the accepted data model, reviewed values, source fingerprints and unresolved content."
    )
    if _dirty(directory) or _data_dirty(directory):
        st.warning("Save/review or discard your unsaved changes before exporting.")
        return
    extraction = _select_extraction(directory)
    if extraction:
        try:
            payload = reviewed_export(directory, extraction)
            st.download_button(
                "Download reviewed JSON",
                json.dumps(payload, ensure_ascii=False, indent=2),
                file_name=session_name(directory) + ".json",
                mime="application/json",
                key="download_reviewed",
            )
            st.caption("Origin: " + payload["data_origin"])
        except (ValueError, OSError, ValidationError) as error:
            _error(error)
    else:
        st.info("Review and save a result set in Data before exporting.")
    st.caption(
        "Formal SDMX structure, code mapping and SDMX-JSON export are pending. This interim JSON is not SDMX-JSON."
    )


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--workspace",
    type=Path,
    default=Path(
        os.getenv(
            "DATA_SNAPSHOT_REVIEW_WORKSPACE",
            str(REPO / "data/structured_data_trials/reviewer_sessions"),
        )
    ),
)
args = parser.parse_args()
st.set_page_config(
    page_title="Data snapshot reviewer",
    page_icon=":material/fact_check:",
    layout="wide",
)
st.session_state.setdefault("active_session", None)
st.session_state.setdefault("active_example", None)
st.session_state.setdefault("working_models", {})
st.session_state.setdefault("working_data", {})
st.session_state.setdefault("stage", "Input")
if "next_stage" in st.session_state:
    st.session_state["stage"] = st.session_state.pop("next_stage")
st.title("Data snapshot reviewer")
named_session = st.session_state.get("active_session")
if named_session:
    name_key = "session_name:" + named_session
    st.session_state.setdefault(name_key, session_name(Path(named_session)))
    st.text_input(
        "Session name",
        key=name_key,
        on_change=_rename_session,
        args=(Path(named_session), name_key),
        persist_state="session",
    )
else:
    st.text_input(
        "Session name", value="Untitled snapshot", disabled=True, key="session_name:new"
    )
with st.sidebar:
    st.text_input("Reviewer name", value="Local reviewer", key="reviewer")
    st.checkbox("Enable paid LLM actions", value=False, key="enable_live")
    try:
        money = _money()
        st.caption(
            f"Recorded spend: ${float(money['running_total_usd']):.4f} / $5 · remaining ${float(money['remaining_usd']):.4f}"
        )
        if float(money["reserved_usd"]):
            st.warning(
                "An API charge is unresolved. New paid actions are disabled pending reconciliation."
            )
    except (ValueError, OSError) as error:
        _error(error)
    last_report = st.session_state.get("last_api_report", {})
    if last_report.get("spending"):
        st.caption(
            "Last LLM action cost: $" + str(last_report["spending"]["call_cost_usd"])
        )
    if last_report.get("status") in {"failed", "stale"}:
        st.warning(
            "Last LLM action: " + last_report.get("error", last_report["status"])
        )
    st.caption("Saved work stays in this local workspace.")
stage = (
    st.segmented_control(
        "Review stage",
        ["Input", "Model", "Data", "Export"],
        format_func=lambda stage: "Data Model" if stage == "Model" else stage,
        key="stage",
        width="stretch",
    )
    or "Input"
)
active = st.session_state.get("active_session")
if stage == "Input":
    _input(args.workspace)
elif active:
    directory = Path(active)
    left, right = st.columns([1, 1.15], gap="large")
    with left:
        with st.container(height=760, border=True):
            st.image(str(directory / "input.png"), width="stretch")
            used_docling = load_session(directory).docling_sha256 is not None
            st.caption("Docling preprocessing: " + ("Yes" if used_docling else "No"))
    with right:
        with st.container(height=760, border=True):
            if stage == "Model":
                _model(directory)
            elif stage == "Data":
                _data(directory)
            else:
                _export(directory)
else:
    st.info("Open a snapshot in Input to begin.")
