import pytest

from aj_parser import AJParserFacade, CastNode, LiteralNode
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder, HumanReadableLabelBuilder


def parse(source: str):
    result = AJParserFacade().parse(source)
    assert result.success, result.error
    return result


def compile_source(source: str):
    parsed = parse(source)
    flow = FlowDiagramEncoder().encode(parsed.ast)
    compiled = AJPythonCompiler().compile(flow)
    assert compiled.success, compiled.message
    return parsed, flow, compiled.source_code


def test_cast_syntax_is_distinct_from_typed_literal_constructor():
    parsed = parse(
        "literal <- INTEGER(23)\n"
        "converted <- CALL INTEGER(literal)\n"
    )
    literal_expr = parsed.ast.body[0].value
    cast_expr = parsed.ast.body[1].value
    assert isinstance(literal_expr, LiteralNode)
    assert literal_expr.data_type == "INTEGER"
    assert literal_expr.value == 23
    assert isinstance(cast_expr, CastNode)
    assert cast_expr.target_type == "INTEGER"


@pytest.mark.parametrize(
    ("target", "python_name"),
    [("INTEGER", "int"), ("FLOAT", "float"), ("STRING", "str")],
)
def test_explicit_casts_lower_to_python_runtime_conversions(target, python_name):
    _, _, source = compile_source(
        "FUNCTION convert ACCEPTS(value)\n"
        f"RETURN CALL {target}(value)\n"
        "ENDFUNCTION\n"
    )
    assert f"return {python_name}(value)" in source


def test_integer_cast_failure_is_catchable_by_existing_try_catch_semantics():
    _, _, source = compile_source(
        'FUNCTION convert ACCEPTS(value)\n'
        'TRY\n'
        'number <- CALL INTEGER(value)\n'
        'RETURN number\n'
        'CATCH\n'
        'RETURN -INTEGER(1)\n'
        'ENDTRY\n'
        'ENDFUNCTION\n'
    )
    namespace = {}
    exec(source, namespace)
    assert namespace["convert"]("23") == 23
    assert namespace["convert"]("invalid") == -1


def test_float_and_string_cast_runtime_behaviour_matches_defined_python_lowering():
    _, _, source = compile_source(
        'FUNCTION convert_float ACCEPTS(value)\n'
        'RETURN CALL FLOAT(value)\n'
        'ENDFUNCTION\n'
        'FUNCTION convert_string ACCEPTS(value)\n'
        'RETURN CALL STRING(value)\n'
        'ENDFUNCTION\n'
    )
    namespace = {}
    exec(source, namespace)
    assert namespace["convert_float"]("3.5") == 3.5
    assert namespace["convert_string"](23) == "23"


def test_cast_requires_exactly_one_argument():
    for source in (
        "x <- CALL INTEGER()\n",
        "x <- CALL FLOAT(INTEGER(1), INTEGER(2))\n",
        "x <- CALL STRING()\n",
    ):
        result = AJParserFacade().parse(source)
        assert not result.success
        assert "requires exactly one argument" in (result.error or "")


def test_flow_structured_program_preserves_cast_as_first_class_semantic_expression():
    parsed, flow, _ = compile_source(
        "FUNCTION convert ACCEPTS(value)\n"
        "result <- CALL INTEGER(value)\n"
        "RETURN result\n"
        "ENDFUNCTION\n"
    )
    value = flow.to_dict()["structured_program"]["body"][0]["body"]["statements"][0]["value"]
    assert value["kind"] == "CastNode"
    assert value["target_type"] == "INTEGER"
    assert HumanReadableLabelBuilder().expression(parsed.ast.body[0].body.statements[0].value) == "value converted to integer"
