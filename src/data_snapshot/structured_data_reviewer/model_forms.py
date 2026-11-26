"""Render plain-language model edits without exposing the internal JSON contract."""

import copy
import json
from typing import Any

import streamlit as st


def _text(label: str, value: str | None, key: str, area: bool = False) -> str:
    st.session_state.setdefault(key, value or "")
    return (st.text_area if area else st.text_input)(
        label, key=key, persist_state="session"
    )


def _select(
    label: str, options: list, value: Any, key: str, format_func: Any = str
) -> Any:
    st.session_state.setdefault(key, value)
    return st.selectbox(
        label, options, key=key, format_func=format_func, persist_state="session"
    )


def _scope(scope: dict, components: list[dict], key: str, errors: list[str]) -> dict:
    ids = [c["id"] for c in components]
    names = {c["id"]: c["name"] for c in components}
    cid = _select(
        "Component", ids, scope["component_id"], key + ":component", names.get
    )
    component = next(c for c in components if c["id"] == cid)
    original = (
        scope if scope["component_id"] == cid else {"result_ids": [], "where": []}
    )
    prefix = key + ":" + cid
    result_names = {r["id"]: r["name"] for r in component["results"]}
    all_results = st.checkbox(
        "All result types",
        value=not original["result_ids"],
        key=prefix + ":all_results",
        persist_state="session",
    )
    selected = (
        []
        if all_results
        else st.multiselect(
            "Result types",
            list(result_names),
            default=original["result_ids"] or list(result_names),
            format_func=result_names.get,
            key=prefix + ":results",
            persist_state="session",
        )
    )
    if not all_results and not selected:
        errors.append("Choose at least one result type, or select All result types.")
    conditions = []
    existing = {s["field_id"]: s["category_ids"] for s in original["where"]}
    for field in component["fields"]:
        if not field["categories"]:
            continue
        all_rows = st.checkbox(
            f"All {field['name']} values",
            value=field["id"] not in existing,
            key=prefix + ":all:" + field["id"],
            persist_state="session",
        )
        if not all_rows:
            labels = {
                c["id"]: c["display_label"] or c["source_label"]
                for c in field["categories"]
            }
            categories = st.multiselect(
                f"Choose {field['name']} values",
                list(labels),
                default=existing.get(field["id"], list(labels)),
                format_func=labels.get,
                key=prefix + ":categories:" + field["id"],
                persist_state="session",
            )
            conditions.append({"field_id": field["id"], "category_ids": categories})
    return {"component_id": cid, "result_ids": selected, "where": conditions}


def _references(components: list[dict]) -> dict[str, str]:
    references = {}
    for c in components:

        def add(
            label: str,
            field: str | None = None,
            category: str | None = None,
            result: str | None = None,
        ) -> None:
            ref = {
                "component_id": c["id"],
                "field_id": field,
                "category_id": category,
                "result_id": result,
            }
            references[json.dumps(ref, sort_keys=True)] = label

        add(c["name"])
        for field in c["fields"]:
            add(f"{c['name']} / {field['name']}", field["id"])
            for category in field["categories"]:
                add(
                    f"{c['name']} / {field['name']} / {category['display_label'] or category['source_label']}",
                    field["id"],
                    category["id"],
                )
        for result in c["results"]:
            add(f"{c['name']} / {result['name']}", result=result["id"])
    return references


