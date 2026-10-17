"""Tests for shared adapter utilities in ``data_snapshot.utils``."""

import json
import logging
import re
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace, TracebackType
from typing import Any

import pytest
from PIL import Image

from data_snapshot.utils import (
    clamp01,
    convert_pdf_to_images,
    normalize_bboxes_xyxy,
    normalize_bboxes_xyxy_with_indices,
    sanitize_bbox,
    utc_now_iso,
)


@pytest.mark.parametrize("failure", [None, "open", "page", "close"])
def test_render_diagnostics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    failure: str | None,
) -> None:
    """Attribute diagnostics and failures without skipping or leaking PDF pages.

    Parameters
    ----------
    tmp_path : Path
        Temporary input location.
    monkeypatch : pytest.MonkeyPatch
        Isolate the rendering library from real PDFs.
    caplog : pytest.LogCaptureFixture
        Capture structured rendering records.
    failure : str | None
        Operation that should fail, or ``None`` for successful rendering.
    """
    messages = ["stale warning from a different document"]
    pdf_path = tmp_path / "input.pdf"

    def warnings(reset: bool = True) -> str:
        """Read and optionally drain the simulated MuPDF message buffer."""
        value = "\n".join(messages)
        if reset:
            messages.clear()
        return value

    class FakeDocument:
        """Simulate two pages and observable resource cleanup."""

        page_count = 2
        closed = False

        def __enter__(self) -> "FakeDocument":
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> None:
            self.closed = True
            if failure == "close":
                messages.append("close diagnostic")
                raise RuntimeError("close failed")

        def load_page(self, page_index: int) -> Any:
            def get_pixmap(*, dpi: int) -> Any:
                assert dpi == 72
                if page_index == 1:
                    messages.append("No common ancestor in structure tree")
                    if failure == "page":
                        raise RuntimeError("page failed")
                return SimpleNamespace(pil_image=lambda: Image.new("RGB", (2, 3)))

            return SimpleNamespace(get_pixmap=get_pixmap)

    document = FakeDocument()

    def open_pdf(path: str) -> FakeDocument:
        """Simulate document-level diagnostics, including an open failure."""
        assert Path(path) == pdf_path
        messages.append("open diagnostic")
        if failure == "open":
            raise RuntimeError("open failed")
        return document

    fake = ModuleType("pymupdf")
    fake.open = open_pdf
    fake.TOOLS = SimpleNamespace(
        reset_mupdf_warnings=messages.clear, mupdf_warnings=warnings
    )
    fake.VersionBind = "test-pymupdf"
    fake.VersionFitz = "test-mupdf"
    monkeypatch.setitem(sys.modules, "pymupdf", fake)
    with caplog.at_level(logging.INFO, logger="data_snapshot.rendering"):
        if failure is None:
            images = convert_pdf_to_images(pdf_path, dpi=72)
            assert len(images) == 2
        else:
            with pytest.raises(RuntimeError, match=f"{failure} failed"):
                convert_pdf_to_images(pdf_path, dpi=72)
    events = [
        json.loads(record.getMessage())
        for record in caplog.records
        if record.name == "data_snapshot.rendering"
    ]
    assert all(event["pdf_path"] == str(pdf_path.resolve()) for event in events)
    assert all("stale warning" not in event["warnings"] for event in events)
    assert document.closed is (failure != "open")
    assert not messages
    if failure is None:
        assert events[-1]["event"] == "document_finished"
        assert events[-1]["rendered_pages"] == events[-1]["page_count"] == 2
        warning = next(event for event in events if event["page_number"] == 2)
        assert warning["status"] == "warning"
        assert warning["page_index"] == 1
        assert warning["width"] == 2 and warning["height"] == 3
        assert "No common ancestor" in warning["warnings"]
    else:
        error = events[-1]
        assert error["event"] == "render_failed"
        assert error["phase"] == failure
        assert error["status"] == "error"
        assert f"RuntimeError: {failure} failed" in error["traceback"]
        assert error["page_number"] == (2 if failure == "page" else None)


class TestUtcNowIso:
    """Tests for ``utc_now_iso``."""

    def test_returns_string(self) -> None:
        assert isinstance(utc_now_iso(), str)

    def test_ends_with_z(self) -> None:
        assert utc_now_iso().endswith("Z")

    def test_iso8601_format(self) -> None:
        ts = utc_now_iso()
        # Should match YYYY-MM-DDTHH:MM:SSZ
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", ts)


