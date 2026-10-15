from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def _compile(canonical: str):
    parsed = AJParserFacade().parse(canonical)
    assert parsed.success, parsed.error
    return AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))


def test_undefined_is_punctuation_is_expected_failure_before_python_generation():
    compiled = _compile("""FUNCTION demo ACCEPTS(value)
    RETURN CALL is_punctuation(value)
ENDFUNCTION
""")
    assert not compiled.success
    assert compiled.source_code == ""
    assert "Expected failure" in compiled.message
    assert "is_punctuation" in compiled.message


def test_explicit_is_punctuation_helper_definition_is_preserved():
    compiled = _compile("""FUNCTION is_punctuation ACCEPTS(value)
    RETURN value == CHAR("!")
ENDFUNCTION
FUNCTION demo ACCEPTS(value)
    RETURN CALL is_punctuation(value)
ENDFUNCTION
""")
    assert compiled.success, compiled.message
    assert "def is_punctuation(value):" in compiled.source_code
    assert "return is_punctuation(value)" in compiled.source_code
    assert ".isalnum()" not in compiled.source_code
    assert ".isspace()" not in compiled.source_code


def test_character_intrinsics_remain_distinct_from_punctuation_boundary():
    compiled = _compile("""FUNCTION demo ACCEPTS(value)
    RETURN CALL is_digit(value) OR CALL is_uppercase(value)
ENDFUNCTION
""")
    assert compiled.success, compiled.message
    assert "value.isdigit()" in compiled.source_code
    assert "value.isupper()" in compiled.source_code
