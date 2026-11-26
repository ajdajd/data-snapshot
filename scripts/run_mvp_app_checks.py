"""Exercise real six-image app sessions, with explicit paid actions and saved logs."""

import argparse
import json
import os
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

from data_snapshot.structured_data_extraction.data_review import load_data_review
from data_snapshot.structured_data_extraction.model_review import load_session
from data_snapshot.structured_data_reviewer.examples import REPO


def main() -> None:
    """Propose first, then finish reviewed cases without repeating completed calls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--phase", choices=["propose", "finish"], required=True)
    parser.add_argument("--sample")
    parser.add_argument("--revision-file", type=Path)
    parser.add_argument(
        "--reextract",
        action="store_true",
        help="Explicit new extraction after a documented failure; preserve earlier attempts",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    os.environ["DATA_SNAPSHOT_REVIEW_WORKSPACE"] = str(root / "sessions")
    pack = json.loads(
        (REPO / "docs/data_extraction/review_design_examples.json").read_text()
    )
    state_path = root / "journeys.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    app_path = REPO / "src/data_snapshot/structured_data_reviewer/app.py"
    sys.argv = [str(app_path)]

    def log(sample: str, action: str, **details: object) -> None:
        row = {"sample": sample, "action": action, **details}
        with (root / "journey.log.jsonl").open("a") as file:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(json.dumps(row, ensure_ascii=False), flush=True)

    def check(app: AppTest) -> None:
        if app.exception or app.error:
            raise RuntimeError(str([e.value for e in [*app.exception, *app.error]]))

    def opened(directory: Path) -> AppTest:
        app = AppTest.from_file(str(app_path), default_timeout=950).run()
        app.text_input(key="reviewer").set_value("MVP verification — assistant").run()
        app.selectbox(key="resume_choice").select(directory).run()
        app.button(key="resume_session").click().run()
        check(app)
        return app

    for case in pack["cases"]:
        sample = case["id"]
        if case["selection"] != "core" or args.sample and args.sample != sample:
            continue
        try:
            if args.phase == "propose":
                if sample in state:
                    log(sample, "reuse_saved_proposal", **state[sample])
                    continue
                image = Path(pack["dataset_root"]) / case["image"]
                app = AppTest.from_file(str(app_path), default_timeout=950).run()
                app.text_input(key="reviewer").set_value(
                    "MVP verification — assistant"
                ).run()
                app.file_uploader(key="png_upload").set_value(
                    (image.name, image.read_bytes(), "image/png")
                ).run()
                app.checkbox(key="use_docling").set_value(sample == "financing").run()
                app.checkbox(key="enable_live").check().run()
                log(sample, "generate_clicked", docling=sample == "financing")
                app.button(key="preprocess_upload").click().run()
                directory = Path(app.session_state["active_session"])
                report = app.session_state["last_api_report"]
                state[sample] = {
                    "directory": str(directory),
                    "proposal_status": report["status"],
                }
                state_path.write_text(json.dumps(state, indent=2) + "\n")
                log(
                    sample,
                    "proposal_returned",
                    **state[sample],
                    spending=report.get("spending"),
                    warnings=[e.value for e in app.warning],
                )
                check(app)
                continue
            entry = state[sample]
            directory = Path(entry["directory"])
            if entry.get("finished") and not args.reextract:
                log(sample, "reuse_finished_journey", **entry)
                continue
            app = opened(directory)
            revision_file = (
                args.revision_file or root / "instructions" / f"{sample}.txt"
            )
            if revision_file.exists() and not entry.get("revision_applied"):
                instruction = revision_file.read_text()
                app.checkbox(key="enable_live").check().run()
                app.text_area(key="assistant_instruction:" + str(directory)).set_value(
                    instruction
                ).run()
                app.button(key="request_proposal").click().run()
                check(app)
                log(
                    sample,
                    "revision_returned",
                    spending=app.session_state["last_api_report"].get("spending"),
                )
                app.button(key="apply_revision").click().run()
                check(app)
                entry["revision_applied"] = True
                state_path.write_text(json.dumps(state, indent=2) + "\n")
                if app.text_area(key="assistant_instruction:" + str(directory)).value:
                    raise AssertionError(
                        "Applied revision did not clear its instruction"
                    )
            if load_session(directory).accepted_revision is None:
                app.button(key="accept_model").click().run()
                check(app)
            else:
                app.session_state["stage"] = "Data"
                app.run()
            reports = [
                p
                for p in (directory / "extractions").glob("*/run.json")
                if json.loads(p.read_text()).get("status") != "preloaded"
            ]
            if not reports or args.reextract:
                app.checkbox(key="enable_live").check().run()
                log(
                    sample,
                    "extract_clicked",
                    model_revision=load_session(directory).accepted_revision,
                )
                app.button(key="extract_live").click().run()
                report = app.session_state["last_api_report"]
                log(
                    sample,
                    "extraction_returned",
                    status=report["status"],
                    spending=report.get("spending"),
                )
                check(app)
                if report["status"] in {"failed", "stale"}:
                    raise RuntimeError(report.get("error", report["status"]))
            extraction = next(
                widget.value
                for widget in app.selectbox
                if widget.label == "Saved result set"
            )
            review = load_data_review(extraction)
            prefix = f"data:{extraction}:{len(review['review']['revisions'])}"
            model = load_session(directory).revisions[-1].model
            for component in model.components:
                app.selectbox(key=prefix + ":component").select(component.id).run()
                check(app)
                for result in component.results:
                    app.selectbox(key=prefix + ":result").select(result.id).run()
                    check(app)
                    log(
                        sample,
                        "result_viewed",
                        component=component.name,
                        result=result.name,
                        displayed_rows=(
                            len(app.dataframe[0].value) if app.dataframe else 0
                        ),
                    )
            # Test an evidence-note edit; keep numerical values intact for source review.
            grid = next(
                (
                    k
                    for k in app.session_state.filtered_state
                    if k.startswith(prefix + ":grid:")
                ),
                None,
            )
            if grid:
                app.session_state[grid] = {
                    "edited_rows": {
                        0: {
                            "Review note": "MVP save/resume interaction tested; see separate numerical review."
                        }
                    },
                    "added_rows": [],
                    "deleted_rows": [],
                }
                app.run()
                check(app)
            app.button(key="save_data").click().run()
            check(app)
            app = opened(directory)
            app.session_state["stage"] = "Data"
            app.run()
            check(app)
            log(
                sample,
                "draft_resumed",
                data_revisions=len(load_data_review(extraction)["review"]["revisions"]),
            )
            # Capture exactly the bytes passed to the UI download control.
            import streamlit as st

            original = st.download_button
            bundle_path = root / f"{sample}.zip"

            def capture(label: str, data: bytes, **kwargs: object) -> bool:
                if kwargs.get("key") == "download_reviewed":
                    bundle_path.write_bytes(data)
                return original(label, data, **kwargs)

            st.download_button = capture
            try:
                app.button(key="approve_data").click().run()
                check(app)
                if not app.get("download_button") or not bundle_path.exists():
                    raise AssertionError("Reviewed export did not reach download")
            finally:
                st.download_button = original
            entry.update(
                finished=True, extraction=str(extraction), bundle=str(bundle_path)
            )
            state_path.write_text(json.dumps(state, indent=2) + "\n")
            log(sample, "bundle_download_ready", **entry)
        except Exception as error:
            log(sample, "FAILED", error=repr(error))
            raise


if __name__ == "__main__":
    main()