def edit_model(model: dict[str, Any], key: str) -> tuple[dict[str, Any], list[str]]:
    """Render one editable model section, retaining staged changes across stages.

    Parameters
    ----------
    model : dict
        Current in-memory working draft; generated and saved revisions stay intact.
    key : str
        Widget prefix unique to the snapshot and loaded draft revision.

    Returns
    -------
    tuple of dict, list
        Candidate model and understandable editor errors to resolve before saving.
    """
    draft = copy.deepcopy(model)
    errors = []
    section = _select(
        "Edit data model",
        [
            "Overview",
            "Categories and results",
            "Units, time and qualifications",
            "Relationships",
            "Questions",
        ],
        "Overview",
        key + ":section",
    )
    if section == "Overview":
        draft["title"] = _text("Snapshot title", draft["title"], key + ":title")
        for c in draft["components"]:
            with st.container(border=True):
                c["name"] = _text("Component name", c["name"], key + ":name:" + c["id"])
                c["one_result_means"] = _text(
                    "What does one result represent?",
                    c["one_result_means"],
                    key + ":meaning:" + c["id"],
                    True,
                )
                choice = _select(
                    "Values to extract",
                    ["printed_only", "allow_estimates"],
                    c["extraction_policy"],
                    key + ":policy:" + c["id"],
                    lambda v: (
                        "Printed values only"
                        if v == "printed_only"
                        else "Also allow image estimates"
                    ),
                )
                c["extraction_policy"] = choice
                st.caption(
                    "Image estimates remain approximate and need review. Missing source information can stay unknown."
                )
    elif section == "Categories and results":
        ids = [c["id"] for c in draft["components"]]
        names = {c["id"]: c["name"] for c in draft["components"]}
        cid = _select(
            "Component to edit", ids, ids[0], key + ":field_component", names.get
        )
        c = next(c for c in draft["components"] if c["id"] == cid)
        for field in c["fields"]:
            with st.expander(field["name"], expanded=True):
                field["name"] = _text(
                    "Field name",
                    field["name"],
                    key + ":field_name:" + cid + ":" + field["id"],
                )
                field["meaning"] = _text(
                    "What does it identify?",
                    field["meaning"],
                    key + ":field_meaning:" + cid + ":" + field["id"],
                )
                if field["categories"]:
                    rows = [
                        {
                            "Source label": v["source_label"],
                            "Display label": v["display_label"] or "",
                        }
                        for v in field["categories"]
                    ]
                    edited = st.data_editor(
                        rows,
                        key=key + ":labels:" + cid + ":" + field["id"],
                        hide_index=True,
                        width="stretch",
                    )
                    for category, values in zip(field["categories"], edited):
                        category["source_label"] = values["Source label"]
                        category["display_label"] = values["Display label"] or None
        for result in c["results"]:
            with st.container(border=True):
                result["name"] = _text(
                    "Result name",
                    result["name"],
                    key + ":result_name:" + cid + ":" + result["id"],
                )
                result["meaning"] = _text(
                    "What does this value mean?",
                    result["meaning"],
                    key + ":result_meaning:" + cid + ":" + result["id"],
                    True,
                )
                result["value_type"] = _select(
                    "Value type",
                    ["number", "text"],
                    result["value_type"],
                    key + ":result_type:" + cid + ":" + result["id"],
                    lambda v: "Number" if v == "number" else "Text / category",
                )
        st.caption(
            "For additions or a different component structure, ask the LLM to revise the data model. Existing labels and meanings can be edited here."
        )
    elif section == "Units, time and qualifications":
        if not draft["contexts"]:
            st.caption(
                "No context was proposed. Ask the LLM to add any missing data model details."
            )
        else:
            names = {c["id"]: c["name"] for c in draft["contexts"]}
            identifier = _select(
                "Data model detail",
                list(names),
                next(iter(names)),
                key + ":context",
                names.get,
            )
            context = next(c for c in draft["contexts"] if c["id"] == identifier)
            prefix = key + ":context:" + identifier
            st.write(context["meaning"])
            statuses = {
                "source_stated": "Shown in source",
                "interpretation": "Inferred from source",
                "user_supplied": "Additional context from me",
                "unresolved": "Unknown / unresolved",
                "not_applicable": "Not applicable",
            }
            old = tuple(
                st.session_state.setdefault(
                    prefix + ":baseline", [context["status"], context["value"]]
                )
            )
            context["status"] = _select(
                "How is this known?",
                list(statuses),
                context["status"],
                prefix + ":status",
                statuses.get,
            )
            if context["status"] in {"unresolved", "not_applicable"}:
                context["value"] = None
                st.caption("No value is being assumed.")
            else:
                context["value"] = (
                    _text("Value / statement", context["value"], prefix + ":value")
                    or None
                )
            if (context["status"], context["value"]) != old and context[
                "status"
            ] not in {"unresolved", "not_applicable"}:
                explanation = _text(
                    "Supporting source text or clarification",
                    None,
                    prefix + ":support",
                    True,
                )
                location = _text(
                    "Where does this come from?", None, prefix + ":location"
                )
                if not explanation or not location:
                    errors.append(
                        "Add supporting text and its source for the changed data model detail."
                    )
                else:
                    basis = "user" if context["status"] == "user_supplied" else "image"
                    item = {"basis": basis, "text": explanation, "location": location}
                    if item not in context["evidence"]:
                        context["evidence"].append(item)
            st.markdown("**Applies to**")
            remaining = []
            for index, scope in enumerate(context["applies_to"]):
                with st.container(border=True):
                    edited = _scope(
                        scope,
                        draft["components"],
                        prefix + ":scope:" + str(index),
                        errors,
                    )
                    if len(context["applies_to"]) == 1 or not st.checkbox(
                        "Remove this scope", key=prefix + ":remove:" + str(index)
                    ):
                        remaining.append(edited)
            context["applies_to"] = remaining
            if st.button("Add another component scope", key=prefix + ":add_scope"):
                context["applies_to"].append(
                    {
                        "component_id": draft["components"][0]["id"],
                        "result_ids": [],
                        "where": [],
                    }
                )
            with st.expander("Source evidence"):
                for item in context["evidence"]:
                    if item["text"]:
                        st.write(item["text"])
                    st.caption(item["location"])
    elif section == "Relationships":
        references = _references(draft["components"])
        if not draft["relationships"]:
            st.caption("No explicit relationships were proposed.")
        for relationship in draft["relationships"]:
            with st.container(border=True):
                st.write(relationship["description"])
                prefix = key + ":relationship:" + relationship["id"]
                for attribute, label in (
                    ("from_ref", "This item"),
                    ("to_ref", "Related item / parent"),
                ):
                    original = json.dumps(relationship[attribute], sort_keys=True)
                    selection = _select(
                        label,
                        list(references),
                        original,
                        prefix + ":" + attribute,
                        references.get,
                    )
                    relationship[attribute] = json.loads(selection)
                relationship["description"] = _text(
                    "Relationship meaning",
                    relationship["description"],
                    prefix + ":description",
                    True,
                )
    else:
        if not draft["questions"]:
            st.caption("No unresolved questions were proposed.")
        for question in draft["questions"]:
            with st.container(border=True):
                st.write(question["question"])
                prefix = key + ":question:" + question["id"]
                unresolved = st.checkbox(
                    "Leave this unresolved",
                    value=question["resolution"] == "unresolved",
                    key=prefix + ":unknown",
                    persist_state="session",
                )
                if unresolved:
                    question.update(answer=None, resolution="unresolved")
                else:
                    question["answer"] = (
                        _text("Answer", question["answer"], prefix + ":answer", True)
                        or None
                    )
                    resolution = _select(
                        "Answer source",
                        ["source", "user"],
                        (
                            question["resolution"]
                            if question["resolution"] != "unresolved"
                            else "user"
                        ),
                        prefix + ":basis",
                        lambda v: (
                            "Source image"
                            if v == "source"
                            else "Additional context from me"
                        ),
                    )
                    previous = question["evidence"][-1] if question["evidence"] else {}
                    support = _text(
                        "Supporting text / explanation",
                        previous.get("text"),
                        prefix + ":evidence",
                        True,
                    )
                    location = _text(
                        "Where does the answer come from?",
                        previous.get("location"),
                        prefix + ":location",
                    )
                    question["resolution"] = resolution
                    if support and location:
                        question["evidence"] = [
                            {
                                "basis": "image" if resolution == "source" else "user",
                                "text": support,
                                "location": location,
                            }
                        ]
                    else:
                        errors.append(
                            "Provide supporting text and a source for the answer, or leave it unresolved."
                        )
    return draft, errors
