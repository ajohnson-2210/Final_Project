"""Python AST serialisation and adjacency-list generation."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from itertools import count
from typing import Any

from aj_parser import AdjacencyList


@dataclass
class PythonASTResult:
    """Contains nested and graph representations of generated Python syntax."""

    tree_document: dict[str, Any]
    adjacency_list: AdjacencyList


class PythonASTBuilder:
    """Builds inspectable AST outputs from generated Python source code."""

    def build(self, source_code: str) -> PythonASTResult:
        syntax_tree = ast.parse(source_code)
        identifiers = count(1)
        nodes: dict[str, dict[str, Any]] = {}
        edges: dict[str, list[str]] = {}

        def visit(node: ast.AST) -> tuple[str, dict[str, Any]]:
            node_id = f"P{next(identifiers)}"
            attributes: dict[str, Any] = {}
            children: list[dict[str, Any]] = []
            child_ids: list[str] = []

            for field_name, value in ast.iter_fields(node):
                if isinstance(value, ast.AST):
                    child_id, child_document = visit(value)
                    child_ids.append(child_id)
                    children.append(
                        {
                            "field": field_name,
                            "node": child_document,
                        }
                    )
                elif isinstance(value, list):
                    list_children: list[dict[str, Any]] = []
                    primitive_values: list[Any] = []

                    for item in value:
                        if isinstance(item, ast.AST):
                            child_id, child_document = visit(item)
                            child_ids.append(child_id)
                            list_children.append(child_document)
                        else:
                            primitive_values.append(item)

                    if list_children:
                        children.append(
                            {
                                "field": field_name,
                                "nodes": list_children,
                            }
                        )

                    if primitive_values:
                        attributes[field_name] = primitive_values
                else:
                    attributes[field_name] = value

            line_number = getattr(node, "lineno", 0)
            nodes[node_id] = {
                "kind": type(node).__name__,
                "line": line_number,
                "attributes": attributes,
            }
            edges[node_id] = child_ids

            document = {
                "node_id": node_id,
                "node_type": type(node).__name__,
                "line": line_number,
                "attributes": attributes,
                "children": children,
            }

            return node_id, document

        root_id, tree_document = visit(syntax_tree)
        adjacency_list = AdjacencyList(
            root_id=root_id,
            nodes=nodes,
            adjacency=edges,
        )
        adjacency_list.validate()

        return PythonASTResult(
            tree_document=tree_document,
            adjacency_list=adjacency_list,
        )
