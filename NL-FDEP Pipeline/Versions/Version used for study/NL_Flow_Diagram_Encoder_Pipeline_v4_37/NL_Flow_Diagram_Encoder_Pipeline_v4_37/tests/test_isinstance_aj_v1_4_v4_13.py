import pytest

from aj_parser import AJParserFacade, IsInstanceNode
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


def test_single_type_reference_parses_as_dedicated_node():
    parsed = parse(
        'value <- STRING("tree")\n'
        'result <- CALL ISINSTANCE(value, STRING)\n'
    )
    node = parsed.ast.body[1].value
    assert isinstance(node, IsInstanceNode)
    assert node.type_names == ['STRING']


def test_multiple_type_references_parse_without_becoming_values():
    parsed = parse(
        'value <- 3\n'
        'result <- CALL ISINSTANCE(value, (INTEGER, FLOAT))\n'
    )
    node = parsed.ast.body[1].value
    assert isinstance(node, IsInstanceNode)
    assert node.type_names == ['INTEGER', 'FLOAT']


def test_isinstance_returns_boolean_for_static_condition_validation():
    parse(
        'value <- 3\n'
        'IF CALL ISINSTANCE(value, (INTEGER, FLOAT)) THEN\n'
        'OUTPUT STRING("numeric")\n'
        'ENDIF\n'
    )


@pytest.mark.parametrize(
    ('aj_type', 'py_type'),
    [
        ('INTEGER', 'int'), ('FLOAT', 'float'), ('STRING', 'str'),
        ('BOOLEAN', 'bool'), ('LIST', 'list'), ('DICTIONARY', 'dict'),
        ('SET', 'set'), ('TUPLE', 'tuple'),
    ],
)
def test_builtin_type_references_lower_to_python_isinstance(aj_type, py_type):
    _, _, source = compile_source(
        'FUNCTION check ACCEPTS(value)\n'
        f'RETURN CALL ISINSTANCE(value, {aj_type})\n'
        'ENDFUNCTION\n'
    )
    assert f'return isinstance(value, {py_type})' in source


def test_multiple_types_lower_to_python_tuple():
    _, _, source = compile_source(
        'FUNCTION check ACCEPTS(value)\n'
        'RETURN CALL ISINSTANCE(value, (INTEGER, FLOAT))\n'
        'ENDFUNCTION\n'
    )
    assert 'return isinstance(value, (int, float))' in source


def test_runtime_behaviour_matches_python_isinstance():
    _, _, source = compile_source(
        'FUNCTION numeric ACCEPTS(value)\n'
        'RETURN CALL ISINSTANCE(value, (INTEGER, FLOAT))\n'
        'ENDFUNCTION\n'
        'FUNCTION textual ACCEPTS(value)\n'
        'RETURN CALL ISINSTANCE(value, STRING)\n'
        'ENDFUNCTION\n'
    )
    namespace = {}
    exec(source, namespace)
    assert namespace['numeric'](3) is True
    assert namespace['numeric'](3.5) is True
    assert namespace['numeric']('3') is False
    assert namespace['textual']('tree') is True
    assert namespace['textual'](3) is False


def test_flow_preserves_isinstance_as_first_class_expression():
    parsed, flow, _ = compile_source(
        'FUNCTION check ACCEPTS(value)\n'
        'RETURN CALL ISINSTANCE(value, (INTEGER, FLOAT))\n'
        'ENDFUNCTION\n'
    )
    expression = flow.to_dict()['structured_program']['body'][0]['body']['statements'][0]['expression']
    assert expression['kind'] == 'IsInstanceNode'
    assert expression['type_names'] == ['INTEGER', 'FLOAT']
    label = HumanReadableLabelBuilder().expression(parsed.ast.body[0].body.statements[0].expression)
    assert label == 'value is an instance of integer or float'


def test_isinstance_checks_source_value_binding_but_not_type_keyword_as_variable():
    result = AJParserFacade().parse('result <- CALL ISINSTANCE(missing, STRING)\n')
    assert not result.success
    assert 'missing' in (result.error or '')


def test_isinstance_requires_type_reference():
    for source in (
        'x <- CALL ISINSTANCE(value, )\n',
        'x <- CALL ISINSTANCE(value, ())\n',
    ):
        result = AJParserFacade().parse(source)
        assert not result.success
