"""Lightweight evidence extractors for study scoring.

These utilities do not re-interpret AJ semantics and are deliberately conservative.
They extract structural signatures from already-generated artefacts so the study layer
can detect missing/spurious constructs and route uncertain cases to human review.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

CONTROL_KINDS = {
    "IfNode",
    "ElseIfNode",
    "WhileNode",
    "ForRangeNode",
    "ForEachNode",
}

EXECUTABLE_KINDS = {
    "AssignmentNode",
    "OutputNode",
    "InputNode",
    "CallNode",
    "CastNode",
    "IsInstanceNode",
    "ImportDirectiveNode",
    "MemberCallNode",
    "AppendNode",
    "InsertNode",
    "RemoveFirstNode",
    "RemoveLastNode",
    "RemoveValueNode",
    "IfNode",
    "ElseIfNode",
    "WhileNode",
    "ForRangeNode",
    "ForEachNode",
    "ReturnNode",
    "BreakNode",
    "StopNode",
    "QuitNode",
    "ContinueNode",
    "RaiseNode",
    "FunctionNode",
    "MethodNode",
    "ConstructorNode",
    "ClassNode",
    "PropertyAssignmentNode",
    "PropertyDeclarationNode",
    "TryCatchNode",
}

DECISION_FLOW_TYPES = {"DECISION", "LOOP_DECISION"}


def _normalise_literal(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return repr(value)
    return f"{type(value).__name__}:{value!r}"


def signature_from_ast_adjacency(document: dict[str, Any]) -> dict[str, Any]:
    """Extract a deterministic multiset signature from ``ast.json``."""
    nodes = document.get("nodes", {})
    if not isinstance(nodes, dict):
        return {"valid": False, "reason": "ast.nodes is not an object"}

    kinds: Counter[str] = Counter()
    operators: Counter[str] = Counter()
    identifiers: Counter[str] = Counter()
    literals: Counter[str] = Counter()

    for node in nodes.values():
        if not isinstance(node, dict):
            continue
        kind = node.get("kind")
        if isinstance(kind, str):
            kinds[kind] += 1
        attributes = node.get("attributes") or {}
        if not isinstance(attributes, dict):
            continue
        operator = attributes.get("operator")
        if isinstance(operator, str):
            operators[operator] += 1
        name = attributes.get("name")
        if isinstance(name, str) and kind in {
            "IdentifierNode", "FunctionNode", "MethodNode", "ClassNode",
            "ParameterNode", "PropertyDeclarationNode"
        }:
            identifiers[name] += 1
        if kind == "LiteralNode" and "value" in attributes:
            literals[_normalise_literal(attributes.get("value"))] += 1

    return {
        "valid": True,
        "node_count": sum(kinds.values()),
        "kinds": dict(sorted(kinds.items())),
        "operators": dict(sorted(operators.items())),
        "identifiers": dict(sorted(identifiers.items())),
        "literals": dict(sorted(literals.items())),
        "executable_node_count": sum(kinds[k] for k in EXECUTABLE_KINDS),
        "decision_count": sum(kinds[k] for k in CONTROL_KINDS),
        "loop_count": sum(kinds[k] for k in {"WhileNode", "ForRangeNode", "ForEachNode"}),
    }


def _walk_structured(value: Any):
    if isinstance(value, dict):
        if isinstance(value.get("kind"), str):
            yield value
        for child in value.values():
            if isinstance(child, (dict, list)):
                yield from _walk_structured(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_structured(child)


def signature_from_structured_program(program: dict[str, Any]) -> dict[str, Any]:
    """Extract the same style of signature from flow ``structured_program``."""
    kinds: Counter[str] = Counter()
    operators: Counter[str] = Counter()
    identifiers: Counter[str] = Counter()
    literals: Counter[str] = Counter()

    for node in _walk_structured(program):
        kind = node.get("kind")
        kinds[kind] += 1
        operator = node.get("operator")
        if isinstance(operator, str):
            operators[operator] += 1
        name = node.get("name")
        if isinstance(name, str) and kind in {
            "IdentifierNode", "FunctionNode", "MethodNode", "ClassNode",
            "ParameterNode", "PropertyDeclarationNode"
        }:
            identifiers[name] += 1
        if kind == "LiteralNode" and "value" in node:
            literals[_normalise_literal(node.get("value"))] += 1

    return {
        "valid": True,
        "node_count": sum(kinds.values()),
        "kinds": dict(sorted(kinds.items())),
        "operators": dict(sorted(operators.items())),
        "identifiers": dict(sorted(identifiers.items())),
        "literals": dict(sorted(literals.items())),
        "executable_node_count": sum(kinds[k] for k in EXECUTABLE_KINDS),
        "decision_count": sum(kinds[k] for k in CONTROL_KINDS),
        "loop_count": sum(kinds[k] for k in {"WhileNode", "ForRangeNode", "ForEachNode"}),
    }


def compare_signatures(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Compare two signatures and report exact structural differences."""
    if not left.get("valid") or not right.get("valid"):
        return {
            "equivalent": False,
            "review_required": True,
            "differences": ["One or both semantic signatures could not be extracted."],
        }

    differences: list[str] = []
    for key in ("kinds", "operators", "identifiers", "literals"):
        if left.get(key) != right.get(key):
            differences.append(f"{key} multiset differs")

    return {
        "equivalent": not differences,
        "review_required": bool(differences),
        "differences": differences,
    }


