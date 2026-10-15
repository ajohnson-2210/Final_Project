import pytest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


@pytest.mark.parametrize(
    ("statement", "expected"),
    [
        ("RETURN (a, b)", "RETURN TUPLE(a, b)"),
        ("return (a, b, c)", "RETURN TUPLE(a, b, c)"),
        ("OUTPUT (a, b)", "OUTPUT TUPLE(a, b)"),
        ("RETURN a, b", "RETURN TUPLE(a, b)"),
        ("OUTPUT a, b", "OUTPUT CALL output_values(a, b)"),
    ],
)
def test_multi_value_statement_surfaces_preserve_return_tuple_and_output_argument_distinction(statement, expected):
    source = f'''FUNCTION pair ACCEPTS(a, b, c)
    {statement}
ENDFUNCTION
'''
    result = _process(source)
    assert expected in result.processed_source
    assert "CALL RETURN" not in result.processed_source
    assert "CALL OUTPUT" not in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_single_parenthesised_expression_is_not_reclassified_as_tuple():
    source = '''FUNCTION grouped ACCEPTS(a, b)
    RETURN (a + b)
ENDFUNCTION
'''
    result = _process(source)
    assert "RETURN TUPLE" not in result.processed_source
    assert "RETURN (a + b)" in result.processed_source
    assert "CALL RETURN" not in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "return (a + b)" in compiled.source_code


def test_nested_commas_inside_calls_do_not_create_statement_tuple():
    source = '''FUNCTION groupedCall ACCEPTS(a, b)
    RETURN (combine(a, b))
ENDFUNCTION
'''
    result = _process(source)
    assert "RETURN TUPLE" not in result.processed_source
    assert "RETURN (CALL combine(a, b))" in result.processed_source


def test_parenthesised_tuple_can_contain_nested_calls_without_losing_boundaries():
    source = '''FUNCTION pairedCalls ACCEPTS(a, b, c)
    RETURN (combine(a, b), transform(c))
ENDFUNCTION
'''
    result = _process(source)
    assert "RETURN TUPLE(CALL combine(a, b), CALL transform(c))" in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_legacy_already_mangled_call_return_remains_backwards_compatible():
    source = '''FUNCTION legacy ACCEPTS(a, b)
    CALL RETURN (a, b)
ENDFUNCTION
'''
    result = _process(source)
    assert "RETURN TUPLE(a, b)" in result.processed_source
    assert "CALL RETURN" not in result.processed_source
