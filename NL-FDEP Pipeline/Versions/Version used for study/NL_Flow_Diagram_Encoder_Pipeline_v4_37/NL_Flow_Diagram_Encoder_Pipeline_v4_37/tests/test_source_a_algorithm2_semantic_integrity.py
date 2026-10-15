import pytest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _raw_algorithm2():
    return '''BEGIN
    INPUT Number
    Binary <- ""

    IF Number = 0 THEN
        OUTPUT "0"
    ELSE
        WHILE Number > 0
            Remainder <- Number MOD 2
            Binary <- Remainder + Binary
            Number <- Number DIV 2
        ENDWHILE

        OUTPUT Binary
    ENDIF
END
'''


def test_source_a_algorithm2_preserves_missing_digit_to_string_conversion_as_expected_failure():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm2(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )

    expected = '''FUNCTION unnamed_function ACCEPTS(Number)
    Binary <- EMPTY STRING

    IF Number == 0 THEN
        OUTPUT STRING("0")
    ELSE
        WHILE Number > 0 DO
            Remainder <- Number MODULUS 2
            Binary <- Remainder + Binary
            Number <- Number INTEGER DIVISION 2
        ENDWHILE

        OUTPUT Binary
    ENDIF
ENDFUNCTION'''
    assert result.processed_source.strip() == expected
    assert "FUNCTION PROCESS" not in result.processed_source
    assert "CALL to_string" not in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "def unnamed_function(Number):" in compiled.source_code
    assert "Remainder = (Number % 2)" in compiled.source_code
    assert "Binary = (Remainder + Binary)" in compiled.source_code
    assert "Number = (Number // 2)" in compiled.source_code

    namespace = {}
    exec(compiled.source_code, namespace)
    with pytest.raises(TypeError, match="int.*str"):
        namespace["unnamed_function"](10)


def test_source_a_algorithm2_audit_counterfactual_string_conversion_makes_algorithm_viable(capsys):
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm2(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    repaired = compiled.source_code.replace(
        "Binary = (Remainder + Binary)",
        "Binary = (str(Remainder) + Binary)",
    )
    assert repaired != compiled.source_code
    namespace = {}
    exec(repaired, namespace)
    namespace["unnamed_function"](10)
    assert capsys.readouterr().out.strip() == "1010"

def test_digit_to_string_coercion_is_not_applied_without_explicit_string_accumulator():
    source = '''FUNCTION Example ACCEPTS(Number)
    Value <- INTEGER(0)
    Remainder <- Number MODULUS 2
    Value <- Remainder + Value
    RETURN Value
ENDFUNCTION
'''
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    assert "Value <- Remainder + Value" in result.processed_source
    assert "to_string(Remainder)" not in result.processed_source