class TestClamp01:
    """Tests for ``clamp01``."""

    def test_value_in_range(self) -> None:
        assert clamp01(0.5) == 0.5

    def test_negative_clamped(self) -> None:
        assert clamp01(-0.1) == 0.0

    def test_above_one_clamped(self) -> None:
        assert clamp01(1.5) == 1.0

    def test_boundary_zero(self) -> None:
        assert clamp01(0.0) == 0.0

    def test_boundary_one(self) -> None:
        assert clamp01(1.0) == 1.0


class TestSanitizeBbox:
    """Tests for ``sanitize_bbox``."""

    def test_valid_bbox(self) -> None:
        assert sanitize_bbox([0.1, 0.2, 0.3, 0.4]) == (0.1, 0.2, 0.3, 0.4)

    def test_clamping(self) -> None:
        assert sanitize_bbox([-0.1, 0.0, 1.5, 1.0]) == (0.0, 0.0, 1.0, 1.0)

    def test_wrong_length_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid bbox"):
            sanitize_bbox([0.1, 0.2])

    def test_not_a_list_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid bbox"):
            sanitize_bbox("bad")  # type: ignore[arg-type]


class TestNormalizeBboxesXyxy:
    """Tests for ``normalize_bboxes_xyxy``."""

    def test_absolute_to_normalized(self) -> None:
        bboxes = [[100.0, 200.0, 300.0, 400.0]]
        result = normalize_bboxes_xyxy(bboxes, width=1000, height=1000)
        assert len(result) == 1
        assert result[0] == pytest.approx([0.1, 0.2, 0.3, 0.4])

    def test_already_normalized_passthrough(self) -> None:
        bboxes = [[0.1, 0.2, 0.9, 0.8]]
        result = normalize_bboxes_xyxy(bboxes, width=1000, height=1000)
        assert len(result) == 1
        assert result[0] == pytest.approx([0.1, 0.2, 0.9, 0.8])

    def test_clips_to_01(self) -> None:
        bboxes = [[-50.0, -50.0, 1100.0, 1100.0]]
        result = normalize_bboxes_xyxy(bboxes, width=1000, height=1000)
        assert len(result) == 1
        assert result[0] == pytest.approx([0.0, 0.0, 1.0, 1.0])

    def test_degenerate_box_dropped(self) -> None:
        bboxes = [[0.5, 0.5, 0.5, 0.5]]  # zero area
        result = normalize_bboxes_xyxy(bboxes, width=1000, height=1000)
        assert len(result) == 0

    def test_wrong_length_dropped(self) -> None:
        bboxes = [[0.1, 0.2, 0.3]]  # only 3 elements
        result = normalize_bboxes_xyxy(bboxes, width=1000, height=1000)
        assert len(result) == 0

    def test_swapped_coords_reordered(self) -> None:
        bboxes = [[0.9, 0.8, 0.1, 0.2]]  # x1>x2 and y1>y2
        result = normalize_bboxes_xyxy(bboxes, width=1000, height=1000)
        assert len(result) == 1
        assert result[0] == pytest.approx([0.1, 0.2, 0.9, 0.8])

    def test_multiple_boxes(self) -> None:
        bboxes = [
            [100.0, 100.0, 500.0, 500.0],
            [0.1, 0.2, 0.3, 0.4],
        ]
        result = normalize_bboxes_xyxy(bboxes, width=1000, height=1000)
        assert len(result) == 2

    def test_empty_input(self) -> None:
        result = normalize_bboxes_xyxy([], width=1000, height=1000)
        assert result == []

    def test_retains_source_indices_when_middle_box_is_dropped(self) -> None:
        bboxes = [
            [0.1, 0.1, 0.2, 0.2],
            [0.5, 0.5, 0.5, 0.5],
            [0.7, 0.7, 0.9, 0.9],
        ]
        labels = ["Figure", "Figure", "Table"]
        scores = [0.95, 0.1, 0.85]

        result = normalize_bboxes_xyxy_with_indices(bboxes, width=1000, height=1000)

        assert result == [
            (0, [0.1, 0.1, 0.2, 0.2]),
            (2, [0.7, 0.7, 0.9, 0.9]),
        ]
        assert [(labels[index], scores[index]) for index, _ in result] == [
            ("Figure", 0.95),
            ("Table", 0.85),
        ]
