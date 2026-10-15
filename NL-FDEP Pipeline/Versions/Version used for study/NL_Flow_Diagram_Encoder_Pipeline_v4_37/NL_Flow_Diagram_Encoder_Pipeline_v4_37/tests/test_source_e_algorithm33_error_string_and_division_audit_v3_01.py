from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


SOURCE = '''FUNCTION SQUARE_ROOT(n)
  IF n < 0 THEN
    RETURN ERROR
  END IF
  IF n == 0 OR n == 1 THEN
    RETURN n
  END IF
  low = 0
  high = n
  WHILE low <= high
    mid = (low + high) / 2
    IF mid * mid <= n THEN
      low = mid + 1
    ELSE
      high = mid - 1
    END IF
  END WHILE
  RETURN high
END FUNCTION
'''


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def test_source_e_algorithm33_recovers_error_string_but_does_not_correct_division():
    result = _process(SOURCE)
    assert 'RETURN STRING("ERROR")' in result.processed_source
    assert 'mid <- (low + high) / 2' in result.processed_source
    assert 'INTEGER DIVISION' not in result.processed_source
    assert any(t.rule == "GC204" for t in result.transformations)

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert 'return "ERROR"' in compiled.source_code or "return 'ERROR'" in compiled.source_code
    mid_lines = [line.strip() for line in compiled.source_code.splitlines() if line.strip().startswith('mid = ')]
    assert len(mid_lines) == 1
    assert ' / ' in mid_lines[0]
    assert '//' not in mid_lines[0]


def test_source_e_algorithm33_is_audited_as_expected_correctness_failure_from_source_division():
    result = _process(SOURCE)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    namespace = {}
    exec(compiled.source_code, namespace)
    function = namespace['SQUARE_ROOT']

    assert function(-1) == "ERROR"
    # Preserve and expose the supplied '/' semantics rather than silently
    # reconstructing the conventional integer midpoint operation.
    assert function(4) == 2.5
    assert function(10) == 2.5
    assert function(4) != 2
    assert function(10) != 3
