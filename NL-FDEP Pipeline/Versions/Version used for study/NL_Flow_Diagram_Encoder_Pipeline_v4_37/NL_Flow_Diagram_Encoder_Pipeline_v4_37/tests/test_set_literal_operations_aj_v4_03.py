from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def parse(source: str):
    return AJParserFacade().parse(source)


def compile_source(source: str):
    parsed = parse(source)
    assert parsed.success, parsed.error or parsed.report.pretty()
    diagram = FlowDiagramEncoder().encode(parsed.ast)
    compiled = AJPythonCompiler().compile(diagram)
    assert compiled.success, compiled.message
    return diagram, compiled.source_code


def test_set_literal_is_first_class_and_empty_set_uses_set_constructor():
    _, python = compile_source('''
FUNCTION demo ACCEPTS()
    a <- SET [INTEGER(1), INTEGER(2)]
    b <- SET []
    RETURN a
ENDFUNCTION
''')
    assert 'a = {1, 2}' in python
    assert 'b = set()' in python


def test_set_literal_establishes_set_backing_for_append_lowering():
    _, python = compile_source('''
FUNCTION demo ACCEPTS()
    values <- SET [INTEGER(1)]
    APPEND INTEGER(2) TO values
    RETURN values
ENDFUNCTION
''')
    assert 'values = {1}' in python
    assert 'values.add(2)' in python
    assert 'values.append(2)' not in python


def test_union_intersection_and_difference_compile_as_set_operations():
    _, python = compile_source('''
FUNCTION demo ACCEPTS()
    left <- SET [INTEGER(1), INTEGER(2)]
    right <- SET [INTEGER(2), INTEGER(3)]
    united <- UNION(left, right)
    common <- INTERSECTION(left, right)
    remaining <- DIFFERENCE(left, right)
    RETURN united
ENDFUNCTION
''')
    assert 'united = (left | right)' in python
    assert 'common = (left & right)' in python
    assert 'remaining = (left - right)' in python


def test_set_operation_result_establishes_set_backing_for_later_append():
    _, python = compile_source('''
FUNCTION demo ACCEPTS()
    left <- EMPTY SET
    right <- EMPTY SET
    result <- UNION(left, right)
    APPEND INTEGER(1) TO result
    RETURN result
ENDFUNCTION
''')
    assert 'result = (left | right)' in python
    assert 'result.add(1)' in python


def test_set_operations_reject_statically_known_non_set_operands_only():
    bad = parse('''
FUNCTION demo ACCEPTS()
    left <- EMPTY LIST
    right <- EMPTY SET
    RETURN UNION(left, right)
ENDFUNCTION
''')
    assert not bad.success
    assert 'UNION requires SET operands, found LIST' in bad.error

    unknown = parse('''
FUNCTION demo ACCEPTS(left, right)
    RETURN INTERSECTION(left, right)
ENDFUNCTION
''')
    assert unknown.success, unknown.error


def test_set_operation_arity_is_exactly_two():
    too_few = parse('''
FUNCTION demo ACCEPTS(values)
    RETURN UNION(values)
ENDFUNCTION
''')
    assert not too_few.success
    assert 'UNION requires exactly two operands' in too_few.error

    too_many = parse('''
FUNCTION demo ACCEPTS(a, b, c)
    RETURN DIFFERENCE(a, b, c)
ENDFUNCTION
''')
    assert not too_many.success
    assert 'DIFFERENCE requires exactly two operands' in too_many.error


def test_set_operation_names_remain_legal_identifiers_outside_operation_syntax():
    result = parse('''
FUNCTION Union ACCEPTS(value)
    RETURN value
ENDFUNCTION

FUNCTION demo ACCEPTS()
    UNION <- INTEGER(1)
    RETURN CALL Union(UNION)
ENDFUNCTION
''')
    assert result.success, result.error
