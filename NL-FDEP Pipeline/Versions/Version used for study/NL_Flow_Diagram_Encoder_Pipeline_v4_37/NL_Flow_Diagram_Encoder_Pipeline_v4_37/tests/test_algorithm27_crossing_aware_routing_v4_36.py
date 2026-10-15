from drawio_exporter import DrawIOFlowExporter
from flow_diagram import FlowDiagram, FlowEdge, FlowNode
from flow_diagram_visualizer import FlowDiagramVisualizer


def _algorithm27_shape():
    nodes = {
        "F1": FlowNode("F1", "START", "Start", 1),
        "F2": FlowNode("F2", "END", "End", 1),
        "F3": FlowNode("F3", "FUNCTION", "Run function unnamed_function with Matrix, N", 1),
        "F4": FlowNode("F4", "CALL", "Call transpose_in_place with Matrix", 2),
        "F5": FlowNode("F5", "LOOP_DECISION", "For each Row in Matrix", 3),
        "F6": FlowNode("F6", "CALL", "Call reverse_list with Row", 4),
        "F7": FlowNode("F7", "OUTPUT", "Display Matrix", 7),
    }
    edges = [
        FlowEdge("F5", "F6", "ITERATE"),
        FlowEdge("F6", "F5", "LOOP"),
        FlowEdge("F4", "F5", "NEXT"),
        FlowEdge("F5", "F7", "NEXT"),
        FlowEdge("F3", "F4", "NEXT"),
        FlowEdge("F1", "F3", "NEXT"),
        FlowEdge("F7", "F2", "NEXT"),
    ]
    positions = {
        "F1": (265.0, 90.0),
        "F2": (265.0, 1075.0),
        "F3": (265.0, 287.0),
        "F4": (265.0, 484.0),
        "F5": (265.0, 681.0),
        "F6": (90.0, 878.0),
        "F7": (440.0, 878.0),
    }
    return FlowDiagram("F1", "F2", nodes, edges, {}), positions


def _proper_segment_crossing(a, b, c, d):
    """True only for an interior H/V crossing, not a shared endpoint."""
    a_vertical = abs(a[0] - b[0]) < 0.001
    c_vertical = abs(c[0] - d[0]) < 0.001
    if a_vertical == c_vertical:
        return False

    if a_vertical:
        vertical_a, vertical_b = a, b
        horizontal_a, horizontal_b = c, d
    else:
        vertical_a, vertical_b = c, d
        horizontal_a, horizontal_b = a, b

    vx = vertical_a[0]
    hy = horizontal_a[1]
    vmin, vmax = sorted((vertical_a[1], vertical_b[1]))
    hmin, hmax = sorted((horizontal_a[0], horizontal_b[0]))
    return hmin < vx < hmax and vmin < hy < vmax


def _routes_cross(first, second):
    return any(
        _proper_segment_crossing(a, b, c, d)
        for a, b in zip(first, first[1:])
        for c, d in zip(second, second[1:])
    )


def test_algorithm27_repeat_uses_clear_right_midpoint_instead_of_crossing_yes_path():
    diagram, positions = _algorithm27_shape()
    visualizer = FlowDiagramVisualizer()
    routes = visualizer._edge_routing_offsets(diagram, positions)

    # F6 has an incoming connector on its top midpoint.  Its Repeat return
    # should therefore use the still-free right midpoint that faces the loop
    # header, instead of sweeping left across the Yes/body connector.
    assert routes[0]["target_side"] == "top"
    assert routes[1]["source_side"] == "right"
    assert routes[1]["source_offset"] == 0.0

    yes_route = visualizer._edge_route_points(diagram, diagram.edges[0], 0, positions, routes)
    repeat_route = visualizer._edge_route_points(diagram, diagram.edges[1], 1, positions, routes)
    assert not _routes_cross(yes_route, repeat_route)


def test_loop_exit_next_is_displayed_as_no_but_ordinary_next_stays_unlabelled():
    visualizer = FlowDiagramVisualizer()
    exporter = DrawIOFlowExporter()

    assert visualizer._display_edge_label("ITERATE", "LOOP_DECISION") == "Yes"
    assert visualizer._display_edge_label("NEXT", "LOOP_DECISION") == "No"
    assert visualizer._display_edge_label("NEXT", "PROCESS") == ""

    assert exporter._edge_label("ITERATE", "LOOP_DECISION") == "Yes"
    assert exporter._edge_label("NEXT", "LOOP_DECISION") == "No"
    assert exporter._edge_label("NEXT", "PROCESS") == ""
