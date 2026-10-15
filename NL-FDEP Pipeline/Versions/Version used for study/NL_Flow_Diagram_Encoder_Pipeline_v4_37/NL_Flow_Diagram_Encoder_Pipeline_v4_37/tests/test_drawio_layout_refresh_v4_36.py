from xml.etree import ElementTree

from flow_diagram import FlowDiagram, FlowEdge, FlowNode
from study_batch import StudyBatchProcessor


def _simple_flow():
    return FlowDiagram(
        entry_node="S",
        exit_node="E",
        nodes={
            "S": FlowNode("S", "START", "Start", 1),
            "P": FlowNode("P", "PROCESS", "Do work", 2),
            "E": FlowNode("E", "END", "End", 3),
        },
        edges=[FlowEdge("S", "P", "NEXT"), FlowEdge("P", "E", "NEXT")],
        structured_program={"kind": "ProgramNode"},
    )


def test_existing_llm_review_root_refreshes_only_stale_drawio(tmp_path):
    algorithm = tmp_path / "Algorithm - 1"
    artifacts = algorithm / "pipeline_artifacts"
    scoring = artifacts / "scoring"
    scoring.mkdir(parents=True)

    flow_path = artifacts / "flow_diagram.json"
    flow_path.write_text(_simple_flow().to_json(), encoding="utf-8")
    (artifacts / "manifest.json").write_text('{"is_baseline": false}', encoding="utf-8")
    drawio_path = artifacts / "flow_diagram.drawio"
    drawio_path.write_text('<mxfile compressed="false"></mxfile>', encoding="utf-8")
    review_path = scoring / "human_review.json"
    review_path.write_text('{"reviewer":{"reviewer_id":"REV001"}}', encoding="utf-8")

    flow_before = flow_path.read_bytes()
    review_before = review_path.read_bytes()

    processor = StudyBatchProcessor()
    result = processor.refresh_llm_drawio_views(tmp_path)

    assert result["checked"] == 1
    assert result["refreshed"] == 1
    assert result["skipped_baseline"] == 0
    assert flow_path.read_bytes() == flow_before
    assert review_path.read_bytes() == review_before
    root = ElementTree.parse(drawio_path).getroot()
    assert root.attrib["nl_fdep_layout_revision"] == processor.pipeline.drawio_exporter.LAYOUT_REVISION

    # Once current, opening Human Review again must not rewrite the file.
    refreshed_bytes = drawio_path.read_bytes()
    second = processor.refresh_llm_drawio_views(tmp_path)
    assert second["refreshed"] == 0
    assert drawio_path.read_bytes() == refreshed_bytes


def test_review_refresh_never_touches_baseline_artifacts(tmp_path):
    algorithm = tmp_path / "Algorithm - 1"
    artifacts = algorithm / "pipeline_artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "flow_diagram.json").write_text(_simple_flow().to_json(), encoding="utf-8")
    (artifacts / "manifest.json").write_text('{"is_baseline": true}', encoding="utf-8")
    drawio_path = artifacts / "flow_diagram.drawio"
    original = b'<mxfile compressed="false"><diagram id="baseline-stays-old"/></mxfile>'
    drawio_path.write_bytes(original)

    result = StudyBatchProcessor().refresh_llm_drawio_views(tmp_path)

    assert result["checked"] == 0
    assert result["refreshed"] == 0
    assert result["skipped_baseline"] == 1
    assert drawio_path.read_bytes() == original


def test_llm_processing_refreshes_stale_drawio_before_protected_resume_skip(tmp_path, monkeypatch):
    """Protected resume states must not block visual-only layout refreshes."""
    import study_batch as study_batch_module

    algorithm = tmp_path / "Algorithm - 27"
    artifacts = algorithm / "pipeline_artifacts"
    artifacts.mkdir(parents=True)
    source = algorithm / "Algorithm 27.txt"
    source.write_text("DISPLAY 27", encoding="utf-8")

    monkeypatch.setattr(study_batch_module, "validate_llm_results", lambda *a, **k: {})
    monkeypatch.setattr(study_batch_module, "write_preflight", lambda *a, **k: {})
    monkeypatch.setattr(study_batch_module, "discover_algorithm_folders", lambda *a, **k: [(27, algorithm)])
    monkeypatch.setattr(study_batch_module, "expected_pseudocode_file", lambda *a, **k: source)
    monkeypatch.setattr(study_batch_module, "adjudicate_files", lambda *a, **k: None)
    monkeypatch.setattr(study_batch_module, "aggregate_algorithm_folders", lambda *a, **k: {})
    monkeypatch.setattr(study_batch_module, "generate_dashboards_for_completed_batch", lambda *a, **k: {})
    monkeypatch.setattr(study_batch_module, "_archive_analysis_snapshot", lambda *a, **k: tmp_path / "history")

    processor = StudyBatchProcessor()
    monkeypatch.setattr(processor, "_tests_for_algorithm", lambda *a, **k: None)
    events = []
    monkeypatch.setattr(processor, "_refresh_drawio_from_canonical_flow", lambda art: events.append(("refresh", art)) or True)
    monkeypatch.setattr(processor, "_resume_status", lambda *a, **k: events.append(("resume", artifacts)) or "REVIEW_PROTECTED_INPUT_CHANGED")
    monkeypatch.setattr(processor, "_write_batch_reports", lambda *a, **k: {"report": str(tmp_path / "report.json")})
    monkeypatch.setattr(processor, "common_test_pack_status", lambda: {})

    result = processor.process_llm_results(tmp_path)

    assert events[:2] == [("refresh", artifacts), ("resume", artifacts)]
    assert result["preflight"] == {}
