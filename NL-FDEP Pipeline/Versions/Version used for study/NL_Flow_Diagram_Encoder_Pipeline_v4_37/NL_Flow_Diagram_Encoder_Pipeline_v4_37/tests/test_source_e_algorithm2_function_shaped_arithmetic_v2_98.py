import pytest

from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


SOURCE = '''FUNCTION DECIMAL_TO_BINARY(n)
  IF n == 0 THEN
    RETURN "0"
  END IF
  binary = ""
  WHILE n > 0
    binary = MOD(n, 2) + binary
    n = FLOOR(n / 2)
  END WHILE
  RETURN binary
END FUNCTION
'''


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def test_source_e_algorithm2_preserves_missing_numeric_to_string_conversion_as_expected_failure():
    result = _process(SOURCE)
    expected = '''FUNCTION DECIMAL_TO_BINARY ACCEPTS(n)
  IF n == 0 THEN
    RETURN STRING("0")
  ENDIF
  binary <- EMPTY STRING
  WHILE n > 0 DO
    binary <- (n MODULUS 2) + binary
    n <- (n INTEGER DIVISION 2)
  ENDWHILE
  RETURN binary
ENDFUNCTION'''
    assert result.processed_source.strip() == expected

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    namespace = {}
    exec(compiled.source_code, namespace)

    assert namespace["DECIMAL_TO_BINARY"](0) == "0"
    with pytest.raises(TypeError, match="int.*str"):
        namespace["DECIMAL_TO_BINARY"](10)


def test_source_e_algorithm2_audit_counterfactual_string_conversion_makes_algorithm_viable():
    result = _process(SOURCE)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    repaired = compiled.source_code.replace(
        "binary = ((n % 2) + binary)",
        "binary = (str((n % 2)) + binary)",
    )
    assert repaired != compiled.source_code
    namespace = {}
    exec(repaired, namespace)
    fn = namespace["DECIMAL_TO_BINARY"]
    assert fn(0) == "0"
    assert fn(1) == "1"
    assert fn(10) == "1010"
    assert fn(31) == "11111"

