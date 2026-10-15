from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _raw_algorithm44():
    return '''BEGIN
    INPUT Array

    CurrentSum ? Array[0]
    MaxSum ? Array[0]

    FOR i ? 1 TO LENGTH(Array)-1
        CurrentSum ? MAX(Array[i], CurrentSum + Array[i])

        IF CurrentSum > MaxSum THEN
            MaxSum ? CurrentSum
        ENDIF
    ENDFOR

    OUTPUT MaxSum
END
'''


def test_source_a_algorithm44_preserves_kadane_and_inclusive_last_index():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm44(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )

    expected = '''FUNCTION unnamed_function ACCEPTS(Array)
    CurrentSum <- Array[0]
    MaxSum <- Array[0]

    FOR i <- IN RANGE 1 TO (LENGTH OF Array - 1) + 1 DO
        CurrentSum <- CALL max(Array[i], CurrentSum + Array[i])

        IF CurrentSum > MaxSum THEN
            MaxSum <- CurrentSum
        ENDIF
    ENDFOR

    OUTPUT MaxSum
ENDFUNCTION'''
    assert result.processed_source == expected

    assert any(t.rule == "GC171" for t in result.transformations)
    assert "FUNCTION PROCESS" not in result.processed_source
    assert "CurrentSum <- CALL max(Array[i], CurrentSum + Array[i])" in result.processed_source
    assert "RETURN" not in result.processed_source

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error

    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "def unnamed_function(Array):" in compiled.source_code
    assert "for i in range(1, len(Array)):" in compiled.source_code
    assert "CurrentSum = max(Array[i], (CurrentSum + Array[i]))" in compiled.source_code
    assert "print(MaxSum)" in compiled.source_code


def test_source_a_algorithm44_does_not_invent_subarray_tracking():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm44(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    upper = result.processed_source.upper()
    assert "STARTINDEX" not in upper
    assert "ENDINDEX" not in upper
    assert "SUBARRAY" not in upper
    assert "SLICE" not in upper
