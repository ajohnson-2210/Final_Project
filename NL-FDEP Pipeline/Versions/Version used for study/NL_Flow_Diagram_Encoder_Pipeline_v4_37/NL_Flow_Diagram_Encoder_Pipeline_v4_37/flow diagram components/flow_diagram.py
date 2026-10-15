"""Machine-readable flow diagram generation from the AJ abstract syntax tree."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any
import json
import re

from aj_parser import (
    ASTNode,
    AppendNode,
    InsertNode,
    RemoveValueNode,
    AssignmentNode,
    BinaryNode,
    BlockNode,
    BreakNode,
    StopNode,
    QuitNode,
    CallNode,
    CastNode,
    IsInstanceNode,
    ClassNode,
    ConstructorNode,
    MethodNode,
    PropertyAssignmentNode,
    PropertyDeclarationNode,
    CommentNode,
    ImportDirectiveNode,
    ContinueNode,
    EmptyLiteralNode,
    ForEachNode,
    ForRangeNode,
    FunctionNode,
    GetNode,
    IdentifierNode,
    IfNode,
    IndexNode,
    MemberAccessNode,
    MemberCallNode,
    RemoveFirstExpressionNode,
    RemoveLastExpressionNode,
    InputNode,
    JoinNode,
    LengthNode,
    ListLiteralNode,
    SetLiteralNode,
    SetOperationNode,
    RandomExpressionNode,
    LiteralNode,
    OutputNode,
    ProgramNode,
    RaiseNode,
    RemoveFirstNode,
    RemoveLastNode,
    ReturnNode,
    TryCatchNode,
    TupleLiteralNode,
    UnaryNode,
    WhileNode,
)


class HumanReadableLabelBuilder:
    """Builds concise plain-English labels from AJ AST operations.

    The visual label explains the operation to a reader who does not need to
    understand AST class names. Node identifiers and line numbers remain
    available separately as diagram metadata.
    """

    OPERATOR_TEXT = {
        "==": "is equal to",
        "!=": "is not equal to",
        "<": "is less than",
        "<=": "is less than or equal to",
        ">": "is greater than",
        ">=": "is greater than or equal to",
        "AND": "and",
        "OR": "or",
        "+": "plus",
        "-": "minus",
        "*": "multiplied by",
        "/": "divided by",
        "%": "modulo",
        "MODULUS": "modulo",
        "INTEGER DIVISION": "integer-divided by",
        "EXP": "raised to the power of",
        "IN": "is contained in",
        "NOT IN": "is not contained in",
        "XOR": "exclusive-or",
        "^": "raised to the power of",
    }

    def statement(self, statement: ASTNode) -> str:
        if isinstance(statement, AssignmentNode):
            return f"Set {self.expression(statement.target)} to {self.expression(statement.value)}"

        if isinstance(statement, PropertyDeclarationNode):
            type_text = f" as {statement.declared_type}" if statement.declared_type else ""
            return f"Declare property {statement.name}{type_text}"

        if isinstance(statement, PropertyAssignmentNode):
            return f"Set {self.expression(statement.target)} to {self.expression(statement.value)}"

        if isinstance(statement, OutputNode):
            return f"Display {self.expression(statement.expression)}"

        if isinstance(statement, InputNode):
            return f"Read input using prompt {self.expression(statement.prompt)}"

        if isinstance(statement, ReturnNode):
            if statement.expression is None:
                return "Return from the function"
            return f"Return {self.expression(statement.expression)}"

        if isinstance(statement, CallNode):
            arguments = ", ".join(self.expression(item) for item in statement.arguments)
            if arguments:
                return f"Call {statement.name} with {arguments}"
            return f"Call {statement.name}"

        if isinstance(statement, MemberCallNode):
            arguments = ", ".join(self.expression(item) for item in statement.arguments)
            target = f"{self.expression(statement.object)}.{statement.member}"
            if arguments:
                return f"Call {target} with {arguments}"
            return f"Call {target}"

        if isinstance(statement, AppendNode):
            return f"Append {self.expression(statement.value)} to {self.expression(statement.collection)}"

        if isinstance(statement, InsertNode):
            return (f"Insert {self.expression(statement.value)} into "
                    f"{self.expression(statement.collection)} at {self.expression(statement.index)}")

        if isinstance(statement, RemoveValueNode):
            return f"Remove {self.expression(statement.value)} from {self.expression(statement.collection)}"

        if isinstance(statement, RemoveFirstNode):
            return f"Remove the first item from {self.expression(statement.collection)}"

        if isinstance(statement, RemoveLastNode):
            return f"Remove the last item from {self.expression(statement.collection)}"

        if isinstance(statement, RaiseNode):
            return f"Raise error {self.expression(statement.expression)}"

        if isinstance(statement, BreakNode):
            return "Exit the current loop"

        if isinstance(statement, QuitNode):
            return "Quit the program"

        if isinstance(statement, ContinueNode):
            return "Continue with the next loop iteration"

        if isinstance(statement, ImportDirectiveNode):
            if statement.directive_type == "IMPORT":
                suffix = f" as {statement.alias}" if statement.alias else ""
                return f"Import module {statement.module}{suffix}"
            imported = ", ".join(statement.names)
            return f"Import {imported} from module {statement.module}"

        if isinstance(statement, CommentNode):
            return statement.text

        if isinstance(statement, ForEachNode):
            return (
                f"For each {statement.variable.name} in "
                f"{self.expression(statement.collection)}"
            )

        if isinstance(statement, ForRangeNode):
            step_text = ""
            if statement.step is not None:
                step_text = f", increasing by {self.expression(statement.step)}"
            return (
                f"For {statement.variable.name} from {self.expression(statement.start)} "
                f"to {self.expression(statement.end)}{step_text}"
            )

        return statement.kind.removesuffix("Node")

    def condition(self, expression: ASTNode, prefix: str = "Is") -> str:
        text = self.expression(expression)
        if text.endswith("?"):
            return text

        comparison_operators = {"==", "!=", "<", "<=", ">", ">=", "IN", "NOT IN"}

        if isinstance(expression, BinaryNode) and expression.operator.upper() in comparison_operators:
            return f"{text[0].upper() + text[1:]}?"

        if prefix.lower() == "while":
            return f"Continue while {text}?"

        return f"{prefix} {text} true?"

    def expression(self, expression: ASTNode | None) -> str:
        if expression is None:
            return "nothing"

        if isinstance(expression, IdentifierNode):
            return expression.name

        if isinstance(expression, LiteralNode):
            if isinstance(expression.value, str):
                return f'"{expression.value}"'
            if expression.value is True:
                return "true"
            if expression.value is False:
                return "false"
            if expression.value is None:
                return "nothing"
            return str(expression.value)

        if isinstance(expression, EmptyLiteralNode):
            return f"an empty {expression.empty_type.lower()}"

        if isinstance(expression, ListLiteralNode):
            items = ", ".join(self.expression(item) for item in expression.items)
            return f"[{items}]"

        if isinstance(expression, SetLiteralNode):
            items = ", ".join(self.expression(item) for item in expression.items)
            return f"set containing {items}" if items else "an empty set"

        if isinstance(expression, SetOperationNode):
            operation = expression.operation.lower()
            return (
                f"the {operation} of {self.expression(expression.left)} and "
                f"{self.expression(expression.right)}"
            )

        if isinstance(expression, RandomExpressionNode):
            if expression.random_type == "BOOLEAN":
                return "a random boolean"
            kind = expression.random_type.lower()
            return (
                f"a random {kind} from {self.expression(expression.minimum)} to "
                f"{self.expression(expression.maximum)}"
            )

        if isinstance(expression, TupleLiteralNode):
            items = ", ".join(self.expression(item) for item in expression.items)
            return f"({items})"

        if isinstance(expression, BinaryNode):
            operator = self.OPERATOR_TEXT.get(expression.operator.upper(), expression.operator)
            return (
                f"{self.expression(expression.left)} {operator} "
                f"{self.expression(expression.right)}"
            )

        if isinstance(expression, UnaryNode):
            operator = expression.operator.upper()
            if operator == "NOT":
                return f"not {self.expression(expression.operand)}"
            if operator == "-":
                return f"negative {self.expression(expression.operand)}"
            return f"{expression.operator} {self.expression(expression.operand)}"

        if isinstance(expression, IndexNode):
            return (
                f"item {self.expression(expression.index)} of "
                f"{self.expression(expression.collection)}"
            )

        if isinstance(expression, MemberAccessNode):
            return (
                f"{expression.member} of "
                f"{self.expression(expression.object)}"
            )

        if isinstance(expression, MemberCallNode):
            arguments = ", ".join(self.expression(item) for item in expression.arguments)
            target = f"{self.expression(expression.object)}.{expression.member}"
            if arguments:
                return f"the result of {target}({arguments})"
            return f"the result of {target}()"

        if isinstance(expression, RemoveFirstExpressionNode):
            return (
                f"remove and return first item from "
                f"{self.expression(expression.collection)}"
            )

        if isinstance(expression, RemoveLastExpressionNode):
            return (
                f"remove and return last item from "
                f"{self.expression(expression.collection)}"
            )

        if isinstance(expression, CastNode):
            return f"{self.expression(expression.expression)} converted to {expression.target_type.lower()}"

        if isinstance(expression, IsInstanceNode):
            targets = " or ".join(name.lower() for name in expression.type_names)
            return f"{self.expression(expression.expression)} is an instance of {targets}"

        if isinstance(expression, CallNode):
            arguments = ", ".join(self.expression(item) for item in expression.arguments)
            if arguments:
                return f"the result of {expression.name}({arguments})"
            return f"the result of {expression.name}()"

        if isinstance(expression, InputNode):
            return f"input prompted by {self.expression(expression.prompt)}"

        if isinstance(expression, LengthNode):
            return f"the length of {self.expression(expression.expression)}"

        if isinstance(expression, JoinNode):
            return (
                f"{self.expression(expression.collection)} joined using "
                f"{self.expression(expression.separator)}"
            )

        if isinstance(expression, GetNode):
            text = (
                f"the value for {self.expression(expression.key)} in "
                f"{self.expression(expression.dictionary)}"
            )
            if expression.default is not None:
                text += f", defaulting to {self.expression(expression.default)}"
            return text

        return expression.kind.removesuffix("Node")


@dataclass
class FlowNode:
    """Represents one executable or structural element in a flow diagram."""

    node_id: str
    node_type: str
    label: str
    line: int
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "label": self.label,
            "line": self.line,
            "data": self.data,
        }


@dataclass
class FlowEdge:
    """Represents a directed connection between two flow nodes."""

    source: str
    target: str
    label: str = "NEXT"

    def to_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "target": self.target,
            "label": self.label,
        }


@dataclass
class FlowDiagram:
    """Serializable flow diagram and structured program representation."""

    entry_node: str
    exit_node: str
    nodes: dict[str, FlowNode]
    edges: list[FlowEdge]
    structured_program: dict[str, Any]
    format_name: str = "NL-FDEP Flow Diagram"
    version: str = "1.0"

    def __post_init__(self) -> None:
        """Remove canonical COMMENT lines from executable flow topology.

        The canonical structured program is authoritative for whether a source
        line is executable.  This also sanitises legacy/cached graphs where a
        canonical COMMENT line was previously mis-typed as a PROCESS node.
        """
        canonical_comments = self._canonical_comments(self.structured_program)
        comment_lines = set(canonical_comments)
        protected_ids = {self.entry_node, self.exit_node}
        excluded_node_ids = {
            node_id
            for node_id, node in self.nodes.items()
            if node_id not in protected_ids
            and (
                str(node.node_type).upper() == "COMMENT"
                or self._normalise_source_line(node.line) in comment_lines
            )
        }
        if excluded_node_ids:
            self.nodes = {
                node_id: node
                for node_id, node in self.nodes.items()
                if node_id not in excluded_node_ids
            }
            self.edges = self._bypass_excluded_nodes(
                self.edges, excluded_node_ids
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": self.format_name,
            "version": self.version,
            "entry_node": self.entry_node,
            "exit_node": self.exit_node,
            "nodes": {
                node_id: node.to_dict()
                for node_id, node in self.nodes.items()
            },
            "edges": [edge.to_dict() for edge in self.edges],
            "structured_program": self.structured_program,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, document: dict[str, Any]) -> "FlowDiagram":
        FlowDiagramValidator().validate(document)

        # COMMENT statements in the canonicalised program are source metadata,
        # not executable flow.  Older cached flow_diagram.json files may still
        # contain a visual node for such a line (sometimes typed as PROCESS), so
        # derive the authoritative comment lines from the canonical structured
        # program and remove those nodes when the flow document is loaded.
        canonical_comments = cls._canonical_comments(document["structured_program"])
        excluded_node_ids = {
            node_id
            for node_id, node_data in document["nodes"].items()
            if str(node_data.get("node_type", "")).upper() == "COMMENT"
            or (
                node_id not in {document["entry_node"], document["exit_node"]}
                and cls._normalise_source_line(node_data.get("line")) in canonical_comments
            )
        }

        nodes = {
            node_id: FlowNode(
                node_id=node_data["node_id"],
                node_type=node_data["node_type"],
                label=node_data["label"],
                line=node_data["line"],
                data=node_data.get("data", {}),
            )
            for node_id, node_data in document["nodes"].items()
            if node_id not in excluded_node_ids
        }

        raw_edges = [
            FlowEdge(
                source=edge["source"],
                target=edge["target"],
                label=edge.get("label", "NEXT"),
            )
            for edge in document["edges"]
        ]
        edges = cls._bypass_excluded_nodes(raw_edges, excluded_node_ids)

        diagram = cls(
            entry_node=document["entry_node"],
            exit_node=document["exit_node"],
            nodes=nodes,
            edges=edges,
            structured_program=document["structured_program"],
            format_name=document["format"],
            version=document["version"],
        )
        FlowDiagramValidator().validate(diagram.to_dict())
        return diagram

    @staticmethod
    def _normalise_source_line(value: Any) -> int | None:
        """Return an integer source line for current and legacy serialisations."""
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            text = value.strip()
            if text.isdigit():
                return int(text)
        return None

    @classmethod
    def _canonical_comments(
        cls,
        structured_program: dict[str, Any],
    ) -> dict[int, set[str]]:
        """Return every canonical COMMENT statement keyed by source line.

        Current AST serialisation uses ``CommentNode`` with an integer ``line``.
        Older cached artefacts can use ``COMMENT``/``CommentStatement`` names,
        string line numbers, or retain the canonical statement text itself.
        Treat all of those as the same non-executable canonical statement so a
        stale PROCESS node cannot survive merely because its serialisation shape
        differs.  This deliberately examines the canonical structured programme
        only; original LLM text is not consulted or reinterpreted here.
        """
        comments: dict[int, set[str]] = {}

        def canonical_comment_text(value: dict[str, Any]) -> str | None:
            kind = re.sub(r"[^A-Z]", "", str(value.get("kind", "")).upper())
            if kind in {
                "COMMENT",
                "COMMENTNODE",
                "COMMENTSTATEMENT",
                "COMMENTSTATEMENTNODE",
            }:
                return str(value.get("text", "")).strip()

            # Some legacy structured programmes stored a canonical statement
            # verbatim rather than preserving the CommentNode kind.  Only
            # statement/source-text fields are considered so string literals such
            # as OUTPUT "COMMENT ..." are never mistaken for comments.
            for key in (
                "canonical",
                "canonical_text",
                "source_text",
                "statement",
                "raw",
                "text",
            ):
                raw = value.get(key)
                if not isinstance(raw, str):
                    continue
                match = re.match(r"^\s*COMMENT(?:\s+(.*))?$", raw, re.IGNORECASE)
                if match:
                    return (match.group(1) or "").strip()
            return None

        def visit(value: Any) -> None:
            if isinstance(value, dict):
                text = canonical_comment_text(value)
                if text is not None:
                    line = None
                    for key in ("line", "source_line", "line_number", "sourceLine"):
                        line = cls._normalise_source_line(value.get(key))
                        if line is not None:
                            break
                    if line is not None:
                        comments.setdefault(line, set()).add(text)
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        visit(structured_program)
        return comments

    @staticmethod
    def _bypass_excluded_nodes(
        edges: list[FlowEdge],
        excluded_node_ids: set[str],
    ) -> list[FlowEdge]:
        """Remove non-executable nodes while preserving surrounding flow."""
        if not excluded_node_ids:
            return edges

        outgoing: dict[str, list[FlowEdge]] = {}
        for edge in edges:
            outgoing.setdefault(edge.source, []).append(edge)

        result: list[FlowEdge] = []
        seen_edges: set[tuple[str, str, str]] = set()

        def append_edge(source: str, target: str, label: str) -> None:
            key = (source, target, label)
            if key not in seen_edges:
                seen_edges.add(key)
                result.append(FlowEdge(source, target, label))

        for edge in edges:
            if edge.source in excluded_node_ids:
                continue

            if edge.target not in excluded_node_ids:
                append_edge(edge.source, edge.target, edge.label)
                continue

            stack: list[tuple[str, str]] = [(edge.target, edge.label)]
            visited: set[str] = set()
            while stack:
                current, carried_label = stack.pop()
                if current in visited:
                    continue
                visited.add(current)

                for next_edge in outgoing.get(current, []):
                    label = (
                        carried_label
                        if carried_label.upper() != "NEXT"
                        else next_edge.label
                    )
                    if next_edge.target in excluded_node_ids:
                        stack.append((next_edge.target, label))
                    else:
                        append_edge(edge.source, next_edge.target, label)

        return result

    @classmethod
    def from_json(cls, source: str) -> "FlowDiagram":
        document = json.loads(source)
        return cls.from_dict(document)


class ASTStructureSerializer:
    """Converts AST node objects into a deterministic dictionary structure."""

    def serialize(self, node: ASTNode | None) -> dict[str, Any] | None:
        if node is None:
            return None

        document: dict[str, Any] = {
            "kind": node.kind,
            "line": node.line,
        }

        for field_definition in fields(node):
            field_name = field_definition.name

            if field_name in {"line", "node_id"}:
                continue

            field_value = getattr(node, field_name)
            document[field_name] = self._serialize_value(field_value)

        return document

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, ASTNode):
            return self.serialize(value)

        if isinstance(value, list):
            serialized_items: list[Any] = []

            for item in value:
                serialized_items.append(self._serialize_value(item))

            return serialized_items

        return value


class FlowDiagramValidator:
    """Validates the external flow-diagram document before compilation."""

    REQUIRED_FIELDS = {
        "format",
        "version",
        "entry_node",
        "exit_node",
        "nodes",
        "edges",
        "structured_program",
    }

    def validate(self, document: dict[str, Any]) -> None:
        if not isinstance(document, dict):
            raise ValueError("Flow diagram must be a JSON object.")

        missing_fields = self.REQUIRED_FIELDS.difference(document)

        if missing_fields:
            missing_text = ", ".join(sorted(missing_fields))
            raise ValueError(f"Flow diagram is missing fields: {missing_text}.")

        if document["format"] != "NL-FDEP Flow Diagram":
            raise ValueError("Unsupported flow diagram format.")

        if document["version"] != "1.0":
            raise ValueError("Unsupported flow diagram version.")

        nodes = document["nodes"]

        if document["entry_node"] not in nodes:
            raise ValueError("Flow diagram entry node does not exist.")

        if document["exit_node"] not in nodes:
            raise ValueError("Flow diagram exit node does not exist.")

        for edge in document["edges"]:
            if edge["source"] not in nodes:
                raise ValueError(f"Unknown flow edge source: {edge['source']}.")

            if edge["target"] not in nodes:
                raise ValueError(f"Unknown flow edge target: {edge['target']}.")

        program = document["structured_program"]

        if not isinstance(program, dict) or program.get("kind") != "ProgramNode":
            raise ValueError("Flow diagram does not contain a valid structured program.")


class FlowDiagramEncoder:
    """Encodes an AJ AST as a control-flow graph and compiler-ready document."""

    def __init__(self) -> None:
        self.nodes: dict[str, FlowNode] = {}
        self.edges: list[FlowEdge] = []
        self.next_identifier = 1
        self.label_builder = HumanReadableLabelBuilder()
        self._resolved_break_ids: set[str] = set()

    def encode(self, program: ProgramNode) -> FlowDiagram:
        self.nodes = {}
        self.edges = []
        self.next_identifier = 1
        self._resolved_break_ids = set()

        start_id = self._add_node("START", "Start", program.line)
        exit_id = self._add_node("END", "End", program.line)

        first_id, final_ids = self._encode_statements(program.body, exit_id)

        if first_id is None:
            self._add_edge(start_id, exit_id)
        else:
            self._add_edge(start_id, first_id)

            for final_id in final_ids:
                self._add_edge(final_id, exit_id)

        self._separate_terminal_error_branches()

        structured_program = ASTStructureSerializer().serialize(program)

        if structured_program is None:
            raise ValueError("Unable to serialize the AST program.")

        diagram = FlowDiagram(
            entry_node=start_id,
            exit_node=exit_id,
            nodes=self.nodes,
            edges=self.edges,
            structured_program=structured_program,
        )

        FlowDiagramValidator().validate(diagram.to_dict())

        return diagram


    def _separate_terminal_error_branches(self) -> None:
        """Route conditional RAISE branches to a dedicated terminal node.

        A RAISE statement terminates that execution path.  It must not rejoin
        the normal continuation path after the conditional.
        """

        outgoing: dict[str, list[FlowEdge]] = {}

        for edge in self.edges:
            outgoing.setdefault(edge.source, []).append(edge)

        edges_to_remove: list[FlowEdge] = []
        edges_to_add: list[FlowEdge] = []

        for decision_id, decision_node in list(self.nodes.items()):
            if decision_node.node_type.upper() != "DECISION":
                continue

            decision_edges = outgoing.get(decision_id, [])
            true_edges = [
                edge
                for edge in decision_edges
                if edge.label.upper() == "TRUE"
            ]

            for true_edge in true_edges:
                target_node = self.nodes.get(true_edge.target)

                if target_node is None or target_node.node_type.upper() != "RAISE":
                    continue

                raise_edges = outgoing.get(true_edge.target, [])

                for raise_edge in raise_edges:
                    edges_to_remove.append(raise_edge)

                error_end_id = self._add_node(
                    "END",
                    "End after error",
                    target_node.line,
                    {
                        "terminal_reason": "RAISE",
                        "source_node": true_edge.target,
                    },
                )
                edges_to_add.append(
                    FlowEdge(
                        true_edge.target,
                        error_end_id,
                        "NEXT",
                    )
                )

                for edge in decision_edges:
                    if edge is true_edge:
                        continue

                    if edge.label.upper() == "NEXT":
                        edge.label = "FALSE"

        if edges_to_remove:
            self.edges = [
                edge
                for edge in self.edges
                if edge not in edges_to_remove
            ]

        self.edges.extend(edges_to_add)

    def _encode_statements(
        self,
        statements: list[ASTNode],
        continuation_id: str | None,
    ) -> tuple[str | None, list[str]]:
        """Encode a statement sequence while preserving non-fallthrough control.

        RETURN/RAISE/STOP/QUIT and unresolved BREAK/CONTINUE nodes must not be wired
        to the following statement merely because they appear in the same block.
        BREAK becomes ordinary fallthrough only after the nearest loop has resolved
        it as a loop exit.
        """
        first_id: str | None = None
        previous_fallthrough_ids: list[str] = []
        escaped_final_ids: list[str] = []

        for statement in statements:
            # Comments are source metadata, not executable control-flow steps.
            # Keeping them in the structured AST preserves source provenance,
            # but they must not become flow nodes or edges because doing so
            # changes graph counts/topology and can create false flow errors.
            if (
                isinstance(statement, CommentNode)
                or str(getattr(statement, "kind", "")).upper() in {"COMMENT", "COMMENTNODE"}
            ):
                continue

            statement_first_id, statement_final_ids = self._encode_statement(
                statement,
                continuation_id,
            )

            if first_id is None:
                first_id = statement_first_id

            for previous_id in previous_fallthrough_ids:
                self._add_edge(previous_id, statement_first_id)

            next_fallthrough: list[str] = []
            for final_id in statement_final_ids:
                node_type = self.nodes[final_id].node_type.upper()
                is_resolved_break = (
                    node_type == "BREAK"
                    and final_id in self._resolved_break_ids
                )
                if node_type in {"RETURN", "RAISE", "STOP", "QUIT", "CONTINUE"}:
                    escaped_final_ids.append(final_id)
                elif node_type == "BREAK" and not is_resolved_break:
                    escaped_final_ids.append(final_id)
                else:
                    next_fallthrough.append(final_id)

            previous_fallthrough_ids = next_fallthrough

        return first_id, escaped_final_ids + previous_fallthrough_ids

    def _encode_statement(
        self,
        statement: ASTNode,
        continuation_id: str | None,
    ) -> tuple[str, list[str]]:
        if isinstance(statement, IfNode):
            return self._encode_if(statement, continuation_id)

        if isinstance(statement, WhileNode):
            return self._encode_while(statement)

        if isinstance(statement, (ForEachNode, ForRangeNode)):
            return self._encode_for(statement)

        if isinstance(statement, TryCatchNode):
            return self._encode_try_catch(statement)

        if isinstance(statement, ClassNode):
            return self._encode_class(statement)

        if isinstance(statement, ConstructorNode):
            return self._encode_constructor(statement)

        if isinstance(statement, MethodNode):
            return self._encode_method(statement)

        if isinstance(statement, FunctionNode):
            return self._encode_function(statement)

        node_type = self._classify_statement(statement)
        label = self._statement_label(statement)
        node_id = self._add_node(
            node_type,
            label,
            statement.line,
            {"ast_kind": statement.kind},
        )

        return node_id, [node_id]

    def _encode_if(
        self,
        statement: IfNode,
        continuation_id: str | None,
    ) -> tuple[str, list[str]]:
        decision_id = self._add_node(
            "DECISION",
            self.label_builder.condition(statement.condition),
            statement.line,
            {"ast_kind": statement.kind},
        )

        final_ids: list[str] = []
        then_first, then_finals = self._encode_statements(
            statement.then_body.statements,
            continuation_id,
        )

        if then_first is not None:
            self._add_edge(decision_id, then_first, "TRUE")
            final_ids.extend(then_finals)
        else:
            final_ids.append(decision_id)

        false_source_id = decision_id

        for clause in statement.else_if:
            clause_id = self._add_node(
                "DECISION",
                self.label_builder.condition(clause.condition),
                clause.line,
                {"ast_kind": clause.kind},
            )
            self._add_edge(false_source_id, clause_id, "FALSE")

            clause_first, clause_finals = self._encode_statements(
                clause.body.statements,
                continuation_id,
            )

            if clause_first is not None:
                self._add_edge(clause_id, clause_first, "TRUE")
                final_ids.extend(clause_finals)
            else:
                final_ids.append(clause_id)

            false_source_id = clause_id

        if statement.else_body is not None:
            else_first, else_finals = self._encode_statements(
                statement.else_body.statements,
                continuation_id,
            )

            if else_first is not None:
                self._add_edge(false_source_id, else_first, "FALSE")
                final_ids.extend(else_finals)
            else:
                final_ids.append(false_source_id)
        else:
            final_ids.append(false_source_id)

        return decision_id, final_ids

    def _encode_while(self, statement: WhileNode) -> tuple[str, list[str]]:
        decision_id = self._add_node(
            "LOOP_DECISION",
            self.label_builder.condition(statement.condition, "While"),
            statement.line,
            {"ast_kind": statement.kind},
        )
        body_first, body_finals = self._encode_statements(
            statement.body.statements,
            decision_id,
        )

        loop_exit_finals: list[str] = []
        escaped_terminals: list[str] = []
        if body_first is not None:
            self._add_edge(decision_id, body_first, "TRUE")

            for final_id in body_finals:
                node_type = self.nodes[final_id].node_type.upper()
                if node_type == "BREAK" and final_id not in self._resolved_break_ids:
                    self._resolved_break_ids.add(final_id)
                    loop_exit_finals.append(final_id)
                elif node_type == "CONTINUE":
                    self._add_edge(final_id, decision_id, "CONTINUE")
                elif node_type in {"RETURN", "RAISE", "STOP", "QUIT"}:
                    escaped_terminals.append(final_id)
                else:
                    self._add_edge(final_id, decision_id, "LOOP")
        else:
            self._add_edge(decision_id, decision_id, "TRUE")

        return decision_id, [decision_id] + loop_exit_finals + escaped_terminals

    def _encode_for(
        self,
        statement: ForEachNode | ForRangeNode,
    ) -> tuple[str, list[str]]:
        loop_id = self._add_node(
            "LOOP_DECISION",
            self._statement_label(statement),
            statement.line,
            {"ast_kind": statement.kind},
        )
        body_first, body_finals = self._encode_statements(
            statement.body.statements,
            loop_id,
        )

        loop_exit_finals: list[str] = []
        escaped_terminals: list[str] = []
        if body_first is not None:
            self._add_edge(loop_id, body_first, "ITERATE")

            for final_id in body_finals:
                node_type = self.nodes[final_id].node_type.upper()
                if node_type == "BREAK" and final_id not in self._resolved_break_ids:
                    self._resolved_break_ids.add(final_id)
                    loop_exit_finals.append(final_id)
                elif node_type == "CONTINUE":
                    self._add_edge(final_id, loop_id, "CONTINUE")
                elif node_type in {"RETURN", "RAISE", "STOP", "QUIT"}:
                    escaped_terminals.append(final_id)
                else:
                    self._add_edge(final_id, loop_id, "LOOP")

        return loop_id, [loop_id] + loop_exit_finals + escaped_terminals

    def _encode_try_catch(
        self,
        statement: TryCatchNode,
    ) -> tuple[str, list[str]]:
        try_id = self._add_node(
            "TRY",
            "Attempt the following operations",
            statement.line,
            {"ast_kind": statement.kind},
        )
        try_first, try_finals = self._encode_statements(
            statement.try_body.statements,
            None,
        )
        catch_first, catch_finals = self._encode_statements(
            statement.catch_body.statements,
            None,
        )

        if try_first is not None:
            self._add_edge(try_id, try_first, "TRY")

        if catch_first is not None:
            self._add_edge(try_id, catch_first, "EXCEPTION")

        final_ids = try_finals + catch_finals

        if not final_ids:
            final_ids = [try_id]

        return try_id, final_ids

    def _encode_class(
        self,
        statement: ClassNode,
    ) -> tuple[str, list[str]]:
        parameter_text = ", ".join(parameter.name for parameter in statement.parameters)
        label = f"Class {statement.name}"
        if parameter_text:
            label += f" accepts {parameter_text}"
        class_id = self._add_node(
            "CLASS",
            label,
            statement.line,
            {"ast_kind": statement.kind, "name": statement.name},
        )
        body_first, body_finals = self._encode_statements(
            statement.body.statements,
            None,
        )
        if body_first is not None:
            self._add_edge(class_id, body_first, "BODY")
        return class_id, body_finals or [class_id]

    def _encode_constructor(
        self,
        statement: ConstructorNode,
    ) -> tuple[str, list[str]]:
        parameter_text = ", ".join(parameter.name for parameter in statement.parameters)
        label = "Run constructor"
        if parameter_text:
            label += f" with {parameter_text}"
        constructor_id = self._add_node(
            "CONSTRUCTOR",
            label,
            statement.line,
            {"ast_kind": statement.kind},
        )
        body_first, body_finals = self._encode_statements(
            statement.body.statements,
            None,
        )
        if body_first is not None:
            self._add_edge(constructor_id, body_first, "BODY")
        return constructor_id, body_finals or [constructor_id]

    def _encode_method(
        self,
        statement: MethodNode,
    ) -> tuple[str, list[str]]:
        parameters = ", ".join(parameter.name for parameter in statement.parameters)
        label = f"Run method {statement.name}"
        if parameters:
            label += f" with {parameters}"
        method_id = self._add_node(
            "METHOD",
            label,
            statement.line,
            {"ast_kind": statement.kind, "name": statement.name},
        )
        body_first, body_finals = self._encode_statements(
            statement.body.statements,
            None,
        )
        if body_first is not None:
            self._add_edge(method_id, body_first, "BODY")
        return method_id, body_finals or [method_id]

    def _encode_function(
        self,
        statement: FunctionNode,
    ) -> tuple[str, list[str]]:
        function_id = self._add_node(
            "FUNCTION",
            self._function_label(statement),
            statement.line,
            {"ast_kind": statement.kind, "name": statement.name},
        )
        body_first, body_finals = self._encode_statements(
            statement.body.statements,
            None,
        )

        if body_first is not None:
            self._add_edge(function_id, body_first, "BODY")

        return function_id, body_finals or [function_id]

    def _add_node(
        self,
        node_type: str,
        label: str,
        line: int,
        data: dict[str, Any] | None = None,
    ) -> str:
        node_id = f"F{self.next_identifier}"
        self.next_identifier += 1
        self.nodes[node_id] = FlowNode(
            node_id=node_id,
            node_type=node_type,
            label=label,
            line=line,
            data=data or {},
        )
        return node_id

    def _add_edge(
        self,
        source: str,
        target: str,
        label: str = "NEXT",
    ) -> None:
        self.edges.append(FlowEdge(source, target, label))

    @staticmethod
    def _classify_statement(statement: ASTNode) -> str:
        mapping = {
            "AssignmentNode": "PROCESS",
            "PropertyAssignmentNode": "PROCESS",
            "PropertyDeclarationNode": "DECLARATION",
            "OutputNode": "OUTPUT",
            "InputNode": "INPUT",
            "ReturnNode": "RETURN",
            "CallNode": "CALL",
            "BreakNode": "BREAK",
            "StopNode": "STOP",
            "QuitNode": "QUIT",
            "ContinueNode": "CONTINUE",
            "RaiseNode": "RAISE",
            "AppendNode": "PROCESS",
            "InsertNode": "PROCESS",
            "RemoveValueNode": "PROCESS",
            "RemoveFirstNode": "PROCESS",
            "RemoveLastNode": "PROCESS",
            "CommentNode": "COMMENT",
            "ImportDirectiveNode": "IMPORT",
        }
        return mapping.get(statement.kind, "PROCESS")

    def _statement_label(self, statement: ASTNode) -> str:
        return self.label_builder.statement(statement)

    @staticmethod
    def _function_label(statement: FunctionNode) -> str:
        parameters = ", ".join(parameter.name for parameter in statement.parameters)
        if parameters:
            return f"Run function {statement.name} with {parameters}"
        return f"Run function {statement.name}"
