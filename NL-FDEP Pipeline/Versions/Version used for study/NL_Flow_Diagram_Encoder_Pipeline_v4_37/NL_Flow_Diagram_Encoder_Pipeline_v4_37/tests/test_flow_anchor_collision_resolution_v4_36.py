from drawio_exporter import DrawIOFlowExporter
from flow_diagram import FlowDiagram, FlowEdge, FlowNode
from flow_diagram_visualizer import FlowDiagramVisualizer


def _diagram():
    nodes = {
        "C": FlowNode("C", "DECISION", "Check?", 1),
        "T": FlowNode("T", "PROCESS", "Local action", 2),
        "A": FlowNode("A", "PROCESS", "Higher return", 3),
        "B": FlowNode("B", "PROCESS", "Lower return", 4),
        "END": FlowNode("END", "END", "End", 5),
    }
    edges = [
        FlowEdge("C", "T", "TRUE"),
        FlowEdge("A", "C", "LOOP"),
        FlowEdge("B", "C", "LOOP"),
        FlowEdge("T", "END", "NEXT"),
    ]
    return FlowDiagram(
        entry_node="C",
        exit_node="END",
        nodes=nodes,
        edges=edges,
        structured_program={},
    )


def _positions():
    return {
        "C": (500.0, 300.0),
        "T": (250.0, 520.0),
        "A": (250.0, 680.0),
        "B": (250.0, 840.0),
        "END": (500.0, 1040.0),
    }


def _style_value(style: str, key: str) -> float:
    prefix = f"{key}="
    for part in style.split(";"):
        if part.startswith(prefix):
            return float(part[len(prefix):])
    raise AssertionError(f"{key} not found in style")


def test_equivalent_repeat_returns_share_one_target_anchor_but_not_other_branches():
    diagram = _diagram()
    positions = _positions()
    visualizer = FlowDiagramVisualizer()
    routes = visualizer._edge_routing_offsets(diagram, positions)

    outgoing = diagram.edges[0]
    upper_repeat = diagram.edges[1]
    lower_repeat = diagram.edges[2]

    outgoing_side = routes[0].get("source_side")
    upper_target_side = routes[1].get("target_side")
    lower_target_side = routes[2].get("target_side")

    assert outgoing_side == "bottom"
    assert upper_target_side == lower_target_side == "left"

    outgoing_anchor = visualizer._edge_anchor_point(
        diagram.nodes["C"], positions["C"], outgoing_side, routes[0]["source_offset"]
    )
    upper_repeat_anchor = visualizer._edge_anchor_point(
        diagram.nodes["C"], positions["C"], upper_target_side, routes[1]["target_offset"]
    )
    lower_repeat_anchor = visualizer._edge_anchor_point(
        diagram.nodes["C"], positions["C"], lower_target_side, routes[2]["target_offset"]
    )

    # Equivalent Repeat returns intentionally converge to one target point.
    assert upper_repeat_anchor == lower_repeat_anchor
    # The unrelated outgoing branch still owns a distinct attachment point.
    assert outgoing_anchor != upper_repeat_anchor


def test_equivalent_repeat_returns_share_one_corridor_and_final_trunk():
    diagram = _diagram()
    positions = _positions()
    visualizer = FlowDiagramVisualizer()
    routes = visualizer._edge_routing_offsets(diagram, positions)

    upper = visualizer._edge_route_points(diagram, diagram.edges[1], 1, positions, routes)
    lower = visualizer._edge_route_points(diagram, diagram.edges[2], 2, positions, routes)

    assert routes[1]["loop_offset"] == routes[2]["loop_offset"]
    assert routes[1]["target_offset"] == routes[2]["target_offset"]

    # Each branch joins the same outer corridor immediately at its own source
    # height; from there the union is one continuous return trunk.
    assert upper[1][0] == lower[1][0]
    assert upper[1][1] == upper[0][1]
    assert lower[1][1] == lower[0][1]
    # Both paths then share the same final trunk into the loop header.
    assert upper[-2:] == lower[-2:]


def test_drawio_shared_repeat_trunk_has_one_visible_direction_marker():
    diagram = _diagram()
    positions = _positions()
    exporter = DrawIOFlowExporter()
    exporter._active_flow_diagram = diagram
    exporter._routing_offsets = exporter.layout_engine._edge_routing_offsets(diagram, positions)
    groups = exporter.layout_engine._shared_return_groups(diagram, positions)
    exporter._shared_return_followers = {
        member for group in groups.values() for member in group[1:]
    }

    outgoing_style = exporter._edge_style(diagram.edges[0], 1, positions)
    leader_style = exporter._edge_style(diagram.edges[1], 2, positions)
    follower_style = exporter._edge_style(diagram.edges[2], 3, positions)

    # The unrelated outgoing edge remains on its own point.
    assert _style_value(outgoing_style, "exitY") != _style_value(leader_style, "entryY")
    # Equivalent returns share the target anchor.
    assert _style_value(leader_style, "entryY") == _style_value(follower_style, "entryY")
    # Only the leader draws the visible trunk arrow/label; the follower remains
    # a real semantic edge in XML but visually merges into the leader trunk.
    assert "endArrow=none" not in leader_style
    assert "textOpacity=0" not in leader_style
    assert "endArrow=none" in follower_style
    assert "textOpacity=0" in follower_style
