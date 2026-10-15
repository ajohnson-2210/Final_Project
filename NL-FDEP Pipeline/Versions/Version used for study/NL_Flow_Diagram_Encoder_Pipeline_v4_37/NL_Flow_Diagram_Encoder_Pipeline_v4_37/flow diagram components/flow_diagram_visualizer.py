"""Standard-convention flowchart visualisation for machine-readable flow diagrams."""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
import html
import json
import heapq
import webbrowser

from flow_diagram import FlowDiagram, FlowEdge, FlowNode


class FlowDiagramVisualizer:
    """Creates an interactive SVG flowchart using conventional flowchart symbols.

    The visual notation follows the convention demonstrated by the supplied
    Tic-Tac-Toe draw.io example: terminators for start/end, diamonds for
    decisions, process rectangles, input/output parallelograms, orthogonal
    arrow connectors, and visible branch labels.
    """

    NODE_WIDTH = 230
    NODE_HEIGHT = 64
    DECISION_WIDTH = 230
    DECISION_HEIGHT = 112
    HORIZONTAL_GAP = 120
    VERTICAL_GAP = 85
    MARGIN = 90

    DECISION_TYPES = {"DECISION", "LOOP_DECISION", "CATCH_DECISION"}
    INPUT_OUTPUT_TYPES = {"INPUT", "OUTPUT"}
    TERMINATOR_TYPES = {"START", "END"}
    SUBROUTINE_TYPES = {"FUNCTION", "CALL"}
    BACK_EDGE_LABELS = {"LOOP", "REPEAT", "BACK"}
    EDGE_ANCHOR_SPACING = 22
    EDGE_MID_LANE_SPACING = 16
    EDGE_MAX_ANCHOR_OFFSET = 44
    EDGE_NODE_CLEARANCE = 18
    EDGE_ROUTE_LEAD = 24
    EDGE_BEND_PENALTY = 34

    def generate(
        self,
        flow_diagram: FlowDiagram,
        output_path: str | Path,
        open_browser: bool = False,
    ) -> Path:
        destination = Path(output_path).resolve()
        positions = self._calculate_positions(flow_diagram)
        width, height = self._calculate_canvas_size(positions)
        svg_edges = self._render_edges(flow_diagram, positions)
        svg_nodes = self._render_nodes(flow_diagram, positions)
        diagram_json = json.dumps(flow_diagram.to_dict())

        document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NL-FDEP Flow Diagram</title>
