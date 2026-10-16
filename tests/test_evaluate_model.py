import json
from pathlib import Path

import pytest

from data_snapshot.constants import ROOT
from data_snapshot.evaluation.evaluate_model import (
    DetObj,
    Stats,
    evaluate,
    greedy_match,
    print_summary_metrics,
)
from data_snapshot.utils import load_json


def test_evaluate_model() -> None:
    ref_path = ROOT / "tests/data/evaluate_model_ref.json"
    gt_path = ROOT / "tests/data/evaluate_model_gt.json"
    pred_path = ROOT / "tests/data/evaluate_model_pred.json"

    ref = load_json(ref_path)
    del ref["info"]
    res = evaluate(
        gt_json_path=gt_path,
        pred_json_path=pred_path,
        iou_thresholds=(0.5, 0.75),
        labels=["Figure", "Table"],
        output_path=None,
    )
    del res["info"]
    assert ref == res


@pytest.mark.parametrize("threshold", [0.0, 1.0])
def test_greedy_match_accepts_boundary_thresholds(threshold: float) -> None:
    obj = DetObj("page", "object", "Figure", (0.0, 0.0, 1.0, 1.0))

    greedy_match([obj], [obj], threshold)


@pytest.mark.parametrize("threshold", [-0.1, 1.1])
def test_greedy_match_rejects_invalid_thresholds(threshold: float) -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        greedy_match([], [], threshold)


def test_evaluate_rejects_invalid_threshold_before_loading_files() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        evaluate("missing-gt.json", "missing-pred.json", iou_thresholds=(-0.1,))


def test_undefined_metrics_are_none() -> None:
    stats = Stats()

    assert stats.precision() is None
    assert stats.recall() is None
    assert stats.mean_iou() is None
    assert stats.mean_area_precision() is None
    assert stats.mean_area_recall() is None


def test_evaluate_writes_undefined_metrics_as_null(tmp_path: Path) -> None:
    gt_path = ROOT / "tests/data/evaluate_model_gt.json"
    pred_path = ROOT / "tests/data/evaluate_model_pred.json"
    output_path = tmp_path / "report.json"

    evaluate(
        gt_path,
        pred_path,
        iou_thresholds=(0.5,),
        labels=("Missing",),
        output_path=output_path,
    )

    report = load_json(output_path)
    assert report["metrics"]["0.5"]["micro"]["precision"] is None
    assert "NaN" not in output_path.read_text(encoding="utf-8")


def test_print_summary_metrics_renders_undefined_values(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    report_path = tmp_path / "report.json"
    metrics = {
        "tp": 0,
        "fp": 0,
        "fn": 0,
        "precision": None,
        "recall": None,
        "matched": 0,
        "mean_iou": None,
        "mean_area_precision": None,
        "mean_area_recall": None,
    }
    report_path.write_text(
        json.dumps({"metrics": {"0.5": {"per_class": {"Figure": metrics}}}}),
        encoding="utf-8",
    )

    print_summary_metrics(report_path, 0.5)

    assert "N/A" in capsys.readouterr().out
