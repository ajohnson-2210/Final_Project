"""Controlled draw.io import for the NL Flow Diagram Encoder Pipeline.

The importer deliberately accepts a constrained convention. Executable draw.io
shapes contain AJ_24038155 Dialect statements. The importer reconstructs a
continuous AJ pseudocode program, which is then passed through the existing
lexer, recursive parser, AST encoder and Python compiler.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from pathlib import Path
from urllib.parse import unquote
import base64
import re
import xml.etree.ElementTree as ElementTree
import zlib


class DrawIOImportError(ValueError):
    """Raised when a draw.io document does not satisfy the controlled convention."""


@dataclass
class DrawIOShape:
    """Represents one executable or structural draw.io vertex."""

    shape_id: str
    label: str
    style: str
    x: float
    y: float
    width: float
    height: float
    parent_id: str | None
    text_only: bool


@dataclass
class DrawIOConnector:
    """Represents one directed draw.io connector."""

    connector_id: str
    source: str
    target: str | None
    label: str


@dataclass
class DrawIOImportResult:
    """Contains the AJ source reconstructed from a draw.io file."""

    pseudocode: str
    shape_count: int
    connector_count: int
    ordered_shape_ids: list[str]
    flow_document: dict | None = None
    is_linear: bool = True


class DrawIOFlowImporter:
    """Imports constrained draw.io diagrams as AJ pseudocode.

    Version 1 supports a single linear executable path:

    Start -> AJ statement -> AJ statement -> End

    Labels may be written directly as AJ statements or prefixed with ``AJ:``.
    Start and End labels are structural and are not emitted as pseudocode.
    """

    START_LABELS = {"START", "BEGIN"}
    END_LABELS = {"END", "STOP", "FINISH"}

    def import_file(self, input_path: Path) -> DrawIOImportResult:
        """Reads and validates a draw.io or draw.io SVG source file."""

        if not input_path.exists():
            raise FileNotFoundError(f"Flow diagram file not found: {input_path.resolve()}")

        source_text = input_path.read_text(encoding="utf-8")
        graph_root = self._extract_graph_model(source_text)
        shapes, connectors = self._read_graph(graph_root)
        ordered_ids, is_linear = self._validate_and_order(shapes, connectors)

        if is_linear:
            pseudocode_lines = self._build_pseudocode(ordered_ids, shapes)
            pseudocode = "\n".join(pseudocode_lines)
            flow_document = None
        else:
            pseudocode = ""
            flow_document = self._build_graph_flow_document(
                shapes=shapes,
                connectors=connectors,
                ordered_ids=ordered_ids,
            )

        return DrawIOImportResult(
            pseudocode=pseudocode,
            shape_count=len(shapes),
            connector_count=len(connectors),
            ordered_shape_ids=ordered_ids,
            flow_document=flow_document,
            is_linear=is_linear,
        )

    def _extract_graph_model(self, source_text: str) -> ElementTree.Element:
        """Returns an mxGraphModel from plain or compressed draw.io XML."""

        try:
            root = ElementTree.fromstring(source_text)
        except ElementTree.ParseError as error:
            raise DrawIOImportError(f"The selected file is not valid XML: {error}") from error

        graph_model = self._find_graph_model(root)

        if graph_model is not None:
            return graph_model

        diagram = root.find(".//diagram")

        if diagram is not None and diagram.text:
            decoded_xml = self._decode_diagram_text(diagram.text.strip())

            try:
                decoded_root = ElementTree.fromstring(decoded_xml)
            except ElementTree.ParseError as error:
                raise DrawIOImportError(
                    "The compressed draw.io diagram could not be decoded."
                ) from error

            graph_model = self._find_graph_model(decoded_root)

            if graph_model is not None:
                return graph_model

        embedded_xml = self._extract_embedded_drawio_xml(source_text)

        if embedded_xml is not None:
            return self._extract_graph_model(embedded_xml)

        raise DrawIOImportError("No mxGraphModel was found in the selected draw.io file.")

    @staticmethod
    def _find_graph_model(root: ElementTree.Element) -> ElementTree.Element | None:
        if root.tag.endswith("mxGraphModel"):
            return root

        for element in root.iter():
            if element.tag.endswith("mxGraphModel"):
                return element

        return None

    @staticmethod
    def _decode_diagram_text(encoded_text: str) -> str:
        compressed_bytes = base64.b64decode(encoded_text)
        decompressed_bytes = zlib.decompress(compressed_bytes, -15)
        return unquote(decompressed_bytes.decode("utf-8"))

    @staticmethod
    def _extract_embedded_drawio_xml(source_text: str) -> str | None:
        patterns = [
            r"content=\"([^\"]*%3Cmxfile[^\"]+)\"",
            r"data-mxgraph=\"([^\"]+)\"",
        ]

        for pattern in patterns:
            match = re.search(pattern, source_text, flags=re.IGNORECASE)

            if match is not None:
                candidate = unescape(match.group(1))
                candidate = unquote(candidate)

                if "<mxfile" in candidate or "<mxGraphModel" in candidate:
                    return candidate

        return None

    def _read_graph(
        self,
        graph_model: ElementTree.Element,
    ) -> tuple[dict[str, DrawIOShape], list[DrawIOConnector]]:
        shapes: dict[str, DrawIOShape] = {}
        connectors: list[DrawIOConnector] = []
        parent_lookup: dict[str, str | None] = {}

        for cell in graph_model.iter():
            if not cell.tag.endswith("mxCell"):
                continue

            cell_id = cell.get("id")

            if not cell_id:
                continue

            parent_lookup[cell_id] = cell.get("parent")

            if cell.get("vertex") == "1":
                label = self._clean_label(cell.get("value", ""))
                style = cell.get("style", "")
                x, y, width, height = self._read_geometry(cell)
                text_only = self._is_text_only_style(style)
                shapes[cell_id] = DrawIOShape(
                    shape_id=cell_id,
                    label=label,
                    style=style,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    parent_id=cell.get("parent"),
                    text_only=text_only,
                )

            if cell.get("edge") == "1":
                source = cell.get("source")
                target = cell.get("target")

                if source:
                    connectors.append(
                        DrawIOConnector(
                            connector_id=cell_id,
                            source=source,
                            target=target,
                            label=self._clean_label(cell.get("value", "")),
                        )
                    )

        if not shapes:
            raise DrawIOImportError("The draw.io file contains no flowchart shapes.")

        connectors = self._merge_edge_labels(
            shapes=shapes,
            connectors=connectors,
        )

        shapes = self._merge_overlaid_text_labels(
            shapes=shapes,
            parent_lookup=parent_lookup,
        )

        return shapes, connectors

    def _merge_edge_labels(
        self,
        shapes: dict[str, DrawIOShape],
        connectors: list[DrawIOConnector],
    ) -> list[DrawIOConnector]:
        """Moves draw.io edge-label child vertices onto their connector."""

        connector_lookup = {
            connector.connector_id: connector
            for connector in connectors
        }

        for shape in shapes.values():
            if "edgelabel" not in shape.style.lower():
                continue

            parent_id = shape.parent_id
            connector = connector_lookup.get(parent_id or "")

            if connector is not None and shape.label:
                connector.label = shape.label.strip().upper()

        return connectors

    @staticmethod
    def _read_geometry(
        cell: ElementTree.Element,
    ) -> tuple[float, float, float, float]:
        for child in cell:
            if child.tag.endswith("mxGeometry"):
                return (
                    float(child.get("x", 0)),
                    float(child.get("y", 0)),
                    float(child.get("width", 0)),
                    float(child.get("height", 0)),
                )

        return 0.0, 0.0, 0.0, 0.0

    @staticmethod
    def _is_text_only_style(style: str) -> bool:
        style_parts = {
            part.strip().lower()
            for part in style.split(";")
            if part.strip()
        }

        if "text" in style_parts:
            return True

        if any(part.startswith("edgelabel") for part in style_parts):
            return True

        return (
            "strokecolor=none" in style_parts
            and "fillcolor=none" in style_parts
        )

    def _merge_overlaid_text_labels(
        self,
        shapes: dict[str, DrawIOShape],
        parent_lookup: dict[str, str | None],
    ) -> dict[str, DrawIOShape]:
        """Associates separate draw.io text labels with underlying shapes."""

        absolute_bounds: dict[str, tuple[float, float, float, float]] = {}

        def calculate_bounds(shape_id: str) -> tuple[float, float, float, float]:
            existing = absolute_bounds.get(shape_id)

            if existing is not None:
                return existing

            shape = shapes[shape_id]
            absolute_x = shape.x
            absolute_y = shape.y
            parent_id = shape.parent_id

            if parent_id in shapes:
                parent_x, parent_y, _, _ = calculate_bounds(parent_id)
                absolute_x += parent_x
                absolute_y += parent_y

            bounds = (
                absolute_x,
                absolute_y,
                shape.width,
                shape.height,
            )
            absolute_bounds[shape_id] = bounds
            return bounds

        for shape_id in shapes:
            calculate_bounds(shape_id)

        text_shape_ids: set[str] = set()

        for text_shape in list(shapes.values()):
            if not text_shape.text_only or not text_shape.label:
                continue

            text_x, text_y, text_width, text_height = absolute_bounds[
                text_shape.shape_id
            ]
            centre_x = text_x + (text_width / 2)
            centre_y = text_y + (text_height / 2)

            candidates: list[tuple[float, DrawIOShape]] = []

            for target_shape in shapes.values():
                if target_shape.shape_id == text_shape.shape_id:
                    continue

                if target_shape.text_only:
                    continue

                if target_shape.style.strip().lower() == "group":
                    continue

                target_x, target_y, target_width, target_height = absolute_bounds[
                    target_shape.shape_id
                ]

                contains_centre = (
                    target_x <= centre_x <= target_x + target_width
                    and target_y <= centre_y <= target_y + target_height
                )

                if not contains_centre:
                    continue

                area = target_width * target_height
                candidates.append((area, target_shape))

            if not candidates:
                continue

            candidates.sort(key=lambda item: item[0])
            target_shape = candidates[0][1]

            if not target_shape.label:
                target_shape.label = text_shape.label

            text_shape_ids.add(text_shape.shape_id)

        cleaned_shapes: dict[str, DrawIOShape] = {}

        for shape_id, shape in shapes.items():
            if shape_id in text_shape_ids:
                continue

            if shape.text_only:
                continue

            if shape.style.strip().lower() == "group":
                continue

            cleaned_shapes[shape_id] = shape

        return cleaned_shapes

    @staticmethod
    def _clean_label(raw_label: str) -> str:
        label = re.sub(r"<br\s*/?>", "\n", raw_label, flags=re.IGNORECASE)
        label = re.sub(r"<[^>]+>", "", label)
        label = unescape(label)
        label = label.replace("\xa0", " ")
        label = re.sub(r"[ \t]+", " ", label)
        label = re.sub(r" *\n *", "\n", label)
        return label.strip()

    def _validate_and_order(
        self,
        shapes: dict[str, DrawIOShape],
        connectors: list[DrawIOConnector],
    ) -> tuple[list[str], bool]:
        outgoing: dict[str, list[str]] = {shape_id: [] for shape_id in shapes}
        incoming: dict[str, list[str]] = {shape_id: [] for shape_id in shapes}

        for connector in connectors:
            if connector.source not in shapes:
                continue

            if connector.target not in shapes:
                continue

            outgoing[connector.source].append(connector.target)
            incoming[connector.target].append(connector.source)

        start_ids = [
            shape_id
            for shape_id, shape in shapes.items()
            if self._is_start(shape)
        ]
        end_ids = [
            shape_id
            for shape_id, shape in shapes.items()
            if self._is_end(shape)
        ]

        if len(start_ids) != 1:
            raise DrawIOImportError(
                "Controlled draw.io import requires exactly one Start shape."
            )

        if len(end_ids) != 1:
            raise DrawIOImportError(
                "Controlled draw.io import requires exactly one End shape."
            )

        start_id = start_ids[0]
        end_id = end_ids[0]
        visited: set[str] = set()
        traversal: list[str] = []
        pending: list[str] = [start_id]

        while pending:
            current_id = pending.pop(0)

            if current_id in visited:
                continue

            visited.add(current_id)
            traversal.append(current_id)

            for target_id in outgoing[current_id]:
                if target_id not in visited:
                    pending.append(target_id)

        if end_id not in visited:
            raise DrawIOImportError(
                "The End shape is not reachable from the Start shape."
            )

        executable_shape_ids = {
            shape_id
            for shape_id, shape in shapes.items()
            if shape.label and not shape.text_only
        }
        disconnected = executable_shape_ids.difference(visited)

        if disconnected:
            raise DrawIOImportError(
                "The diagram contains disconnected executable shapes: "
                + ", ".join(sorted(disconnected))
            )

        is_linear = True

        for shape_id in traversal:
            targets = outgoing[shape_id]

            if shape_id == end_id:
                continue

            if len(targets) != 1:
                is_linear = False

        if len(visited) != len(traversal):
            is_linear = False

        edge_count = sum(len(outgoing[shape_id]) for shape_id in traversal)

        if edge_count != max(len(traversal) - 1, 0):
            is_linear = False

        return traversal, is_linear

    def _build_graph_flow_document(
        self,
        shapes: dict[str, DrawIOShape],
        connectors: list[DrawIOConnector],
        ordered_ids: list[str],
    ) -> dict:
        """Builds a canonical compiler-ready graph document."""

        id_lookup = {
            shape_id: f"D{index}"
            for index, shape_id in enumerate(ordered_ids, start=1)
        }
        nodes: dict[str, dict] = {}

        for shape_id in ordered_ids:
            shape = shapes[shape_id]
            node_id = id_lookup[shape_id]
            node_type = self._node_type(shape)
            nodes[node_id] = {
                "node_id": node_id,
                "node_type": node_type,
                "label": shape.label or node_type.title(),
                "line": 0,
                "data": {
                    "drawio_id": shape_id,
                    "style": shape.style,
                    "source_label": shape.label,
                },
            }

        edges: list[dict] = []

        for connector in connectors:
            if connector.source not in id_lookup:
                continue

            source_id = id_lookup[connector.source]

            if connector.target in id_lookup:
                target_id = id_lookup[connector.target]
            else:
                target_id = id_lookup[self._find_end_shape_id(shapes)]

            label = connector.label.strip().upper() or "NEXT"
            edges.append(
                {
                    "source": source_id,
                    "target": target_id,
                    "label": label,
                }
            )

        end_shape_id = self._find_end_shape_id(shapes)
        end_node_id = id_lookup[end_shape_id]
        connected_sources = {edge["source"] for edge in edges}

        for node_id in nodes:
            if node_id == end_node_id:
                continue

            if node_id not in connected_sources:
                edges.append(
                    {
                        "source": node_id,
                        "target": end_node_id,
                        "label": "NEXT",
                    }
                )

        start_shape_id = next(
            shape_id for shape_id, shape in shapes.items() if self._is_start(shape)
        )

        graph_program = {
            "kind": "ProgramNode",
            "line": 1,
            "body": [],
            "execution_model": "STATE_MACHINE",
            "entry_node": id_lookup[start_shape_id],
            "exit_node": end_node_id,
            "nodes": nodes,
            "edges": edges,
        }

        return {
            "format": "NL-FDEP Flow Diagram",
            "version": "1.0",
            "entry_node": id_lookup[start_shape_id],
            "exit_node": end_node_id,
            "nodes": nodes,
            "edges": edges,
            "structured_program": graph_program,
        }

    def _node_type(self, shape: DrawIOShape) -> str:
        if self._is_start(shape):
            return "START"

        if self._is_end(shape):
            return "END"

        if "rhombus" in shape.style.lower():
            return "DECISION"

        label_upper = shape.label.upper()

        if "INPUT" in label_upper or "CHOOSES" in label_upper:
            return "INPUT"

        if "DECLARED" in label_upper or "WINNER" in label_upper:
            return "OUTPUT"

        return "PROCESS"

    def _find_end_shape_id(self, shapes: dict[str, DrawIOShape]) -> str:
        return next(
            shape_id for shape_id, shape in shapes.items() if self._is_end(shape)
        )

    def _build_pseudocode(
        self,
        ordered_ids: list[str],
        shapes: dict[str, DrawIOShape],
    ) -> list[str]:
        pseudocode_lines: list[str] = []

        for shape_id in ordered_ids:
            shape = shapes[shape_id]

            if self._is_start(shape) or self._is_end(shape):
                continue

            statement = shape.label

            if statement.upper().startswith("AJ:"):
                statement = statement[3:].strip()

            if not statement:
                raise DrawIOImportError(
                    f"Executable shape {shape_id} has no AJ statement label."
                )

            statement_lines = [line.strip() for line in statement.splitlines() if line.strip()]
            pseudocode_lines.extend(statement_lines)

        if not pseudocode_lines:
            raise DrawIOImportError("The flow diagram contains no executable AJ statements.")

        return pseudocode_lines

    def _is_start(self, shape: DrawIOShape) -> bool:
        return shape.label.upper() in self.START_LABELS

    def _is_end(self, shape: DrawIOShape) -> bool:
        return shape.label.upper() in self.END_LABELS
