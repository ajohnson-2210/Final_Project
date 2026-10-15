import pytest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _process(source: str):
    return PseudocodeProfileProcessor().process(source, PseudocodeProfile.GENERIC_COMPATIBILITY)


@pytest.mark.parametrize(
    ("source_expression", "expected_expression"),
    [
        ("ASCII(c)", "CHAR(c)"),
        ("ascii(c)", "CHAR(c)"),
        ("CALL ASCII(c)", "CHAR(c)"),
        ("Call Ascii(c)", "CHAR(c)"),
    ],
)
def test_ascii_wrapper_recovery_is_case_and_pipeline_shape_independent(source_expression, expected_expression):
    source = f'''FUNCTION encode ACCEPTS(c)
    value <- {source_expression}
    RETURN value
ENDFUNCTION
'''
    result = _process(source)
    assert "ASCII" not in result.processed_source.upper()
    assert expected_expression in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "value = ord(c)" in compiled.source_code


def test_reserved_keyword_identifier_escape_is_applied_inside_char_conversion():
    source = '''FUNCTION encode ACCEPTS(text)
    FOR EACH char IN text DO
        value <- ASCII(char)
        OUTPUT value
    ENDFOR
ENDFUNCTION
'''
    result = _process(source)
    assert "FOR EACH __reserved_keyword__char IN text DO" in result.processed_source
    assert "CHAR(__reserved_keyword__char)" in result.processed_source
    assert "CHAR(CHAR)" not in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_unrelated_free_function_call_is_not_reclassified_as_char_conversion():
    source = '''FUNCTION encode ACCEPTS(c)
    RETURN characterCode(c)
ENDFUNCTION
'''
    result = _process(source)
    assert "CALL characterCode(c)" in result.processed_source
    assert "CHAR(c)" not in result.processed_source
