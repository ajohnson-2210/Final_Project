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


def test_random_expressions_are_first_class_and_compile_to_documented_backing():
    diagram, python = compile_source('''
FUNCTION demo ACCEPTS()
    i <- RANDOM INT(INTEGER(1), INTEGER(3))
    f <- RANDOM FLOAT(INTEGER(1), FLOAT(3.5))
    b <- RANDOM BOOLEAN()
    RETURN b
ENDFUNCTION
''')
    statements = diagram.to_dict()['structured_program']['body'][0]['body']['statements']
    assert statements[0]['value']['kind'] == 'RandomExpressionNode'
    assert statements[0]['value']['random_type'] == 'INT'
    assert statements[1]['value']['random_type'] == 'FLOAT'
    assert statements[2]['value']['random_type'] == 'BOOLEAN'
    assert 'import random as _aj_random' in python
    assert '_aj_random.randint(1, 3)' in python
    assert '_aj_random.uniform(1, 3.5)' in python
    assert 'bool(_aj_random.getrandbits(1))' in python


def test_random_import_is_only_added_when_random_expression_is_present():
    _, python = compile_source('''
FUNCTION demo ACCEPTS()
    RETURN INTEGER(1)
ENDFUNCTION
''')
    assert 'import random as _aj_random' not in python


def test_random_module_alias_is_hygienic_against_source_identifiers():
    _, python = compile_source('''
FUNCTION demo ACCEPTS()
    _aj_random <- INTEGER(7)
    value <- RANDOM INT(INTEGER(1), INTEGER(2))
    RETURN value + _aj_random
ENDFUNCTION
''')
    assert 'import random as _aj_random_1' in python
    assert '_aj_random_1.randint(1, 2)' in python
    assert '_aj_random = 7' in python


def test_random_arity_is_fixed_by_canonical_grammar():
    too_few = parse('''
FUNCTION demo ACCEPTS()
    RETURN RANDOM INT(INTEGER(1))
ENDFUNCTION
''')
    assert not too_few.success
    assert 'RANDOM INT requires exactly two bounds' in too_few.error

    too_many = parse('''
FUNCTION demo ACCEPTS()
    RETURN RANDOM BOOLEAN(INTEGER(1))
ENDFUNCTION
''')
    assert not too_many.success
    assert 'RANDOM BOOLEAN requires zero arguments' in too_many.error


def test_random_int_requires_known_integer_bounds_only():
    bad = parse('''
FUNCTION demo ACCEPTS()
    RETURN RANDOM INT(FLOAT(1.5), INTEGER(3))
ENDFUNCTION
''')
    assert not bad.success
    assert 'RANDOM INT bounds must be INTEGER, found FLOAT' in bad.error

    unknown = parse('''
FUNCTION demo ACCEPTS(low, high)
    RETURN RANDOM INT(low, high)
ENDFUNCTION
''')
    assert unknown.success, unknown.error


def test_random_float_requires_known_numeric_bounds_only():
    bad = parse('''
FUNCTION demo ACCEPTS()
    RETURN RANDOM FLOAT(STRING("low"), FLOAT(3.5))
ENDFUNCTION
''')
    assert not bad.success
    assert 'RANDOM FLOAT bounds must be numeric, found STRING' in bad.error

    valid = parse('''
FUNCTION demo ACCEPTS()
    RETURN RANDOM FLOAT(INTEGER(1), FLOAT(3.5))
ENDFUNCTION
''')
    assert valid.success, valid.error


def test_random_result_types_participate_in_existing_boolean_semantics():
    valid = parse('''
FUNCTION demo ACCEPTS()
    IF RANDOM BOOLEAN() THEN
        RETURN INTEGER(1)
    ENDIF
    RETURN INTEGER(0)
ENDFUNCTION
''')
    assert valid.success, valid.error

    invalid = parse('''
FUNCTION demo ACCEPTS()
    IF RANDOM INT(INTEGER(0), INTEGER(1)) THEN
        RETURN INTEGER(1)
    ENDIF
    RETURN INTEGER(0)
ENDFUNCTION
''')
    assert not invalid.success
    assert 'IF condition must be BOOLEAN, found INTEGER' in invalid.error


def test_random_expression_has_human_readable_flow_label():
    result = parse('''
value <- RANDOM INT(INTEGER(1), INTEGER(5))
''')
    assert result.success, result.error
    document = FlowDiagramEncoder().encode(result.ast).to_dict()
    labels = [node['label'] for node in document['nodes'].values()]
    assert any('random int from 1 to 5' in label.lower() for label in labels)
