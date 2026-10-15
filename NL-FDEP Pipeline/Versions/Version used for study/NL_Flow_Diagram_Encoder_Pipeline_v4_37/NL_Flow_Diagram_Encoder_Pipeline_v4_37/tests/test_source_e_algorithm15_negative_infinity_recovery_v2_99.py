from aj_parser import AJParserFacade
from flow_diagram import FlowDiagramEncoder
from aj_python_compiler import AJPythonCompiler
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


SOURCE = '''FUNCTION SECOND_LARGEST(arr)
  max = NEGATIVE_INFINITY
  second_max = NEGATIVE_INFINITY
  FOR num IN arr
    IF num > max THEN
      second_max = max
      max = num
    ELSE IF num > second_max AND num != max THEN
      second_max = num
    END IF
  END FOR
  RETURN second_max
END FUNCTION
'''


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def test_source_e_algorithm15_exact_source_uses_existing_negative_infinity_representation():
    result = _process(SOURCE)
    assert "max <- CALL negative_infinity()" in result.processed_source
    assert "second_max <- CALL negative_infinity()" in result.processed_source
    assert "NEGATIVE_INFINITY" not in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    namespace = {}
    exec(compiled.source_code, namespace)

    assert namespace["SECOND_LARGEST"]([1, 2, 3, 4, 5]) == 4
    assert namespace["SECOND_LARGEST"]([-8, -3, -10, -4]) == -4