<style>
:root {{ color-scheme: light; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; background: #f4f5f7; color: #16191f; }}
header {{ position: sticky; top: 0; z-index: 10; padding: 14px 18px; background: white; border-bottom: 1px solid #c9cdd3; }}
header h1 {{ margin: 0 0 4px; font-size: 20px; }}
header p {{ margin: 0; color: #555d69; font-size: 13px; }}
.controls {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }}
.controls input {{ min-width: 220px; flex: 1; padding: 8px 10px; border: 1px solid #9da4ae; border-radius: 5px; }}
.controls button {{ padding: 8px 12px; border: 1px solid #8f97a3; border-radius: 5px; background: white; cursor: pointer; }}
.viewport {{ overflow: hidden; width: 100%; height: calc(100vh - 108px); background: white; cursor: grab; }}
.viewport.dragging {{ cursor: grabbing; }}
svg {{ width: 100%; height: 100%; user-select: none; }}
.flow-node {{ cursor: pointer; }}
.flow-node .shape {{ fill: white; stroke: #20242a; stroke-width: 1.6; vector-effect: non-scaling-stroke; }}
.flow-node text {{ fill: #111418; font-size: 13px; text-anchor: middle; dominant-baseline: middle; pointer-events: none; }}
.flow-node .metadata {{ fill: #606874; font-size: 10px; }}
.flow-node.match .shape {{ stroke: #d18b00; stroke-width: 4; }}
.flow-node.selected .shape {{ stroke: #1769aa; stroke-width: 4; }}
.flow-edge {{ fill: none; stroke: #252a31; stroke-width: 1.45; vector-effect: non-scaling-stroke; marker-end: url(#arrowhead); }}
.shared-return-follower {{ marker-end: none; }}
.edge-label rect {{ fill: white; stroke: none; }}
.edge-label text {{ fill: #20242a; font-size: 11px; text-anchor: middle; dominant-baseline: middle; }}
.legend {{ position: fixed; right: 14px; bottom: 14px; padding: 9px 11px; background: rgba(255,255,255,.94); border: 1px solid #c9cdd3; border-radius: 6px; font-size: 11px; line-height: 1.6; }}
</style>
</head>
<body>
<header>
<h1>NL to Flow Diagram Encoder Pipeline</h1>
<p>Standard flowchart notation generated from AJ pseudocode.</p>
<div class="controls">
<input id="search" placeholder="Search step, type, line, or node ID">
<button id="zoom-in" type="button">Zoom in</button>
<button id="zoom-out" type="button">Zoom out</button>
<button id="fit" type="button">Fit diagram</button>
</div>
</header>
<div id="viewport" class="viewport">
<svg id="diagram" viewBox="0 0 {width} {height}" role="img" aria-label="Generated program flow diagram">
<defs>
<marker id="arrowhead" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto" markerUnits="strokeWidth">
<path d="M 0 0 L 9 3.5 L 0 7 z" fill="#252a31"></path>
</marker>
</defs>
<g id="canvas">{svg_edges}{svg_nodes}</g>
</svg>
</div>
<div class="legend">Oval: Start/End<br>Diamond: Decision<br>Parallelogram: Input/Output<br>Rectangle: Process<br>Double rectangle: Function/Call</div>
<script>
const diagramData = {diagram_json};
const svg = document.getElementById('diagram');
const canvas = document.getElementById('canvas');
const viewport = document.getElementById('viewport');
const INITIAL_SCALE = 1.15;
let scale = INITIAL_SCALE;
let translateX = 0;
let translateY = 0;
let dragging = false;
let startX = 0;
let startY = 0;

function applyTransform() {{
    canvas.setAttribute('transform', `translate(${{translateX}} ${{translateY}}) scale(${{scale}})`);
}}

function initialView() {{
    const box = canvas.getBBox();
    const visibleWidth = viewport.clientWidth;
    scale = INITIAL_SCALE;
    translateX = (visibleWidth - box.width * scale) / 2 - box.x * scale;
    translateY = 28 - box.y * scale;
    applyTransform();
}}

function fitDiagram() {{
    const box = canvas.getBBox();
    const visibleWidth = viewport.clientWidth;
    const visibleHeight = viewport.clientHeight;
    scale = Math.min(visibleWidth / (box.width + 80), visibleHeight / (box.height + 80), 1.3);
    translateX = (visibleWidth - box.width * scale) / 2 - box.x * scale;
    translateY = (visibleHeight - box.height * scale) / 2 - box.y * scale;
    applyTransform();
}}

document.getElementById('zoom-in').addEventListener('click', () => {{ scale *= 1.15; applyTransform(); }});
document.getElementById('zoom-out').addEventListener('click', () => {{ scale /= 1.15; applyTransform(); }});
document.getElementById('fit').addEventListener('click', fitDiagram);

document.getElementById('search').addEventListener('input', event => {{
    const query = event.target.value.trim().toLowerCase();
    document.querySelectorAll('.flow-node').forEach(node => {{
        node.classList.toggle('match', query.length > 0 && node.textContent.toLowerCase().includes(query));
    }});
}});

document.querySelectorAll('.flow-node').forEach(node => {{
    node.addEventListener('click', () => node.classList.toggle('selected'));
}});

viewport.addEventListener('mousedown', event => {{
    dragging = true;
    startX = event.clientX - translateX;
    startY = event.clientY - translateY;
    viewport.classList.add('dragging');
}});
window.addEventListener('mousemove', event => {{
    if (!dragging) return;
    translateX = event.clientX - startX;
    translateY = event.clientY - startY;
    applyTransform();
}});
window.addEventListener('mouseup', () => {{ dragging = false; viewport.classList.remove('dragging'); }});
viewport.addEventListener('wheel', event => {{
    event.preventDefault();
    const factor = event.deltaY < 0 ? 1.1 : 0.9;
    scale *= factor;
    applyTransform();
}}, {{ passive: false }});
window.addEventListener('load', initialView);
window.addEventListener('resize', initialView);
</script>
</body>
</html>"""

        destination.write_text(document, encoding="utf-8")

        if open_browser:
            webbrowser.open(destination.as_uri())

        return destination

    def _calculate_positions(self, flow_diagram: FlowDiagram) -> dict[str, tuple[float, float]]:
        ranks: dict[str, int] = {flow_diagram.entry_node: 0}
        outgoing: dict[str, list[FlowEdge]] = defaultdict(list)

        for edge in flow_diagram.edges:
            outgoing[edge.source].append(edge)

        queue: deque[str] = deque([flow_diagram.entry_node])
        visit_count: dict[str, int] = defaultdict(int)

        while queue:
            source = queue.popleft()
            source_rank = ranks.get(source, 0)

            for edge in outgoing[source]:
                if edge.label.upper() in self.BACK_EDGE_LABELS:
                    continue

                proposed_rank = source_rank + 1
                current_rank = ranks.get(edge.target, -1)

                if proposed_rank > current_rank:
                    ranks[edge.target] = proposed_rank
                    visit_count[edge.target] += 1

                    if visit_count[edge.target] <= len(flow_diagram.nodes):
                        queue.append(edge.target)

        next_rank = max(ranks.values(), default=0) + 1

        for node_id in flow_diagram.nodes:
            if node_id not in ranks:
                ranks[node_id] = next_rank
                next_rank += 1

        ranked_nodes: dict[int, list[str]] = defaultdict(list)

        for node_id, rank in ranks.items():
            ranked_nodes[rank].append(node_id)

        positions: dict[str, tuple[float, float]] = {}
        widest_count = max((len(items) for items in ranked_nodes.values()), default=1)
        canvas_center = self.MARGIN + ((widest_count - 1) * (self.NODE_WIDTH + self.HORIZONTAL_GAP) + self.NODE_WIDTH) / 2

        for rank in sorted(ranked_nodes):
            node_ids = self._ordered_rank_nodes(
                ranked_nodes[rank],
                flow_diagram,
                ranks,
                positions,
            )
            row_width = (len(node_ids) - 1) * (self.NODE_WIDTH + self.HORIZONTAL_GAP) + self.NODE_WIDTH
            start_x = canvas_center - row_width / 2
            y = self.MARGIN + rank * (self.DECISION_HEIGHT + self.VERTICAL_GAP)

            for index, node_id in enumerate(node_ids):
                x = start_x + index * (self.NODE_WIDTH + self.HORIZONTAL_GAP)
                positions[node_id] = (x, y)

        self._position_terminal_error_branches(
            flow_diagram,
            positions,
        )
        self._position_loop_exit_terminals(
            flow_diagram,
            positions,
        )

        return positions

    def _position_terminal_error_branches(
        self,
        flow_diagram: FlowDiagram,
        positions: dict[str, tuple[float, float]],
    ) -> None:
        """Place error branches beside decisions and normal flow below."""

        outgoing: dict[str, list[FlowEdge]] = defaultdict(list)

        for edge in flow_diagram.edges:
            outgoing[edge.source].append(edge)

        for decision_id, decision_node in flow_diagram.nodes.items():
            if decision_node.node_type.upper() not in self.DECISION_TYPES:
                continue

            decision_x, decision_y = positions[decision_id]
            decision_edges = outgoing.get(decision_id, [])

            error_edge = None
            continuation_edge = None

            for edge in decision_edges:
                target = flow_diagram.nodes[edge.target]

                if edge.label.upper() == "TRUE" and target.node_type.upper() == "RAISE":
                    error_edge = edge
                elif edge.label.upper() in {"FALSE", "NEXT"}:
                    continuation_edge = edge

            if error_edge is None or continuation_edge is None:
                continue

            side_x = decision_x + self.DECISION_WIDTH + self.HORIZONTAL_GAP
            positions[error_edge.target] = (
                side_x,
                decision_y + (self.DECISION_HEIGHT - self.NODE_HEIGHT) / 2,
            )

            continuation_x, continuation_y = positions[continuation_edge.target]
            positions[continuation_edge.target] = (
                decision_x,
                continuation_y,
            )

            for terminal_edge in outgoing.get(error_edge.target, []):
                terminal = flow_diagram.nodes[terminal_edge.target]

                if terminal.node_type.upper() == "END":
                    positions[terminal_edge.target] = (
                        side_x,
                        decision_y + self.DECISION_HEIGHT + self.VERTICAL_GAP,
                    )

    def _position_loop_exit_terminals(
        self,
        flow_diagram: FlowDiagram,
        positions: dict[str, tuple[float, float]],
    ) -> None:
        """Place normal loop exits outside the loop body at lower-right.

        A loop header can have a normal exit directly to an END terminator while
        one or more body nodes return to the header through Repeat/Loop/Back
        edges.  Leaving that END on its ordinary rank can place it inside the
        visual loop field.  Move the END beyond the right-most body node and
        down alongside the lowest returning body node so the exit can travel
        cleanly from the loop header's right side into the top of the END.

        This is layout-only; graph topology and edge semantics are unchanged.
        """

        outgoing: dict[str, list[FlowEdge]] = defaultdict(list)
        returning_to: dict[str, list[str]] = defaultdict(list)

        for edge in flow_diagram.edges:
            outgoing[edge.source].append(edge)
            if edge.label.upper() in self.BACK_EDGE_LABELS:
                returning_to[edge.target].append(edge.source)

        for loop_header, return_sources in returning_to.items():
            if loop_header not in positions:
                continue

            exit_edges = [
                edge
                for edge in outgoing.get(loop_header, [])
                if edge.label.upper() not in self.BACK_EDGE_LABELS
                and flow_diagram.nodes[edge.target].node_type.upper() == "END"
            ]
            if not exit_edges:
                continue

            body_sources = [
                node_id
                for node_id in return_sources
                if node_id in positions
            ]
            if not body_sources:
                continue

            # Ignore the END nodes themselves when determining the occupied
            # right edge; otherwise a previously-ranked END can push itself
            # further right on repeated layout calls.
            excluded_end_ids = {edge.target for edge in exit_edges}
            right_edge = max(
                positions[node_id][0] + self._node_width(node)
                for node_id, node in flow_diagram.nodes.items()
                if node_id in positions and node_id not in excluded_end_ids
            )
            lowest_return_center = max(
                positions[node_id][1] + self._node_height(flow_diagram.nodes[node_id]) / 2
                for node_id in body_sources
            )

            for offset_index, exit_edge in enumerate(exit_edges):
                terminal_x = right_edge + 40.0 + offset_index * (self.NODE_WIDTH + 40.0)
                terminal_y = lowest_return_center + offset_index * (self.NODE_HEIGHT + 20.0)
                positions[exit_edge.target] = (terminal_x, terminal_y)

    def _ordered_rank_nodes(
        self,
        node_ids: list[str],
        flow_diagram: FlowDiagram,
        ranks: dict[str, int],
        positioned: dict[str, tuple[float, float]],
    ) -> list[str]:
        """Order a rank by predecessor position to reduce connector crossings.

        Nodes reached from the same decision are ordered Yes/True to the left
        and No/False to the right.  This keeps branch targets close to their
        source and prevents unrelated terminal nodes from sitting between them.
        """

        incoming: dict[str, list[FlowEdge]] = defaultdict(list)
        for edge in flow_diagram.edges:
            if edge.label.upper() not in self.BACK_EDGE_LABELS:
                incoming[edge.target].append(edge)

        branch_order = {
            "TRUE": -2,
            "YES": -2,
            "ITERATE": -2,
            "BODY": -1,
            "FALSE": 2,
            "NO": 2,
            "NEXT": 1,
        }

        def key(node_id: str) -> tuple[float, int, tuple[int, str]]:
            candidates: list[tuple[float, int]] = []
            for edge in incoming.get(node_id, []):
                if edge.source not in positioned:
                    continue
                source = flow_diagram.nodes[edge.source]
                source_x, _ = positioned[edge.source]
                source_center = source_x + self._node_width(source) / 2
                candidates.append((source_center, branch_order.get(edge.label.upper(), 0)))

            if not candidates:
                return (float("inf"), 0, self._node_sort_key(node_id))

            predecessor_x = sum(item[0] for item in candidates) / len(candidates)
            branch_hint = min(item[1] for item in candidates)
            return (predecessor_x, branch_hint, self._node_sort_key(node_id))

        return sorted(node_ids, key=key)

    def _node_sort_key(self, node_id: str) -> tuple[int, str]:
        digits = "".join(character for character in node_id if character.isdigit())
        return (int(digits) if digits else 0, node_id)

    def _calculate_canvas_size(self, positions: dict[str, tuple[float, float]]) -> tuple[int, int]:
        maximum_x = max((x for x, _ in positions.values()), default=0)
        maximum_y = max((y for _, y in positions.values()), default=0)
        width = int(maximum_x + self.NODE_WIDTH + self.MARGIN)
        height = int(maximum_y + self.DECISION_HEIGHT + self.MARGIN)
        return max(width, 700), max(height, 500)

    def _render_nodes(self, flow_diagram: FlowDiagram, positions: dict[str, tuple[float, float]]) -> str:
        fragments: list[str] = []

        for node_id, node in flow_diagram.nodes.items():
            x, y = positions[node_id]
            fragments.append(self._render_node(node, x, y))

        return "".join(fragments)

    def _render_node(self, node: FlowNode, x: float, y: float) -> str:
        node_type = node.node_type.upper()
        label_lines = self._wrap_label(node.label, 30)
        safe_id = html.escape(node.node_id)
        title = html.escape(f"{node.node_type} | Line {node.line} | {node.node_id}")
        text = self._render_multiline_text(label_lines, x + self.NODE_WIDTH / 2, y + self._node_height(node) / 2 - 7)
        metadata_y = y + self._node_height(node) - 13
        metadata = html.escape(f"Line {node.line} · {node.node_id}")

        if node_type in self.TERMINATOR_TYPES:
            shape = (
                f'<rect class="shape" x="{x}" y="{y}" width="{self.NODE_WIDTH}" '
                f'height="{self.NODE_HEIGHT}" rx="32" ry="32"></rect>'
            )
        elif node_type in self.DECISION_TYPES:
            center_x = x + self.DECISION_WIDTH / 2
            center_y = y + self.DECISION_HEIGHT / 2
            points = (
                f"{center_x},{y} {x + self.DECISION_WIDTH},{center_y} "
                f"{center_x},{y + self.DECISION_HEIGHT} {x},{center_y}"
            )
            shape = f'<polygon class="shape" points="{points}"></polygon>'
        elif node_type in self.INPUT_OUTPUT_TYPES:
            inset = 24
            points = (
                f"{x + inset},{y} {x + self.NODE_WIDTH},{y} "
                f"{x + self.NODE_WIDTH - inset},{y + self.NODE_HEIGHT} {x},{y + self.NODE_HEIGHT}"
            )
            shape = f'<polygon class="shape" points="{points}"></polygon>'
        elif node_type in self.SUBROUTINE_TYPES:
            shape = (
                f'<rect class="shape" x="{x}" y="{y}" width="{self.NODE_WIDTH}" height="{self.NODE_HEIGHT}"></rect>'
                f'<line class="shape" x1="{x + 12}" y1="{y}" x2="{x + 12}" y2="{y + self.NODE_HEIGHT}"></line>'
                f'<line class="shape" x1="{x + self.NODE_WIDTH - 12}" y1="{y}" x2="{x + self.NODE_WIDTH - 12}" y2="{y + self.NODE_HEIGHT}"></line>'
            )
        else:
            shape = (
                f'<rect class="shape" x="{x}" y="{y}" width="{self.NODE_WIDTH}" '
                f'height="{self.NODE_HEIGHT}" rx="4" ry="4"></rect>'
            )

        return (
            f'<g class="flow-node" data-node-id="{safe_id}"><title>{title}</title>'
            f'{shape}{text}<text class="metadata" x="{x + self.NODE_WIDTH / 2}" y="{metadata_y}">{metadata}</text></g>'
        )

    def _render_edges(self, flow_diagram: FlowDiagram, positions: dict[str, tuple[float, float]]) -> str:
        fragments: list[str] = []
        routing = self._edge_routing_offsets(flow_diagram, positions)
        shared_return_groups = self._shared_return_groups(flow_diagram, positions)
        shared_return_followers = {
            member
            for group in shared_return_groups.values()
            for member in group[1:]
        }

        for edge_index, edge in enumerate(flow_diagram.edges):
            points = self._edge_route_points(
                flow_diagram,
                edge,
                edge_index,
                positions,
                routing,
            )
            path = "M " + " L ".join(f"{x} {y}" for x, y in points)
            label = (
                ""
                if edge_index in shared_return_followers
                else self._display_edge_label(
                    edge.label,
                    source_node_type=flow_diagram.nodes[edge.source].node_type,
                )
            )
            label_x, label_y = self._edge_label_position(points)

            edge_class = "flow-edge shared-return-follower" if edge_index in shared_return_followers else "flow-edge"
            fragments.append(f'<path class="{edge_class}" d="{path}"></path>')

            if label:
                safe_label = html.escape(label)
                label_width = max(30, len(label) * 7 + 12)
                fragments.append(
                    f'<g class="edge-label"><rect x="{label_x - label_width / 2}" y="{label_y - 9}" '
                    f'width="{label_width}" height="18" rx="3"></rect>'
                    f'<text x="{label_x}" y="{label_y}">{safe_label}</text></g>'
                )

        return "".join(fragments)

    def _edge_anchor_sides(
        self,
        flow_diagram: FlowDiagram,
        edge: FlowEdge,
        positions: dict[str, tuple[float, float]],
    ) -> tuple[str, str]:
        source = flow_diagram.nodes[edge.source]
        target = flow_diagram.nodes[edge.target]
        sx, sy = positions[edge.source]
        tx, ty = positions[edge.target]
        source_width = self._node_width(source)
        source_height = self._node_height(source)
        target_width = self._node_width(target)
        target_height = self._node_height(target)
        source_center_x = sx + source_width / 2
        source_center_y = sy + source_height / 2
        target_center_x = tx + target_width / 2
        target_center_y = ty + target_height / 2

        terminal_side = self._terminal_entry_side(
            flow_diagram, edge, positions
        )

        is_side_error_branch = (
            source.node_type.upper() in self.DECISION_TYPES
            and target.node_type.upper() == "RAISE"
            and edge.label.upper() in {"TRUE", "YES"}
        )
        if is_side_error_branch:
            return "right", terminal_side or "left"

        is_loop_exit_to_end = (
            target.node_type.upper() == "END"
            and any(
                candidate.target == edge.source
                and candidate.label.upper() in self.BACK_EDGE_LABELS
                for candidate in flow_diagram.edges
            )
        )
        if is_loop_exit_to_end:
            return "right", terminal_side or "top"

        is_back_edge = (
            edge.label.upper() in self.BACK_EDGE_LABELS
            or target_center_y <= source_center_y
        )
        if is_back_edge:
            return "left", terminal_side or "left"

        label = edge.label.upper()
        if source.node_type.upper() in self.DECISION_TYPES and label in {
            "TRUE", "YES", "FALSE", "NO"
        }:
            role = self._decision_chain_role(flow_diagram, edge.source)
            is_true = label in {"TRUE", "YES"}

            # AST-aware branch presentation:
            # * a top-level if/else split uses opposite left/right exits so the
            #   two subtrees immediately receive separate visual regions;
            # * an else-if decision keeps the FALSE continuation on the
            #   vertical spine and sends the local TRUE/action branch sideways.
            if role == "nested":
                source_side = "left" if is_true else "bottom"
            elif role == "root":
                source_side = "left" if is_true else "right"
            else:
                # A standalone/local decision should use the vertex that
                # naturally faces its branch target.  This is especially
                # important for loop-body checks where a Yes branch directly
                # below the rhombus should own the bottom vertex, leaving the
                # left vertex available for a Repeat/back-edge.
                delta_x = target_center_x - source_center_x
                delta_y = target_center_y - source_center_y
                if abs(delta_x) > abs(delta_y) * 1.35:
                    source_side = "right" if delta_x > 0 else "left"
                else:
                    source_side = "bottom" if delta_y >= 0 else "top"

            return source_side, terminal_side or "top"

        if source.node_type.upper() in self.DECISION_TYPES:
            delta_x = target_center_x - source_center_x
            if delta_x < -source_width * 0.18:
                return "left", terminal_side or "top"
            if delta_x > source_width * 0.18:
                return "right", terminal_side or "top"

        if target_center_y > source_center_y:
            return "bottom", terminal_side or "top"

        if target_center_x >= source_center_x:
            return "right", terminal_side or "left"
        return "left", terminal_side or "right"

    def _decision_chain_role(
        self,
        flow_diagram: FlowDiagram,
        decision_id: str,
    ) -> str:
        """Classify a decision by its position in an encoded if/else-if tree.

        The flow encoder represents ``else if`` as a FALSE edge from one
        decision node to the next.  That topology mirrors the AST closely
        enough for the visualiser to distinguish the primary split from nested
        continuation checks without altering the graph itself.
        """

        incoming_false = False
        outgoing_false_to_decision = False

        for candidate in flow_diagram.edges:
            label = candidate.label.upper()
            if label not in {"FALSE", "NO"}:
                continue
            if candidate.target == decision_id:
                source = flow_diagram.nodes.get(candidate.source)
                if source and source.node_type.upper() in self.DECISION_TYPES:
                    incoming_false = True
            if candidate.source == decision_id:
                target = flow_diagram.nodes.get(candidate.target)
                if target and target.node_type.upper() in self.DECISION_TYPES:
                    outgoing_false_to_decision = True

        if incoming_false:
            return "nested"
        if outgoing_false_to_decision:
            return "root"
        return "standalone"

    def _terminal_entry_side(
        self,
        flow_diagram: FlowDiagram,
        edge: FlowEdge,
        positions: dict[str, tuple[float, float]],
    ) -> str | None:
        """Allocate distinct approach sides when several paths share an END.

        The closest/most central incoming path owns the top entry. Remaining
        paths use the left and right sides according to their spatial origin;
        any additional path uses the bottom approach. This keeps terminal
        convergence readable and prevents several independent AST branches
        from collapsing onto one connector anchor.
        """

        target = flow_diagram.nodes[edge.target]
        if target.node_type.upper() != "END":
            return None

        incoming = [
            candidate
            for candidate in flow_diagram.edges
            if candidate.target == edge.target
            and candidate.label.upper() not in self.BACK_EDGE_LABELS
            and candidate.source in positions
        ]
        if len(incoming) <= 1:
            return None

        target_x, target_y = positions[edge.target]
        target_center_x = target_x + self._node_width(target) / 2
        target_center_y = target_y + self._node_height(target) / 2

        def source_center(candidate: FlowEdge) -> tuple[float, float]:
            node = flow_diagram.nodes[candidate.source]
            x, y = positions[candidate.source]
            return (
                x + self._node_width(node) / 2,
                y + self._node_height(node) / 2,
            )

        # First reserve the top connection for the nearest path whose horizontal
        # displacement from END is smallest.  In a typical if/else-if tree this
        # is the deepest branch, which should visually terminate directly.
        top_edge = min(
            incoming,
            key=lambda candidate: (
                abs(source_center(candidate)[1] - target_center_y),
                abs(source_center(candidate)[0] - target_center_x),
            ),
        )
        assignments: dict[int, str] = {id(top_edge): "top"}
        remaining = [candidate for candidate in incoming if candidate is not top_edge]

        left_candidates = [
            candidate
            for candidate in remaining
            if source_center(candidate)[0] < target_center_x
        ]
        right_candidates = [
            candidate
            for candidate in remaining
            if source_center(candidate)[0] >= target_center_x
        ]

        if left_candidates:
            left_edge = min(
                left_candidates,
                key=lambda candidate: abs(source_center(candidate)[1] - target_center_y),
            )
            assignments[id(left_edge)] = "left"
            remaining.remove(left_edge)

        if right_candidates:
            right_candidates = [candidate for candidate in right_candidates if candidate in remaining]
            if right_candidates:
                right_edge = min(
                    right_candidates,
                    key=lambda candidate: abs(source_center(candidate)[1] - target_center_y),
                )
                assignments[id(right_edge)] = "right"
                remaining.remove(right_edge)

        # Extra convergence paths take the bottom. Multiple extras can still be
        # separated by the existing target-anchor offset lanes.
        for candidate in remaining:
            assignments[id(candidate)] = "bottom"

        return assignments.get(id(edge))

    def _edge_route_points(
        self,
        flow_diagram: FlowDiagram,
        edge: FlowEdge,
        edge_index: int,
        positions: dict[str, tuple[float, float]],
        routing: dict[int, dict[str, float]] | None = None,
    ) -> list[tuple[float, float]]:
        """Return an orthogonal route whose segments avoid every node box."""

        routing = routing or self._edge_routing_offsets(flow_diagram, positions)
        route = routing.get(edge_index, {})
        source = flow_diagram.nodes[edge.source]
        target = flow_diagram.nodes[edge.target]
        natural_source_side, natural_target_side = self._edge_anchor_sides(
            flow_diagram, edge, positions
        )
        source_side = str(route.get("source_side") or natural_source_side)
        target_side = str(route.get("target_side") or natural_target_side)
        start = self._edge_anchor_point(
            source, positions[edge.source], source_side, route.get("source_offset", 0.0)
        )
        end = self._edge_anchor_point(
            target, positions[edge.target], target_side, route.get("target_offset", 0.0)
        )
        start_lead = self._outward_point(start, source_side, self.EDGE_ROUTE_LEAD)
        end_lead = self._outward_point(end, target_side, self.EDGE_ROUTE_LEAD)
        obstacles = self._node_obstacle_rectangles(flow_diagram, positions)

        terminal_side = self._terminal_entry_side(flow_diagram, edge, positions)
        if target.node_type.upper() == "END" and terminal_side is not None:
            middle = self._terminal_convergence_route(
                flow_diagram,
                edge,
                positions,
                start_lead,
                end_lead,
                terminal_side,
                obstacles,
                route,
            )
            if middle:
                return self._simplify_route([start, *middle, end])

        # Equivalent same-target Repeat/Loop/Back paths should visibly merge
        # into one return trunk, not merely overlap for the last few pixels at
        # the target.  Route each branch directly to the same outer corridor at
        # its own source height; the union of those paths is one continuous
        # directed trunk back to the loop header.
        shared_return_member = any(
            edge_index in indexes
            for indexes in self._shared_return_groups(flow_diagram, positions).values()
        )
        if shared_return_member and target_side in {"left", "right"}:
            if target_side == "left":
                min_left = min((item[0] for item in obstacles), default=min(start_lead[0], end_lead[0]))
                corridor_x = max(20.0, min_left - 38.0 - route.get("loop_offset", 0.0))
            else:
                max_right = max((item[2] for item in obstacles), default=max(start_lead[0], end_lead[0]))
                corridor_x = max_right + 38.0 + route.get("loop_offset", 0.0)

            source_join = (corridor_x, start_lead[1])
            target_join = (corridor_x, end_lead[1])
            middle = [start_lead, source_join, target_join, end_lead]
            return self._simplify_route([start, *middle, end])

        is_back_edge = (
            edge.label.upper() in self.BACK_EDGE_LABELS
            or positions[edge.target][1] <= positions[edge.source][1]
        )
        if is_back_edge:
            # When attachment allocation has selected an inward-facing source
            # midpoint and a top/bottom target vertex, prefer the clear local
            # orthogonal route.  Forcing every return through the far-left loop
            # corridor can create a visible crossing with the loop's Yes/body
            # branch even though an unused midpoint provides a crossing-free
            # path (Algorithm 27 is the canonical example).
            local_middle = []
            if source_side in {"left", "right"} and target_side in {"top", "bottom"}:
                local_middle = self._orthogonal_obstacle_route(
                    start_lead, end_lead, obstacles, route, prefer_left=False
                )

            if local_middle:
                middle = local_middle
            else:
                min_left = min((item[0] for item in obstacles), default=min(start_lead[0], end_lead[0]))
                left_corridor = max(20.0, min_left - 38.0 - route.get("loop_offset", 0.0))
                corridor_point = (left_corridor, (start_lead[1] + end_lead[1]) / 2)
                first_leg = self._orthogonal_obstacle_route(
                    start_lead, corridor_point, obstacles, route, prefer_left=False
                )
                second_leg = self._orthogonal_obstacle_route(
                    corridor_point, end_lead, obstacles, route, prefer_left=False
                )
                if first_leg and second_leg:
                    middle = [*first_leg, *second_leg[1:]]
                else:
                    middle = self._orthogonal_obstacle_route(
                        start_lead, end_lead, obstacles, route, prefer_left=True
                    )
        else:
            middle = self._orthogonal_obstacle_route(
                start_lead, end_lead, obstacles, route, prefer_left=False
            )
        if not middle:
            middle = [start_lead, end_lead]

        return self._simplify_route([start, *middle, end])

    def _terminal_convergence_route(
        self,
        flow_diagram: FlowDiagram,
        edge: FlowEdge,
        positions: dict[str, tuple[float, float]],
        start_lead: tuple[float, float],
        end_lead: tuple[float, float],
        target_side: str,
        obstacles: list[tuple[float, float, float, float]],
        route: dict[str, float],
    ) -> list[tuple[float, float]]:
        """Route independent branch terminals to END without shared trunks.

        Each assigned END side receives its own corridor.  Left-side arrivals
        use a near-left corridor; an extra bottom arrival uses a farther-left
        corridor before travelling below the END.  Right arrivals use the
        corresponding outer-right space, while the top arrival remains the
        direct/deep branch.  This mirrors the visible AST branch ownership and
        keeps convergence paths separate until they reach the terminator.
        """

        node_lefts = [positions[node_id][0] for node_id in flow_diagram.nodes]
        node_rights = [
            positions[node_id][0] + self._node_width(node)
            for node_id, node in flow_diagram.nodes.items()
        ]
        min_left = min(node_lefts, default=min(start_lead[0], end_lead[0]))
        max_right = max(node_rights, default=max(start_lead[0], end_lead[0]))

        near_left = max(20.0, min_left - 10.0)
        far_left = max(20.0, min_left - 40.0)
        far_right = max_right + 40.0

        if target_side == "bottom":
            return [
                start_lead,
                (far_left, start_lead[1]),
                (far_left, end_lead[1]),
                end_lead,
            ]

        if target_side == "left":
            return [
                start_lead,
                (near_left, start_lead[1]),
                (near_left, end_lead[1]),
                end_lead,
            ]

        if target_side == "right":
            return [
                start_lead,
                (far_right, start_lead[1]),
                (far_right, end_lead[1]),
                end_lead,
            ]

        # The top entry is intentionally reserved for the closest/deepest
        # branch. Use the obstacle router so it takes the shortest clear local
        # route rather than joining one of the outer terminal corridors.
        direct = self._orthogonal_obstacle_route(
            start_lead, end_lead, obstacles, route, prefer_left=False
        )
        return direct or [start_lead, end_lead]

    def _edge_anchor_point(
        self,
        node: FlowNode,
        position: tuple[float, float],
        side: str,
        offset: float = 0.0,
    ) -> tuple[float, float]:
        x, y = position
        width = self._node_width(node)
        height = self._node_height(node)
        if side in {"left", "right"}:
            limit = min(self.EDGE_MAX_ANCHOR_OFFSET, height * 0.38)
            offset = max(-limit, min(limit, offset))
            if side == "left":
                return (x, y + height / 2 + offset)
            return (x + width, y + height / 2 + offset)

        limit = min(self.EDGE_MAX_ANCHOR_OFFSET, width * 0.38)
        offset = max(-limit, min(limit, offset))
        if side == "top":
            return (x + width / 2 + offset, y)
        return (x + width / 2 + offset, y + height)

    @staticmethod
    def _outward_point(
        point: tuple[float, float],
        side: str,
        distance: float,
    ) -> tuple[float, float]:
        x, y = point
        if side == "left":
            return (x - distance, y)
        if side == "right":
            return (x + distance, y)
        if side == "top":
            return (x, y - distance)
        return (x, y + distance)

    def _node_obstacle_rectangles(
        self,
        flow_diagram: FlowDiagram,
        positions: dict[str, tuple[float, float]],
    ) -> list[tuple[float, float, float, float]]:
        clearance = self.EDGE_NODE_CLEARANCE
        rectangles: list[tuple[float, float, float, float]] = []
        for node_id, node in flow_diagram.nodes.items():
            x, y = positions[node_id]
            width = self._node_width(node)
            height = self._node_height(node)
            rectangles.append((
                x - clearance,
                y - clearance,
                x + width + clearance,
                y + height + clearance,
            ))
        return rectangles

    def _orthogonal_obstacle_route(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        obstacles: list[tuple[float, float, float, float]],
        route: dict[str, float],
        prefer_left: bool = False,
    ) -> list[tuple[float, float]]:
        """Find a shortest orthogonal route on obstacle-boundary guide lines."""

        xs = {float(start[0]), float(end[0])}
        ys = {float(start[1]), float(end[1])}
        for left, top, right, bottom in obstacles:
            xs.update((left, right))
            ys.update((top, bottom))

        min_left = min((item[0] for item in obstacles), default=min(start[0], end[0]))
        max_right = max((item[2] for item in obstacles), default=max(start[0], end[0]))
        left_corridor = max(20.0, min_left - 38.0 - route.get("loop_offset", 0.0))
        right_corridor = max_right + 38.0 + route.get("side_offset", 0.0)
        xs.update((left_corridor, right_corridor))
        ys.add((start[1] + end[1]) / 2 + route.get("mid_offset", 0.0))

        xs_sorted = sorted(xs)
        ys_sorted = sorted(ys)

        def point_clear(point: tuple[float, float]) -> bool:
            x, y = point
            for left, top, right, bottom in obstacles:
                if left + 0.1 < x < right - 0.1 and top + 0.1 < y < bottom - 0.1:
                    return False
            return True

        def segment_clear(a: tuple[float, float], b: tuple[float, float]) -> bool:
            x1, y1 = a
            x2, y2 = b
            if abs(x1 - x2) < 0.001:
                low, high = sorted((y1, y2))
                for left, top, right, bottom in obstacles:
                    if left + 0.1 < x1 < right - 0.1 and max(low, top + 0.1) < min(high, bottom - 0.1):
                        return False
                return True
            if abs(y1 - y2) < 0.001:
                low, high = sorted((x1, x2))
                for left, top, right, bottom in obstacles:
                    if top + 0.1 < y1 < bottom - 0.1 and max(low, left + 0.1) < min(high, right - 0.1):
                        return False
                return True
            return False

        points = {(x, y) for x in xs_sorted for y in ys_sorted if point_clear((x, y))}
        points.add(start)
        points.add(end)
        rows: dict[float, list[tuple[float, float]]] = defaultdict(list)
        cols: dict[float, list[tuple[float, float]]] = defaultdict(list)
        for point in points:
            rows[point[1]].append(point)
            cols[point[0]].append(point)

        adjacency: dict[tuple[float, float], list[tuple[tuple[float, float], str, float]]] = defaultdict(list)
        for row_points in rows.values():
            row_points.sort()
            for first, second in zip(row_points, row_points[1:]):
                if segment_clear(first, second):
                    distance = abs(second[0] - first[0])
                    adjacency[first].append((second, "H", distance))
                    adjacency[second].append((first, "H", distance))
        for col_points in cols.values():
            col_points.sort(key=lambda point: point[1])
            for first, second in zip(col_points, col_points[1:]):
                if segment_clear(first, second):
                    distance = abs(second[1] - first[1])
                    adjacency[first].append((second, "V", distance))
                    adjacency[second].append((first, "V", distance))

        queue: list[tuple[float, tuple[float, float], str]] = [(0.0, start, "")]
        best: dict[tuple[tuple[float, float], str], float] = {(start, ""): 0.0}
        previous: dict[tuple[tuple[float, float], str], tuple[tuple[float, float], str] | None] = {(start, ""): None}
        final_state = None

        while queue:
            cost, point, orientation = heapq.heappop(queue)
            state = (point, orientation)
            if cost != best.get(state):
                continue
            if point == end:
                final_state = state
                break
            for neighbour, next_orientation, distance in adjacency.get(point, []):
                bend = self.EDGE_BEND_PENALTY if orientation and orientation != next_orientation else 0.0
                left_bias = 0.0
                if prefer_left:
                    left_bias = max(0.0, neighbour[0] - left_corridor) * 0.015
                next_cost = cost + distance + bend + left_bias
                next_state = (neighbour, next_orientation)
                if next_cost < best.get(next_state, float("inf")):
                    best[next_state] = next_cost
                    previous[next_state] = state
                    heapq.heappush(queue, (next_cost, neighbour, next_orientation))

        if final_state is None:
            return []

        reversed_points: list[tuple[float, float]] = []
        state = final_state
        while state is not None:
            reversed_points.append(state[0])
            state = previous.get(state)
        return list(reversed(reversed_points))

    @staticmethod
    def _simplify_route(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
        cleaned: list[tuple[float, float]] = []
        for point in points:
            if cleaned and abs(point[0] - cleaned[-1][0]) < 0.001 and abs(point[1] - cleaned[-1][1]) < 0.001:
                continue
            cleaned.append(point)
        if len(cleaned) < 3:
            return cleaned
        simplified = [cleaned[0]]
        for index in range(1, len(cleaned) - 1):
            previous = simplified[-1]
            current = cleaned[index]
            following = cleaned[index + 1]
            vertical = abs(previous[0] - current[0]) < 0.001 and abs(current[0] - following[0]) < 0.001
            horizontal = abs(previous[1] - current[1]) < 0.001 and abs(current[1] - following[1]) < 0.001
            if not (vertical or horizontal):
                simplified.append(current)
        simplified.append(cleaned[-1])
        return simplified

    @staticmethod
    def _edge_label_position(points: list[tuple[float, float]]) -> tuple[float, float]:
        best = None
        for first, second in zip(points, points[1:]):
            length = abs(second[0] - first[0]) + abs(second[1] - first[1])
            horizontal = abs(first[1] - second[1]) < 0.001
            rank = (1 if horizontal else 0, length)
            if best is None or rank > best[0]:
                best = (rank, first, second)
        if best is None:
            return points[0]
        _, first, second = best
        x = (first[0] + second[0]) / 2
        y = (first[1] + second[1]) / 2
        return (x, y - 9 if abs(first[1] - second[1]) < 0.001 else y)

    def _shared_return_groups(
        self,
        flow_diagram: FlowDiagram,
        positions: dict[str, tuple[float, float]],
    ) -> dict[tuple[str, str, str], list[int]]:
        """Group equivalent back-edges that may share one visible return trunk.

        Multiple Repeat/Loop/Back paths that return to the same target and the
        same target side represent one control-flow convergence.  They remain
        distinct canonical edges, but visual routing may merge them into one
        directed trunk.  The first member is chosen as the source closest to
        the target so lower branches naturally join that trunk from below.
        """

        grouped: dict[tuple[str, str, str], list[int]] = defaultdict(list)
        for index, edge in enumerate(flow_diagram.edges):
            label = edge.label.upper()
            if label not in self.BACK_EDGE_LABELS:
                continue
            source_side, target_side = self._edge_anchor_sides(
                flow_diagram, edge, positions
            )
            grouped[(edge.target, target_side, "REPEAT")].append(index)

        result: dict[tuple[str, str, str], list[int]] = {}
        for key, indexes in grouped.items():
            if len(indexes) < 2:
                continue
            target_y = positions[key[0]][1]
            ordered = sorted(
                indexes,
                key=lambda item: (
                    abs(positions[flow_diagram.edges[item].source][1] - target_y),
                    positions[flow_diagram.edges[item].source][1],
                    item,
                ),
            )
            result[key] = ordered
        return result

    def _edge_routing_offsets(
        self,
        flow_diagram: FlowDiagram,
        positions: dict[str, tuple[float, float]],
    ) -> dict[int, dict[str, float]]:
        """Assign small deterministic lanes so orthogonal connectors do not stack.

        This is visual-only routing metadata. It does not change graph topology,
        edge direction, labels, node placement, or any study/scoring artefact.
        """

        routes: dict[int, dict[str, float]] = {
            index: {
                "source_offset": 0.0,
                "target_offset": 0.0,
                "mid_offset": 0.0,
                "loop_offset": 0.0,
                "side_offset": 0.0,
            }
            for index in range(len(flow_diagram.edges))
        }

        forward_indexes: list[int] = []
        back_indexes: list[int] = []
        side_indexes: list[int] = []

        for index, edge in enumerate(flow_diagram.edges):
            source = flow_diagram.nodes[edge.source]
            target = flow_diagram.nodes[edge.target]
            _, source_y = positions[edge.source]
            _, target_y = positions[edge.target]

            is_side_error_branch = (
                source.node_type.upper() in self.DECISION_TYPES
                and target.node_type.upper() == "RAISE"
                and edge.label.upper() == "TRUE"
            )

            if is_side_error_branch:
                side_indexes.append(index)
            elif target_y > source_y:
                forward_indexes.append(index)
            else:
                back_indexes.append(index)

        # Allocate node attachment points in two stages.  Every shape gets its
        # four canonical primary anchors before any fractional edge position is
        # introduced.  For decision rhombuses those anchors are the four true
        # vertices; for rectangular/process-style nodes they are the four edge
        # midpoints.  Yes/No branches leaving a decision have first claim on
        # rhombus vertices, then other branches/connections use the remaining
        # vertices.  Only excess attachments fall back to fractional positions.
        # Equivalent same-target Repeat/Loop/Back returns count as one logical
        # target attachment because they intentionally converge into one trunk.
        shared_return_groups = self._shared_return_groups(flow_diagram, positions)
        shared_target_group_by_index: dict[int, tuple[str, str, str]] = {}
        for group_key, indexes in shared_return_groups.items():
            for index in indexes:
                shared_target_group_by_index[index] = group_key

        horizontal_lanes: dict[tuple[float, float], list[int]] = defaultdict(list)
        attachments_by_node: dict[str, dict[tuple, dict[str, object]]] = defaultdict(dict)

        def node_center(node_id: str) -> tuple[float, float]:
            node = flow_diagram.nodes[node_id]
            x, y = positions[node_id]
            return (
                x + self._node_width(node) / 2,
                y + self._node_height(node) / 2,
            )

        def attachment_priority(node_id: str, index: int, endpoint: str) -> int:
            node = flow_diagram.nodes[node_id]
            edge = flow_diagram.edges[index]
            if node.node_type.upper() in self.DECISION_TYPES and endpoint == "source":
                label=edge.label.upper()
                if label in {"TRUE", "YES", "FALSE", "NO", "ITERATE"}:
                    return 0
                # A LOOP_DECISION NEXT edge is the loop-exit/No branch even
                # though the canonical graph keeps the neutral NEXT label.
                if node.node_type.upper()=="LOOP_DECISION" and label=="NEXT":
                    return 0
                return 1
            return 2

        def add_attachment(
            node_id: str,
            logical_key: tuple,
            index: int,
            endpoint: str,
            natural_side: str,
            other_center: tuple[float, float],
        ) -> None:
            bucket = attachments_by_node[node_id]
            item = bucket.get(logical_key)
            if item is None:
                item = {
                    "members": [],
                    "natural_side": natural_side,
                    "other_centres": [],
                    "priority": attachment_priority(node_id, index, endpoint),
                    "tie": index,
                }
                bucket[logical_key] = item
            item["members"].append((index, endpoint))
            item["other_centres"].append(other_center)
            item["priority"] = min(
                int(item["priority"]), attachment_priority(node_id, index, endpoint)
            )
            item["tie"] = min(int(item["tie"]), index)

        for index, edge in enumerate(flow_diagram.edges):
            source_side, target_side = self._edge_anchor_sides(
                flow_diagram, edge, positions
            )
            source_center = node_center(edge.source)
            target_center = node_center(edge.target)

            add_attachment(
                edge.source,
                ("edge", index, "source"),
                index,
                "source",
                source_side,
                target_center,
            )

            shared_key = shared_target_group_by_index.get(index)
            target_key = (
                ("shared-return", shared_key)
                if shared_key is not None
                else ("edge", index, "target")
            )
            add_attachment(
                edge.target,
                target_key,
                index,
                "target",
                target_side,
                source_center,
            )

        side_vectors = {
            "left": (-1.0, 0.0),
            "right": (1.0, 0.0),
            "top": (0.0, -1.0),
            "bottom": (0.0, 1.0),
        }
        side_order = ("top", "right", "bottom", "left")

        for node_id, logical_map in attachments_by_node.items():
            node = flow_diagram.nodes[node_id]
            center_x, center_y = node_center(node_id)
            attachments = list(logical_map.values())

            def averaged_other(item: dict[str, object]) -> tuple[float, float]:
                centres = list(item["other_centres"])
                return (
                    sum(point[0] for point in centres) / len(centres),
                    sum(point[1] for point in centres) / len(centres),
                )

            def facing_side(item: dict[str, object]) -> str:
                """Return the current shape side that most directly faces its peer.

                Direction is normalised by this node's dimensions rather than
                centre-to-centre angle alone.  Thus two nodes whose boxes overlap
                horizontally but are vertically separated prefer top/bottom
                anchors even when their centres are slightly diagonal.
                """
                other_x, other_y = averaged_other(item)
                dx = other_x - center_x
                dy = other_y - center_y
                nx = abs(dx) / max(1.0, self._node_width(node) / 2)
                ny = abs(dy) / max(1.0, self._node_height(node) / 2)
                if nx > ny:
                    return "right" if dx >= 0 else "left"
                return "bottom" if dy >= 0 else "top"

            def side_score(item: dict[str, object], side: str) -> float:
                other_x, other_y = averaged_other(item)
                dx = other_x - center_x
                dy = other_y - center_y
                length = max(1.0, (dx * dx + dy * dy) ** 0.5)
                vx, vy = side_vectors[side]
                geometry = (dx / length) * vx + (dy / length) * vy
                # Facing the peer is the dominant geometric preference.  The
                # legacy/natural side is only a light tie-breaker; it must not
                # pull a connector onto the opposite side of the node.
                facing_bonus = 3.5 if side == facing_side(item) else 0.0
                natural_bonus = 0.25 if side == item["natural_side"] else 0.0
                return facing_bonus + natural_bonus + geometry

            ordered = sorted(
                attachments,
                key=lambda item: (
                    int(item["priority"]),
                    int(item["tie"]),
                ),
            )

            used_primary_sides: set[str] = set()
            assigned_by_side: dict[str, list[dict[str, object]]] = defaultdict(list)

            for item in ordered:
                if len(used_primary_sides) < 4:
                    available = [side for side in side_order if side not in used_primary_sides]
                    natural = str(item["natural_side"])
                    facing = facing_side(item)
                    # Yes/No (including loop-exit NEXT) departures retain their
                    # semantic branch side.  All other attachments first prefer
                    # the primary side physically facing the connected node.
                    decision_branch = (
                        node.node_type.upper() in self.DECISION_TYPES
                        and int(item["priority"]) == 0
                        and any(endpoint == "source" for _, endpoint in item["members"])
                    )
                    shared_return_source = any(
                        endpoint == "source" and index in shared_target_group_by_index
                        for index, endpoint in item["members"]
                    )
                    if (decision_branch or shared_return_source) and natural in available:
                        chosen = natural
                    elif facing in available:
                        chosen = facing
                    else:
                        chosen = max(
                            available,
                            key=lambda side: (side_score(item, side), -side_order.index(side)),
                        )
                    used_primary_sides.add(chosen)
                    item["primary"] = True
                else:
                    # All canonical vertices/midpoints are occupied.  Excess
                    # connectors may now use a fractional point, preferring the
                    # geometrically/naturally appropriate edge.
                    chosen = max(
                        side_order,
                        key=lambda side: (
                            side_score(item, side)
                            - 0.35 * len(assigned_by_side[side]),
                            -side_order.index(side),
                        ),
                    )
                    item["primary"] = False

                item["assigned_side"] = chosen
                assigned_by_side[chosen].append(item)
                for index, endpoint in item["members"]:
                    routes[index][f"{endpoint}_side"] = chosen

            # Keep the first/canonical attachment exactly at the vertex or edge
            # midpoint (offset 0).  Only excess attachments on the same edge get
            # fractional offsets, ordered by the physical position of the route.
            for side, side_items in assigned_by_side.items():
                if len(side_items) <= 1:
                    continue

                primary = next((item for item in side_items if item.get("primary")), side_items[0])
                primary_order = (
                    averaged_other(primary)[1]
                    if side in {"left", "right"}
                    else averaged_other(primary)[0]
                )
                extras = [item for item in side_items if item is not primary]
                extras.sort(
                    key=lambda item: (
                        averaged_other(item)[1]
                        if side in {"left", "right"}
                        else averaged_other(item)[0],
                        int(item["tie"]),
                    )
                )

                dimension = (
                    self._node_height(node)
                    if side in {"left", "right"}
                    else self._node_width(node)
                )
                limit = min(self.EDGE_MAX_ANCHOR_OFFSET, dimension * 0.38)
                spacing = min(self.EDGE_ANCHOR_SPACING, max(8.0, limit / max(1, len(extras))))
                below_count = 0
                above_count = 0
                for item in extras:
                    item_order = (
                        averaged_other(item)[1]
                        if side in {"left", "right"}
                        else averaged_other(item)[0]
                    )
                    if item_order < primary_order:
                        above_count += 1
                        offset = -min(limit, spacing * above_count)
                    else:
                        below_count += 1
                        offset = min(limit, spacing * below_count)
                    for index, endpoint in item["members"]:
                        routes[index][f"{endpoint}_offset"] = offset

        for index in forward_indexes:
            edge = flow_diagram.edges[index]
            source = flow_diagram.nodes[edge.source]
            target = flow_diagram.nodes[edge.target]
            _, sy = positions[edge.source]
            _, ty = positions[edge.target]
            start_y = sy + self._node_height(source)
            end_y = ty
            horizontal_lanes[(round(start_y, 3), round(end_y, 3))].append(index)

        for indexes in horizontal_lanes.values():
            offsets = self._centred_offsets(len(indexes), self.EDGE_MID_LANE_SPACING)
            for index, offset in zip(indexes, offsets):
                routes[index]["mid_offset"] = offset

        back_by_corridor: dict[tuple[float, float], list[int]] = defaultdict(list)
        for index in back_indexes:
            edge = flow_diagram.edges[index]
            sx, _ = positions[edge.source]
            tx, _ = positions[edge.target]
            back_by_corridor[(round(min(sx, tx), 3), round(max(sx, tx), 3))].append(index)

        for indexes in back_by_corridor.values():
            for lane, index in enumerate(indexes):
                routes[index]["loop_offset"] = lane * self.EDGE_MID_LANE_SPACING

        # Equivalent returns share the same outer corridor and the same target
        # anchor, creating one trunk after their paths converge.
        for indexes in shared_return_groups.values():
            shared_loop_offset = min(routes[index]["loop_offset"] for index in indexes)
            shared_target_offset = routes[indexes[0]]["target_offset"]
            for index in indexes:
                routes[index]["loop_offset"] = shared_loop_offset
                routes[index]["target_offset"] = shared_target_offset

        side_by_source: dict[str, list[int]] = defaultdict(list)
        for index in side_indexes:
            side_by_source[flow_diagram.edges[index].source].append(index)

        for indexes in side_by_source.values():
            offsets = self._centred_offsets(len(indexes), self.EDGE_MID_LANE_SPACING)
            for index, offset in zip(indexes, offsets):
                routes[index]["side_offset"] = offset

        # Crossing-aware primary-anchor refinement.  The semantic priority
        # above still decides who receives the four true vertices/midpoints,
        # and fractional anchors remain forbidden until those are exhausted.
        # Once that invariant is satisfied, an attachment that currently
        # crosses another connector may move to an *unused* primary side when
        # doing so strictly reduces crossings.  Yes/No decision departures are
        # left alone so their branch presentation remains stable.
        def proper_segment_crossing(
            first_a: tuple[float, float],
            first_b: tuple[float, float],
            second_a: tuple[float, float],
            second_b: tuple[float, float],
        ) -> bool:
            first_vertical = abs(first_a[0] - first_b[0]) < 0.001
            second_vertical = abs(second_a[0] - second_b[0]) < 0.001
            if first_vertical == second_vertical:
                return False

            if first_vertical:
                vertical_a, vertical_b = first_a, first_b
                horizontal_a, horizontal_b = second_a, second_b
            else:
                vertical_a, vertical_b = second_a, second_b
                horizontal_a, horizontal_b = first_a, first_b

            vertical_x = vertical_a[0]
            horizontal_y = horizontal_a[1]
            vertical_min, vertical_max = sorted((vertical_a[1], vertical_b[1]))
            horizontal_min, horizontal_max = sorted((horizontal_a[0], horizontal_b[0]))

            # Strict inequalities deliberately ignore shared endpoints and
            # T-junctions at a node anchor.  We only penalise visible interior
            # crossings between independent orthogonal segments.
            return (
                horizontal_min < vertical_x < horizontal_max
                and vertical_min < horizontal_y < vertical_max
            )

        def crossing_count(edge_index: int) -> int:
            edge = flow_diagram.edges[edge_index]
            candidate_points = self._edge_route_points(
                flow_diagram, edge, edge_index, positions, routes
            )
            count = 0
            for other_index, other_edge in enumerate(flow_diagram.edges):
                if other_index == edge_index:
                    continue
                other_points = self._edge_route_points(
                    flow_diagram, other_edge, other_index, positions, routes
                )
                if any(
                    proper_segment_crossing(a, b, c, d)
                    for a, b in zip(candidate_points, candidate_points[1:])
                    for c, d in zip(other_points, other_points[1:])
                ):
                    count += 1
            return count

        for node_id, logical_map in attachments_by_node.items():
            primary_items = [
                item for item in logical_map.values() if bool(item.get("primary"))
            ]
            used_sides = {str(item["assigned_side"]) for item in primary_items}

            for item in sorted(primary_items, key=lambda value: int(value["tie"])):
                # Preserve the deliberately assigned Yes/No rhombus vertices.
                if int(item["priority"]) == 0:
                    continue
                members = list(item["members"])
                if len(members) != 1:
                    # Shared logical attachments must remain shared.
                    continue

                edge_index, endpoint = members[0]
                current_side = str(item["assigned_side"] )
                current_crossings = crossing_count(edge_index)
                if current_crossings == 0:
                    continue

                alternatives = [
                    side
                    for side in side_order
                    if side == current_side or side not in used_sides
                ]
                best_side = current_side
                best_crossings = current_crossings

                for candidate_side in alternatives:
                    if candidate_side == current_side:
                        continue
                    routes[edge_index][f"{endpoint}_side"] = candidate_side
                    candidate_crossings = crossing_count(edge_index)
                    if candidate_crossings < best_crossings:
                        best_side = candidate_side
                        best_crossings = candidate_crossings

                routes[edge_index][f"{endpoint}_side"] = best_side
                if best_side != current_side:
                    used_sides.discard(current_side)
                    used_sides.add(best_side)
                    item["assigned_side"] = best_side

        return routes

    def _centred_offsets(self, count: int, spacing: float) -> list[float]:
        if count <= 1:
            return [0.0] * max(count, 0)
        midpoint = (count - 1) / 2
        return [(index - midpoint) * spacing for index in range(count)]

    def _attachment_offsets(
        self,
        node: FlowNode,
        side: str,
        count: int,
    ) -> list[float]:
        """Return unique ordered anchor offsets confined to one shape edge.

        Left/right edges vary vertically; top/bottom edges vary horizontally.
        The usable span is deliberately kept away from corners so draw.io and
        SVG renderers retain clean arrow joins even when a node has many
        incident connectors.
        """

        if count <= 1:
            return [0.0] * max(count, 0)

        dimension = (
            self._node_height(node)
            if side in {"left", "right"}
            else self._node_width(node)
        )
        limit = min(self.EDGE_MAX_ANCHOR_OFFSET, dimension * 0.38)
        step = min(self.EDGE_ANCHOR_SPACING, (2 * limit) / (count - 1))
        return self._centred_offsets(count, step)

    def _clamp_anchor_offset(self, offset: float) -> float:
        return max(-self.EDGE_MAX_ANCHOR_OFFSET, min(self.EDGE_MAX_ANCHOR_OFFSET, offset))

    def _node_width(self, node: FlowNode) -> int:
        if node.node_type.upper() in self.DECISION_TYPES:
            return self.DECISION_WIDTH
        return self.NODE_WIDTH

    def _node_height(self, node: FlowNode) -> int:
        if node.node_type.upper() in self.DECISION_TYPES:
            return self.DECISION_HEIGHT
        return self.NODE_HEIGHT

    def _display_edge_label(
        self,
        label: str,
        source_node_type: str | None = None,
    ) -> str:
        normalized = label.upper()
        if normalized == "NEXT":
            # LOOP_DECISION fallthrough is the exhausted/false branch.  Keep
            # ordinary sequential NEXT connectors unlabelled, but show the
            # loop exit explicitly so it mirrors the visible Yes branch.
            return "No" if (source_node_type or "").upper() == "LOOP_DECISION" else ""

        translations = {
            "TRUE": "Yes",
            "FALSE": "No",
            "ITERATE": "Yes",
            "BODY": "",
            "LOOP": "Repeat",
            "CATCH": "Exception",
        }
        return translations.get(normalized, label.title())

    def _wrap_label(self, label: str, width: int) -> list[str]:
        words = label.split()
        lines: list[str] = []
        current = ""

        for word in words:
            candidate = word if not current else f"{current} {word}"

            if len(candidate) <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines[:3] or [""]

    def _render_multiline_text(self, lines: list[str], x: float, center_y: float) -> str:
        line_height = 16
        first_y = center_y - ((len(lines) - 1) * line_height / 2)
        fragments = [f'<text x="{x}" y="{first_y}">']

        for index, line in enumerate(lines):
            dy = 0 if index == 0 else line_height
            fragments.append(f'<tspan x="{x}" dy="{dy}">{html.escape(line)}</tspan>')

        fragments.append("</text>")
        return "".join(fragments)