def flow_graph_validation(flow_document: dict[str, Any]) -> dict[str, Any]:
    """Validate study-relevant graph invariants without replacing the core validator."""
    nodes = flow_document.get("nodes") or {}
    edges = flow_document.get("edges") or []
    entry = flow_document.get("entry_node")
    exit_node = flow_document.get("exit_node")
    issues: list[str] = []
    warnings: list[str] = []

    if entry not in nodes:
        issues.append("entry_node does not reference an existing node")
    if exit_node not in nodes:
        issues.append("exit_node does not reference an existing node")

    outgoing: dict[str, list[dict[str, Any]]] = {node_id: [] for node_id in nodes}
    incoming: dict[str, list[dict[str, Any]]] = {node_id: [] for node_id in nodes}
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if source not in nodes:
            issues.append(f"edge source {source!r} does not exist")
            continue
        if target not in nodes:
            issues.append(f"edge target {target!r} does not exist")
            continue
        outgoing[source].append(edge)
        incoming[target].append(edge)

    if entry in nodes and incoming.get(entry):
        warnings.append("entry node has incoming edge(s)")
    if exit_node in nodes and outgoing.get(exit_node):
        issues.append("exit node has outgoing edge(s)")

    decision_nodes = 0
    loop_nodes = 0
    for node_id, node in nodes.items():
        node_type = node.get("node_type")
        outs = outgoing.get(node_id, [])
        labels = {str(edge.get("label", "")).upper() for edge in outs}
        if node_type in DECISION_FLOW_TYPES:
            decision_nodes += 1
            if len(outs) < 2:
                issues.append(f"decision node {node_id} has fewer than two outgoing paths")
            if node_type == "LOOP_DECISION":
                loop_nodes += 1
                if not ({"TRUE", "ITERATE"} & labels):
                    issues.append(f"loop decision {node_id} has no TRUE/ITERATE body edge")
                if not ({"NEXT", "FALSE", "EXIT"} & labels):
                    issues.append(f"loop decision {node_id} has no identifiable exit edge")

    for node_id, node in nodes.items():
        node_type = str(node.get("node_type", "")).upper()
        outs = outgoing.get(node_id, [])
        if node_type == "BREAK":
            if any(str(edge.get("label", "")).upper() in {"LOOP", "CONTINUE"} for edge in outs):
                issues.append(f"BREAK node {node_id} incorrectly routes back to a loop")
        elif node_type == "CONTINUE":
            if not outs or not all(
                str(edge.get("label", "")).upper() in {"LOOP", "CONTINUE"}
                and nodes.get(edge.get("target"), {}).get("node_type") == "LOOP_DECISION"
                for edge in outs
            ):
                issues.append(f"CONTINUE node {node_id} does not route directly to a loop decision")
        elif node_type in {"RETURN", "RAISE", "STOP", "QUIT"}:
            if any(nodes.get(edge.get("target"), {}).get("node_type") != "END" for edge in outs):
                issues.append(f"terminal node {node_id} has a non-terminal outgoing path")

    loop_back_edges = sum(
        str(edge.get("label", "")).upper() in {"LOOP", "CONTINUE"}
        for edge in edges
    )
    if loop_nodes and loop_back_edges < loop_nodes:
        warnings.append(
            "fewer explicit LOOP/CONTINUE edges than loop-decision nodes; nested/terminal loop structure requires review"
        )

    reachable: set[str] = set()
    if entry in nodes:
        stack = [entry]
        while stack:
            current = stack.pop()
            if current in reachable:
                continue
            reachable.add(current)
            stack.extend(
                edge.get("target") for edge in outgoing.get(current, [])
                if edge.get("target") in nodes
            )
    unreachable = sorted(set(nodes) - reachable)
    if unreachable:
        warnings.append(f"unreachable flow nodes: {', '.join(unreachable)}")

    return {
        "valid": not issues,
        "issues": issues,
        "warnings": warnings,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "decision_node_count": decision_nodes,
        "loop_decision_count": loop_nodes,
        "loop_back_edge_count": loop_back_edges,
        "unreachable_nodes": unreachable,
    }


def _max_loop_nesting(value: Any, depth: int = 0) -> int:
    maximum = depth
    if isinstance(value, dict):
        kind = value.get("kind")
        next_depth = depth + 1 if kind in {"WhileNode", "ForRangeNode", "ForEachNode"} else depth
        maximum = max(maximum, next_depth)
        for child in value.values():
            if isinstance(child, (dict, list)):
                maximum = max(maximum, _max_loop_nesting(child, next_depth))
    elif isinstance(value, list):
        for child in value:
            maximum = max(maximum, _max_loop_nesting(child, depth))
    return maximum


def complexity_from_structured_program(program: dict[str, Any]) -> dict[str, Any]:
    sig = signature_from_structured_program(program)
    decision_count = int(sig.get("decision_count", 0))
    # McCabe-style control-flow approximation for one connected routine/program.
    cyclomatic = 1 + decision_count
    return {
        "cyclomatic_complexity": cyclomatic,
        "decision_count": decision_count,
        "loop_count": int(sig.get("loop_count", 0)),
        "maximum_loop_nesting": _max_loop_nesting(program),
        "ast_executable_nodes": int(sig.get("executable_node_count", 0)),
        "note": "Cyclomatic complexity is reported as 1 + control-decision count for study stratification.",
    }
