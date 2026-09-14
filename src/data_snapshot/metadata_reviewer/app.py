"""Run the local Streamlit shell for Data Snapshot metadata review.

Use Streamlit's argument separator to pass dataset roots::

    streamlit run src/data_snapshot/metadata_reviewer/app.py -- \
        --snapshots-root notebooks/metadata_extraction/data/snapshots \
        --generated-root notebooks/metadata_extraction/exported \
        --gold-root notebooks/metadata_extraction/gold
"""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Sequence

import streamlit as st
from pydantic import ValidationError

from data_snapshot.metadata_reviewer.forms import (
    clear_form_widget_state,
    render_metadata_form,
)
from data_snapshot.metadata_reviewer.storage import (
    DiscoveryResult,
    ReviewItem,
    discover_review_items,
    load_review_records,
    metadata_values_equal,
    save_gold,
    validate_metadata,
)


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_SNAPSHOT_ROOT = (
    _PROJECT_ROOT / "notebooks" / "metadata_extraction" / "data" / "snapshots"
)
_DEFAULT_GENERATED_ROOT = (
    _PROJECT_ROOT / "notebooks" / "metadata_extraction" / "exported"
)
_DEFAULT_GOLD_ROOT = _PROJECT_ROOT / "notebooks" / "metadata_extraction" / "gold"


