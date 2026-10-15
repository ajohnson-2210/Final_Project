import json
from pathlib import Path

from aj_parser import AJParserFacade
from flow_diagram import FlowDiagram, FlowDiagramEncoder, FlowEdge, FlowNode
from flow_diagram_visualizer import FlowDiagramVisualizer
from study_batch import StudyBatchProcessor
from pseudocode_profiles import PseudocodeProfile


def _encode(source: str):
    parsed = AJParserFacade().parse(source)
    assert parsed.success, parsed.error
    return FlowDiagramEncoder().encode(parsed.ast)


def test_comments_remain_ast_metadata_but_are_not_flow_nodes_or_edges():
    flow = _encode(
        """COMMENT setup only
x <- INTEGER(1)
COMMENT explanation between operations
OUTPUT x
COMMENT trailing note
"""
    )

    assert any(
        item.get("kind") == "CommentNode"
        for item in flow.structured_program.get("body", [])
    )
    assert all(node.node_type.upper() != "COMMENT" for node in flow.nodes.values())
    assert [node.node_type for node in flow.nodes.values()] == [
        "START",
        "END",
        "PROCESS",
        "OUTPUT",
    ]
    assert [(edge.source, edge.target, edge.label) for edge in flow.edges] == [
        ("F3", "F4", "NEXT"),
        ("F1", "F3", "NEXT"),
        ("F4", "F2", "NEXT"),
    ]


def test_comment_only_program_connects_start_directly_to_end():
    flow = _encode("COMMENT documentation only\nCOMMENT another note\n")
    assert [node.node_type for node in flow.nodes.values()] == ["START", "END"]
    assert [(edge.source, edge.target, edge.label) for edge in flow.edges] == [
        ("F1", "F2", "NEXT")
    ]


def test_primary_connection_sides_face_the_peer_node_when_available():
    nodes = {
        "L": FlowNode("L", "PROCESS", "Left", 1),
        "R": FlowNode("R", "PROCESS", "Right", 2),
    }
    diagram = FlowDiagram("L", "R", nodes, [FlowEdge("L", "R", "NEXT")], {})
    positions = {"L": (100.0, 100.0), "R": (500.0, 100.0)}

    route = FlowDiagramVisualizer()._edge_routing_offsets(diagram, positions)[0]
    assert route["source_side"] == "right"
    assert route["target_side"] == "left"
    assert route["source_offset"] == 0.0
    assert route["target_offset"] == 0.0


def test_overlapping_columns_prefer_vertical_facing_side_not_diagonal_centre_angle():
    nodes = {
        "A": FlowNode("A", "PROCESS", "Above-right", 1),
        "B": FlowNode("B", "PROCESS", "Below-left", 2),
    }
    # The rectangles overlap in x even though their centres are diagonally
    # displaced.  Their closest/facing sides are therefore bottom/top.
    diagram = FlowDiagram("A", "B", nodes, [FlowEdge("A", "B", "NEXT")], {})
    positions = {"A": (265.0, 681.0), "B": (90.0, 878.0)}

    route = FlowDiagramVisualizer()._edge_routing_offsets(diagram, positions)[0]
    assert route["source_side"] == "bottom"
    assert route["target_side"] == "top"


def test_legacy_comment_flow_is_not_accepted_as_current(tmp_path, monkeypatch):
    processor = StudyBatchProcessor()
    artifact_directory = tmp_path / "pipeline_artifacts"
    artifact_directory.mkdir()
    (artifact_directory / "flow_diagram.json").write_text(
        json.dumps(
            {
                "entry_node": "F1",
                "exit_node": "F2",
                "nodes": {
                    "F1": {"node_id": "F1", "node_type": "START", "label": "Start", "line": 1, "data": {}},
                    "F2": {"node_id": "F2", "node_type": "END", "label": "End", "line": 1, "data": {}},
                    "F3": {"node_id": "F3", "node_type": "COMMENT", "label": "note", "line": 1, "data": {}},
                },
                "edges": [],
                "structured_program": {"kind": "ProgramNode", "body": []},
            }
        ),
        encoding="utf-8",
    )
    assert processor._flow_diagram_has_comment_nodes(artifact_directory)



def test_legacy_comment_flow_forces_only_affected_baseline_to_regenerate(tmp_path):
    baseline = tmp_path / "Baseline"
    pseudo = baseline / "pseudocode" / "Algorithm - 1"
    reference = baseline / "python" / "Algorithm - 1"
    pseudo.mkdir(parents=True)
    reference.mkdir(parents=True)
    source = pseudo / "Algorithm 1 Pseudocode.txt"
    source.write_text("COMMENT documentation\nx <- INTEGER(1)\nOUTPUT x\n", encoding="utf-8")
    (reference / "Algorithm 1 Python.py").write_text("x=1\nprint(x)\n", encoding="utf-8")
    (reference / "Algorithm 1 Tests.json").write_text(
        json.dumps({"tests": [{"name": "one", "standard_input": [], "expected_output": ["1"]}]}),
        encoding="utf-8",
    )

    processor = StudyBatchProcessor(common_tests_root=tmp_path / "no_common_tests")
    processor.process_baseline(baseline, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
    artifact_directory = pseudo / "pipeline_artifacts"
    flow_path = artifact_directory / "flow_diagram.json"
    legacy = json.loads(flow_path.read_text(encoding="utf-8"))
    legacy["nodes"]["LEGACY_COMMENT"] = {
        "node_id": "LEGACY_COMMENT",
        "node_type": "COMMENT",
        "label": "legacy note",
        "line": 1,
        "data": {},
    }
    flow_path.write_text(json.dumps(legacy, indent=2), encoding="utf-8")

    rerun = processor.process_baseline(baseline, profile=PseudocodeProfile.AJ_DIALECT_STRICT)
    assert rerun["report"]["algorithms"][0]["action"] != "SKIPPED_CURRENT"
    refreshed = json.loads(flow_path.read_text(encoding="utf-8"))
    assert all(node["node_type"] != "COMMENT" for node in refreshed["nodes"].values())
