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


@pytest.mark.parametrize("surface", ["ERROR", "error", "Error"])
def test_bare_error_in_return_position_is_canonical_error_string(surface):
    source = f'''FUNCTION check ACCEPTS(value)\n    IF value < 0 THEN\n        RETURN {surface}\n    ENDIF\n    RETURN value\nENDFUNCTION\n'''
    result = _process(source)
    assert 'RETURN STRING("ERROR")' in result.processed_source
    assert any(t.rule == "GC204" for t in result.transformations)

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    namespace = {}
    exec(compiled.source_code, namespace)
    assert namespace["check"](-1) == "ERROR"
    assert namespace["check"](7) == 7


def test_error_assignment_is_not_reclassified_as_return_sentinel():
    source = '''FUNCTION check ACCEPTS()\n    status <- ERROR\n    RETURN status\nENDFUNCTION\n'''
    result = _process(source)
    assert 'status <- ERROR' in result.processed_source
    assert 'STRING("ERROR")' not in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success


def test_longer_error_identifier_is_not_reclassified():
    source = '''FUNCTION check ACCEPTS(ERROR_CODE)\n    RETURN ERROR_CODE\nENDFUNCTION\n'''
    result = _process(source)
    assert 'RETURN ERROR_CODE' in result.processed_source
    assert 'STRING("ERROR")' not in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_existing_error_string_is_left_as_a_string_literal():
    source = '''FUNCTION check ACCEPTS()\n    RETURN "ERROR"\nENDFUNCTION\n'''
    result = _process(source)
    assert 'RETURN STRING("ERROR")' in result.processed_source
    assert not any(t.rule == "GC204" for t in result.transformations)