def main(args: Sequence[str] | None = None) -> None:
    """Render the metadata-review shell.

    Parameters
    ----------
    args : collections.abc.Sequence[str] | None, optional
        Reviewer-specific command-line arguments. Defaults to ``sys.argv[1:]``.
    """

    paths = _parse_args(args)
    st.set_page_config(page_title="Metadata Reviewer", layout="wide")
    st.markdown("### Data Snapshot Metadata Reviewer")

    try:
        discovery = discover_review_items(
            paths.snapshots_root, paths.generated_root, paths.gold_root
        )
    except (OSError, ValueError) as error:
        st.error(str(error))
        st.stop()
        return

    if not discovery.items:
        st.warning("No matching snapshot and generated metadata files were found.")
        _render_warnings(discovery)
        st.stop()
        return

    index = _current_index(discovery)
    item = discovery.items[index]
    try:
        generated, working, baseline = _current_records(item)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        st.error(str(error))
        st.stop()
        return

    notice = st.session_state.pop("metadata_reviewer_notice", None)
    if notice:
        st.toast(notice)

    toolbar_placeholder = st.empty()
    guard_placeholder = st.empty()
    _render_warnings(discovery)

    st.markdown(
        """
        <style>
        .st-key-metadata_reviewer_snapshot {
            position: sticky;
            top: 4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    image_column, metadata_column = st.columns((1.15, 1), gap="large")
    with image_column:
        with st.container(key="metadata_reviewer_snapshot"):
            st.image(
                item.snapshot_path, caption=item.snapshot_path.name, width="stretch"
            )
    with metadata_column:
        status_placeholder = st.empty()
        validation_placeholder = st.empty()
        editing_tab, generated_tab = st.tabs(("Edit gold", "Generated reference"))
        with editing_tab:
            render_metadata_form(working, generated)
        with generated_tab:
            with st.container(
                height=760, border=True, key="metadata_reviewer_editor_generated"
            ):
                st.json(generated, expanded=2)

        _render_record_status(status_placeholder, item, working, generated)
        _render_validation_status(validation_placeholder, working)

    dirty = not metadata_values_equal(working, baseline)
    with toolbar_placeholder.container():
        _render_toolbar(discovery, item, index, working, dirty)
    with guard_placeholder.container():
        _render_navigation_guard(discovery, item, working)

    st.caption("Orange labels differ from the immutable generated reference.")


def _parse_args(args: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots-root", type=Path, default=_DEFAULT_SNAPSHOT_ROOT)
    parser.add_argument("--generated-root", type=Path, default=_DEFAULT_GENERATED_ROOT)
    parser.add_argument("--gold-root", type=Path, default=_DEFAULT_GOLD_ROOT)
    return parser.parse_args(args)


def _current_index(discovery: DiscoveryResult) -> int:
    signature = tuple(item.snapshot_id for item in discovery.items)
    if st.session_state.get("metadata_reviewer_signature") != signature:
        st.session_state["metadata_reviewer_signature"] = signature
        st.session_state["metadata_reviewer_index"] = next(
            (index for index, item in enumerate(discovery.items) if not item.reviewed),
            0,
        )
    index = int(st.session_state.get("metadata_reviewer_index", 0))
    return max(0, min(index, len(discovery.items) - 1))


def _current_records(
    item: ReviewItem,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    if st.session_state.get("metadata_reviewer_item_id") != item.snapshot_id:
        generated, working = load_review_records(item)
        clear_form_widget_state()
        st.session_state["metadata_reviewer_item_id"] = item.snapshot_id
        st.session_state["metadata_reviewer_generated"] = generated
        st.session_state["metadata_reviewer_working"] = working
        st.session_state["metadata_reviewer_baseline"] = deepcopy(working)
        st.session_state.pop("metadata_reviewer_pending_index", None)
    return (
        st.session_state["metadata_reviewer_generated"],
        st.session_state["metadata_reviewer_working"],
        st.session_state["metadata_reviewer_baseline"],
    )


def _render_toolbar(
    discovery: DiscoveryResult,
    item: ReviewItem,
    index: int,
    working: dict[str, object],
    dirty: bool,
) -> None:
    reviewed_count = sum(candidate.reviewed for candidate in discovery.items)
    source = item.snapshot_path.parent.parent.name
    artifact_type = item.snapshot_path.parent.name
    status = "Unsaved edits" if dirty else "Reviewed" if item.reviewed else "Unreviewed"
    st.caption(
        f"**{item.snapshot_id}** · {source} / {artifact_type} · "
        f"{index + 1} of {len(discovery.items)} · {reviewed_count} reviewed · {status}"
    )

    previous_column, save_column, next_column, _ = st.columns((1, 2, 1, 5))
    if previous_column.button(
        "Previous",
        disabled=index == 0 or _navigation_pending(),
        width="stretch",
        key="review_previous",
    ):
        _request_navigation(index - 1, dirty)
    if next_column.button(
        "Next",
        disabled=index == len(discovery.items) - 1 or _navigation_pending(),
        width="stretch",
        key="review_next",
    ):
        _request_navigation(index + 1, dirty)
    if save_column.button(
        "Save Gold & Next",
        type="primary",
        disabled=_navigation_pending(),
        width="stretch",
        key="review_save",
    ):
        _save_and_move(item, working, min(index + 1, len(discovery.items) - 1))


def _render_navigation_guard(
    discovery: DiscoveryResult,
    item: ReviewItem,
    working: dict[str, object],
) -> None:
    target = st.session_state.get("metadata_reviewer_pending_index")
    if target is None:
        return
    target_item = discovery.items[target]
    st.warning(
        f"Unsaved edits for {item.snapshot_id}. Save or discard them before moving "
        f"to {target_item.snapshot_id}."
    )
    save_column, discard_column, cancel_column, _ = st.columns((2, 2, 1, 5))
    if save_column.button("Save & move", type="primary", key="review_guard_save"):
        _save_and_move(item, working, target)
    if discard_column.button("Discard & move", key="review_guard_discard"):
        _move_to(target)
    if cancel_column.button("Cancel", key="review_guard_cancel"):
        st.session_state.pop("metadata_reviewer_pending_index", None)
        st.rerun()


def _render_record_status(
    placeholder: Any,
    item: ReviewItem,
    working: dict[str, object],
    generated: dict[str, object],
) -> None:
    with placeholder.container():
        if not item.reviewed:
            st.info(
                "No gold file exists. The generated metadata is the working record."
            )
        elif metadata_values_equal(working, generated):
            st.markdown(":green[**Gold matches generated metadata.**]")
        else:
            st.markdown(":orange[**Gold differs from generated metadata.**]")


def _render_validation_status(placeholder: Any, working: dict[str, object]) -> None:
    try:
        validate_metadata(working)
    except ValidationError as error:
        with placeholder.container():
            st.error("Fix these errors before saving gold:")
            st.markdown(_format_validation_error(error))


def _navigation_pending() -> bool:
    return "metadata_reviewer_pending_index" in st.session_state


def _request_navigation(target: int, dirty: bool) -> None:
    if dirty:
        st.session_state["metadata_reviewer_pending_index"] = target
        st.rerun()
    _move_to(target)


def _save_and_move(item: ReviewItem, working: dict[str, object], target: int) -> None:
    try:
        metadata = save_gold(item, working)
    except ValidationError as error:
        st.error("Gold was not saved because the working record is invalid.")
        st.markdown(_format_validation_error(error))
        return
    except (OSError, ValueError) as error:
        st.error(str(error))
        return
    canonical = metadata.model_dump(mode="json", exclude_none=True)
    st.session_state["metadata_reviewer_working"] = canonical
    st.session_state["metadata_reviewer_baseline"] = deepcopy(canonical)
    st.session_state["metadata_reviewer_notice"] = f"Saved gold for {item.snapshot_id}."
    if target == st.session_state["metadata_reviewer_index"]:
        clear_form_widget_state()
        st.session_state.pop("metadata_reviewer_pending_index", None)
        st.rerun()
    _move_to(target)


def _move_to(target: int) -> None:
    st.session_state["metadata_reviewer_index"] = target
    st.session_state.pop("metadata_reviewer_item_id", None)
    st.session_state.pop("metadata_reviewer_pending_index", None)
    clear_form_widget_state()
    st.rerun()


def _render_warnings(discovery: DiscoveryResult) -> None:
    if not discovery.warnings:
        return
    with st.expander(f"Discovery warnings ({len(discovery.warnings)})"):
        for warning in discovery.warnings:
            st.warning(warning)


def _format_validation_error(error: ValidationError) -> str:
    lines = []
    for detail in error.errors(include_url=False):
        path = "".join(
            f"[{part}]" if isinstance(part, int) else ("." if position else "") + part
            for position, part in enumerate(detail["loc"])
        )
        lines.append(f"- `{path or '<record>'}`: {detail['msg']}")
    return "\n".join(lines)


if __name__ == "__main__":
    main(sys.argv[1:])
