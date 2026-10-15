from flow_diagram import FlowDiagram, FlowEdge, FlowNode
from flow_diagram_visualizer import FlowDiagramVisualizer


def _diagram(nodes, edges, entry, exit_node):
    return FlowDiagram(
        entry_node=entry,
        exit_node=exit_node,
        nodes=nodes,
        edges=edges,
        structured_program={},
    )


def test_decision_yes_no_claim_true_vertices_before_fractional_anchors():
    nodes = {
        "A1": FlowNode("A1", "PROCESS", "Incoming one", 1),
        "A2": FlowNode("A2", "PROCESS", "Incoming two", 2),
        "D": FlowNode("D", "DECISION", "Check?", 3),
        "Y": FlowNode("Y", "PROCESS", "Yes action", 4),
        "N": FlowNode("N", "DECISION", "Else check?", 5),
        "O": FlowNode("O", "PROCESS", "Other", 6),
        "END": FlowNode("END", "END", "End", 7),
    }
    edges = [
        FlowEdge("A1", "D", "NEXT"),
        FlowEdge("A2", "D", "NEXT"),
        FlowEdge("D", "Y", "TRUE"),
        FlowEdge("D", "N", "FALSE"),
        FlowEdge("D", "O", "NEXT"),
        FlowEdge("Y", "END", "NEXT"),
        FlowEdge("N", "END", "NEXT"),
        FlowEdge("O", "END", "NEXT"),
    ]
    positions = {
        "A1": (440.0, 100.0),
        "A2": (650.0, 180.0),
        "D": (440.0, 400.0),
        "Y": (100.0, 650.0),
        "N": (780.0, 650.0),
        "O": (440.0, 760.0),
        "END": (440.0, 1000.0),
    }
    diagram = _diagram(nodes, edges, "A1", "END")
    routes = FlowDiagramVisualizer()._edge_routing_offsets(diagram, positions)

    # Even though the two incoming edges appear first in the edge list, the
    # semantic Yes/No branches own true rhombus vertices with no fractional
    # displacement.
    assert routes[2]["source_side"] == "left"
    assert routes[3]["source_side"] == "right"
    assert routes[2]["source_offset"] == 0.0
    assert routes[3]["source_offset"] == 0.0

    # Four logical attachments consume four distinct vertices before the fifth
    # is permitted to share an edge fractionally.
    incident = [
        (routes[0]["target_side"], routes[0]["target_offset"]),
        (routes[1]["target_side"], routes[1]["target_offset"]),
        (routes[2]["source_side"], routes[2]["source_offset"]),
        (routes[3]["source_side"], routes[3]["source_offset"]),
        (routes[4]["source_side"], routes[4]["source_offset"]),
    ]
    zero_offset_sides = {side for side, offset in incident if offset == 0.0}
    assert zero_offset_sides == {"top", "right", "bottom", "left"}
    assert any(offset != 0.0 for _, offset in incident)


def test_rectangle_uses_all_edge_midpoints_before_fractional_connections():
    nodes = {
        "A1": FlowNode("A1", "PROCESS", "Incoming one", 1),
        "A2": FlowNode("A2", "PROCESS", "Incoming two", 2),
        "P": FlowNode("P", "PROCESS", "Process", 3),
        "B1": FlowNode("B1", "PROCESS", "Below one", 4),
        "B2": FlowNode("B2", "PROCESS", "Below two", 5),
        "L": FlowNode("L", "PROCESS", "Left", 6),
        "END": FlowNode("END", "END", "End", 7),
    }
    edges = [
        FlowEdge("A1", "P", "NEXT"),
        FlowEdge("A2", "P", "NEXT"),
        FlowEdge("P", "B1", "NEXT"),
        FlowEdge("P", "B2", "NEXT"),
        FlowEdge("P", "L", "NEXT"),
        FlowEdge("B1", "END", "NEXT"),
        FlowEdge("B2", "END", "NEXT"),
        FlowEdge("L", "END", "NEXT"),
    ]
    positions = {
        "A1": (440.0, 100.0),
        "A2": (620.0, 160.0),
        "P": (440.0, 440.0),
        "B1": (440.0, 700.0),
        "B2": (620.0, 760.0),
        "L": (100.0, 440.0),
        "END": (440.0, 1000.0),
    }
    diagram = _diagram(nodes, edges, "A1", "END")
    routes = FlowDiagramVisualizer()._edge_routing_offsets(diagram, positions)

    incident = [
        (routes[0]["target_side"], routes[0]["target_offset"]),
        (routes[1]["target_side"], routes[1]["target_offset"]),
        (routes[2]["source_side"], routes[2]["source_offset"]),
        (routes[3]["source_side"], routes[3]["source_offset"]),
        (routes[4]["source_side"], routes[4]["source_offset"]),
    ]
    midpoint_sides = {side for side, offset in incident if offset == 0.0}
    assert midpoint_sides == {"top", "right", "bottom", "left"}
    assert sum(offset != 0.0 for _, offset in incident) == 1
