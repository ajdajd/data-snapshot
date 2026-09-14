"""Smoke-test the interactive metadata reviewer workflow."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest


AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUB"
    "AScY42YAAAAASUVORK5CYII="
)


def test_edit_highlight_and_dirty_navigation_guard(tmp_path: Path) -> None:
    """Keep edits in session and require discard before navigation."""

    snapshots = tmp_path / "snapshots"
    generated = tmp_path / "exported"
    gold = tmp_path / "gold"
    for snapshot_id in ("alpha", "beta"):
        snapshot = snapshots / "unhcr" / "figure" / f"{snapshot_id}.png"
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(_PNG)
        generated.mkdir(parents=True, exist_ok=True)
        (generated / f"{snapshot_id}_metadata.json").write_text(
            json.dumps({"title": f"Generated {snapshot_id}"}), encoding="utf-8"
        )
    runner = tmp_path / "reviewer_app.py"
    runner.write_text(
        "from data_snapshot.metadata_reviewer.app import main\n"
        f"main(['--snapshots-root', {str(snapshots)!r}, "
        f"'--generated-root', {str(generated)!r}, "
        f"'--gold-root', {str(gold)!r}])\n",
        encoding="utf-8",
    )

    app = AppTest.from_file(runner, default_timeout=30).run()
    assert not app.exception
    assert app.session_state["metadata_reviewer_item_id"] == "alpha"

    app.text_input(key="metadata_reviewer_widget:alpha:title").set_value(
        "Reviewed alpha"
    ).run()
    assert not app.exception
    assert app.text_input(key="metadata_reviewer_widget:alpha:title").label == (
        ":orange[Title]"
    )
    assert "Unsaved edits" in app.caption[0].value

    app.button(key="review_next").click().run()
    assert app.session_state["metadata_reviewer_item_id"] == "alpha"
    assert any("Unsaved edits for alpha" in warning.value for warning in app.warning)

    app.button(key="review_guard_discard").click().run()
    assert not app.exception
    assert app.session_state["metadata_reviewer_item_id"] == "beta"
    assert not gold.exists()

    generated_beta = generated / "beta_metadata.json"
    original_generated = generated_beta.read_bytes()
    app.text_input(key="metadata_reviewer_widget:beta:title").set_value(
        "Reviewed beta"
    ).run()
    app.button(key="review_save").click().run()

    assert not app.exception
    assert json.loads(
        (gold / "unhcr" / "figure" / "beta.json").read_text(encoding="utf-8")
    ) == {"title": "Reviewed beta"}
    assert generated_beta.read_bytes() == original_generated
