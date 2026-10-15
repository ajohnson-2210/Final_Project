"""Editable draw.io XML export for generated flow diagrams."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree
import html

from flow_diagram import FlowDiagram, FlowEdge, FlowNode
from flow_diagram_visualizer import FlowDiagramVisualizer


class DrawIOFlowExporter:
    """Exports a canonical flow diagram using the HTML visualiser's layout."""

    # Internal visual-layout revision only. This is deliberately independent of
    # the pipeline release version so silent v4.37 routing fixes can refresh
    # existing experimental DrawIO views without invalidating semantic artefacts.
    LAYOUT_REVISION = "v4.37-layout-20260922-1"

    NODE_WIDTH = FlowDiagramVisualizer.NODE_WIDTH
    NODE_HEIGHT = FlowDiagramVisualizer.NODE_HEIGHT
    DECISION_WIDTH = FlowDiagramVisualizer.DECISION_WIDTH
    DECISION_HEIGHT = FlowDiagramVisualizer.DECISION_HEIGHT

    DECISION_TYPES = FlowDiagramVisualizer.DECISION_TYPES
    INPUT_OUTPUT_TYPES = FlowDiagramVisualizer.INPUT_OUTPUT_TYPES
    TERMINATOR_TYPES = FlowDiagramVisualizer.TERMINATOR_TYPES
    SUBROUTINE_TYPES = FlowDiagramVisualizer.SUBROUTINE_TYPES

    def __init__(self) -> None:
        self.layout_engine = FlowDiagramVisualizer()

    def export(
        self,
        flow_diagram: FlowDiagram,
        output_path: str | Path,
    ) -> Path:
        """Write an editable draw.io file and return its absolute path."""

        destination = Path(output_path).resolve()
        self._active_flow_diagram = flow_diagram
        positions = self.layout_engine._calculate_positions(flow_diagram)
        self._routing_offsets = self.layout_engine._edge_routing_offsets(
            flow_diagram,
            positions,
        )
        shared_return_groups = self.layout_engine._shared_return_groups(
            flow_diagram, positions
        )
        self._shared_return_followers = {
            member
            for group in shared_return_groups.values()
            for member in group[1:]
        }
        canvas_width, canvas_height = self.layout_engine._calculate_canvas_size(
            positions
        )

        mxfile = ElementTree.Element(
            "mxfile",
            {
                "host": "app.diagrams.net",
                "modified": "2026-08-04T00:00:00.000Z",
                "agent": "NL to Flow Diagram Encoder Pipeline",
                "version": "24.7.17",
                "type": "device",
                "compressed": "false",
                "nl_fdep_layout_revision": self.LAYOUT_REVISION,
            },
        )

        diagram = ElementTree.SubElement(
            mxfile,
            "diagram",
            {
                "id": "generated-flow-diagram",
                "name": "Generated Flow Diagram",
            },
        )

        model = ElementTree.SubElement(
            diagram,
            "mxGraphModel",
            {
                "dx": str(canvas_width),
                "dy": str(canvas_height),
                "grid": "1",
                "gridSize": "10",
                "guides": "1",
                "tooltips": "1",
                "connect": "1",
                "arrows": "1",
                "fold": "1",
                "page": "0",
                "pageScale": "1",
                "pageWidth": str(canvas_width),
                "pageHeight": str(canvas_height),
                "math": "0",
                "shadow": "0",
                "background": "#ffffff",
            },
        )

        root = ElementTree.SubElement(
            model,
            "root",
        )

        ElementTree.SubElement(
            root,
            "mxCell",
            {
                "id": "0",
            },
        )

        ElementTree.SubElement(
            root,
            "mxCell",
            {
                "id": "1",
                "parent": "0",
            },
        )

        for node_id, node in flow_diagram.nodes.items():
            self._append_node(
                root=root,
                node=node,
                position=positions[node_id],
            )

        for index, edge in enumerate(
            flow_diagram.edges,
            start=1,
        ):
            self._append_edge(
                root=root,
                flow_diagram=flow_diagram,
                edge=edge,
                index=index,
                positions=positions,
            )

        ElementTree.indent(
            mxfile,
            space="  ",
        )

        xml_document = ElementTree.tostring(
            mxfile,
            encoding="utf-8",
            xml_declaration=True,
        )

        destination.write_bytes(
            xml_document
        )

        return destination

    def _append_node(
        self,
        root: ElementTree.Element,
        node: FlowNode,
        position: tuple[float, float],
    ) -> None:
        x_position, y_position = position
        width, height = self._node_dimensions(
            node
        )

        node_type = node.node_type.upper()
        uses_overlay_label = node_type in self.SUBROUTINE_TYPES

        node_value = self._node_value(
            node
        )

        if uses_overlay_label:
            node_value = ""

        cell = ElementTree.SubElement(
            root,
            "mxCell",
            {
                "id": node.node_id,
                "value": node_value,
                "style": self._node_style(node),
                "vertex": "1",
                "parent": "1",
            },
        )

        ElementTree.SubElement(
            cell,
            "mxGeometry",
            {
                "x": self._number(x_position),
                "y": self._number(y_position),
                "width": self._number(width),
                "height": self._number(height),
                "as": "geometry",
            },
        )

        if uses_overlay_label:
            self._append_overlay_label(
                root=root,
                node=node,
                x_position=x_position,
                y_position=y_position,
                width=width,
                height=height,
            )


    def _append_overlay_label(
        self,
        root: ElementTree.Element,
        node: FlowNode,
        x_position: float,
        y_position: float,
        width: float,
        height: float,
    ) -> None:
        """Place a full-width text cell over inset draw.io shapes."""

        label_cell = ElementTree.SubElement(
            root,
            "mxCell",
            {
                "id": f"{node.node_id}_LABEL",
                "value": self._node_value(node),
                "style": (
                    "text;"
                    "html=1;"
                    "whiteSpace=wrap;"
                    "overflow=hidden;"
                    "align=center;"
                    "verticalAlign=middle;"
                    "fontFamily=Arial;"
                    "fontSize=13;"
                    "fontColor=#111418;"
                    "strokeColor=none;"
                    "fillColor=none;"
                    "spacing=0;"
                    "connectable=0;"
                    "movable=0;"
                    "resizable=0;"
                ),
                "vertex": "1",
                "parent": "1",
            },
        )

        ElementTree.SubElement(
            label_cell,
            "mxGeometry",
            {
                "x": self._number(x_position),
                "y": self._number(y_position),
                "width": self._number(width),
                "height": self._number(height),
                "as": "geometry",
            },
        )

    def _append_edge(
        self,
        root: ElementTree.Element,
        flow_diagram: FlowDiagram,
        edge: FlowEdge,
        index: int,
        positions: dict[str, tuple[float, float]],
    ) -> None:
        visible_label = self._edge_label(
            edge.label,
            source_node_type=flow_diagram.nodes[edge.source].node_type,
        )

        cell = ElementTree.SubElement(
            root,
            "mxCell",
            {
                "id": f"E{index}",
                "value": visible_label,
                "style": self._edge_style(
                    edge=edge,
                    index=index,
                    positions=positions,
                ),
                "edge": "1",
                "parent": "1",
                "source": edge.source,
                "target": edge.target,
            },
        )

        geometry = ElementTree.SubElement(
            cell,
            "mxGeometry",
            {
                "relative": "1",
                "as": "geometry",
            },
        )

        waypoints = self._edge_waypoints(
            flow_diagram=flow_diagram,
            edge=edge,
            index=index,
            positions=positions,
        )

        if waypoints:
            points = ElementTree.SubElement(
                geometry,
                "Array",
                {
                    "as": "points",
                },
            )

            for x_position, y_position in waypoints:
                ElementTree.SubElement(
                    points,
                    "mxPoint",
                    {
                        "x": self._number(x_position),
                        "y": self._number(y_position),
                    },
                )

    def _edge_style(
        self,
        edge: FlowEdge,
        index: int,
        positions: dict[str, tuple[float, float]],
    ) -> str:
        common = (
            "edgeStyle=orthogonalEdgeStyle;"
            "rounded=0;"
            "orthogonalLoop=1;"
            "jettySize=auto;"
            "html=1;"
            "strokeColor=#252a31;"
            "strokeWidth=1.45;"
            "fontFamily=Arial;"
            "fontSize=11;"
            "fontColor=#20242a;"
            "labelBackgroundColor=#ffffff;"
            "endArrow=block;"
            "endSize=9;"
            "endFill=1;"
        )

        if not hasattr(self, "_active_flow_diagram"):
            return common

        flow_diagram = self._active_flow_diagram
        source = flow_diagram.nodes[edge.source]
        target = flow_diagram.nodes[edge.target]
        natural_source_side, natural_target_side = self.layout_engine._edge_anchor_sides(
            flow_diagram, edge, positions
        )
        route = getattr(self, "_routing_offsets", {}).get(index - 1, {})
        source_side = str(route.get("source_side") or natural_source_side)
        target_side = str(route.get("target_side") or natural_target_side)

        def anchor_fraction(node: FlowNode, side: str, offset: float) -> tuple[float, float]:
            width = self.layout_engine._node_width(node)
            height = self.layout_engine._node_height(node)
            if side in {"left", "right"}:
                fraction = max(0.12, min(0.88, 0.5 + offset / height))
                if side == "left":
                    return (0.0, fraction)
                return (1.0, fraction)
            fraction = max(0.12, min(0.88, 0.5 + offset / width))
            if side == "top":
                return (fraction, 0.0)
            return (fraction, 1.0)

        exit_x, exit_y = anchor_fraction(
            source, source_side, route.get("source_offset", 0.0)
        )
        entry_x, entry_y = anchor_fraction(
            target, target_side, route.get("target_offset", 0.0)
        )

        style = (
            common
            + f"exitX={self._number(exit_x)};"
            + f"exitY={self._number(exit_y)};"
            + "exitDx=0;exitDy=0;"
            + f"entryX={self._number(entry_x)};"
            + f"entryY={self._number(entry_y)};"
            + "entryDx=0;entryDy=0;"
        )

        # Secondary members of an equivalent shared-return group remain real
        # source->target edges for round-trip semantics, but their overlapping
        # trunk does not draw a second arrowhead or a duplicate label.
        if index - 1 in getattr(self, "_shared_return_followers", set()):
            style += "endArrow=none;textOpacity=0;"

        return style

    def _node_value(
        self,
        node: FlowNode,
    ) -> str:
        wrapped_lines = self.layout_engine._wrap_label(
            node.label,
            30,
        )

        label = "<br>".join(
            html.escape(line)
            for line in wrapped_lines
        )

        metadata = html.escape(
            f"Line {node.line} · {node.node_id}"
        )

        return (
            '<div style="font-family:Arial;font-size:13px;'
            'line-height:16px;text-align:center;">'
            f"{label}"
            '<div style="margin-top:6px;font-size:10px;'
            f'color:#606874;">{metadata}</div>'
            "</div>"
        )

    def _node_dimensions(
        self,
        node: FlowNode,
    ) -> tuple[float, float]:
        if node.node_type.upper() in self.DECISION_TYPES:
            return (
                self.DECISION_WIDTH,
                self.DECISION_HEIGHT,
            )

        return (
            self.NODE_WIDTH,
            self.NODE_HEIGHT,
        )

    def _node_style(
        self,
        node: FlowNode,
    ) -> str:
        common = (
            "whiteSpace=wrap;"
            "html=1;"
            "align=center;"
            "verticalAlign=middle;"
            "fontFamily=Arial;"
            "fontSize=13;"
            "fontColor=#111418;"
            "strokeColor=#20242a;"
            "strokeWidth=1.6;"
            "fillColor=#ffffff;"
            "spacing=0;"
        )

        node_type = node.node_type.upper()

        if node_type in self.TERMINATOR_TYPES:
            return (
                common
                + "rounded=1;"
                + "arcSize=100;"
            )

        if node_type in self.DECISION_TYPES:
            return (
                common
                + "rhombus;"
                + "perimeter=rhombusPerimeter;"
            )

        if node_type in self.INPUT_OUTPUT_TYPES:
            return (
                common
                + "shape=parallelogram;"
                + "perimeter=parallelogramPerimeter;"
                + "fixedSize=1;"
            )

        if node_type in self.SUBROUTINE_TYPES:
            return (
                common
                + "shape=process;"
                + "size=12;"
                + "overflow=hidden;"
            )

        return (
            common
            + "rounded=1;"
            + "arcSize=8;"
        )

    def _edge_waypoints(
        self,
        flow_diagram: FlowDiagram,
        edge: FlowEdge,
        index: int,
        positions: dict[str, tuple[float, float]],
    ) -> list[tuple[float, float]]:
        points = self.layout_engine._edge_route_points(
            flow_diagram,
            edge,
            index - 1,
            positions,
            getattr(self, "_routing_offsets", None),
        )
        if len(points) <= 2:
            if len(points) == 2:
                first, second = points
                return [((first[0] + second[0]) / 2, (first[1] + second[1]) / 2)]
            return []
        return points[1:-1]

    def _edge_label(
        self,
        label: str,
        source_node_type: str | None = None,
    ) -> str:
        normalised = label.strip().upper()

        if normalised == "NEXT":
            # A LOOP_DECISION's normal fallthrough is its exhausted/false
            # branch.  Render it as No while ordinary sequential NEXT edges
            # remain unlabelled.
            return "No" if (source_node_type or "").upper() == "LOOP_DECISION" else ""

        translations = {
            "TRUE": "Yes",
            "FALSE": "No",
            "ITERATE": "Yes",
            "BODY": "",
            "LOOP": "Repeat",
            "CATCH": "Exception",
        }

        return translations.get(
            normalised,
            label.title(),
        )

    def _number(
        self,
        value: float,
    ) -> str:
        rounded = round(
            value,
            3,
        )

        if rounded.is_integer():
            return str(
                int(rounded)
            )

        return str(
            rounded
        )
