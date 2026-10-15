from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _raw_algorithm42():
    return '''BEGIN
    INPUT Array, Target

    FOR i ? 0 TO LENGTH(Array)-2
        FOR j ? i+1 TO LENGTH(Array)-1
            IF Array[i] + Array[j] = Target THEN
                OUTPUT Array[i], Array[j]
            ENDIF
        ENDFOR
    ENDFOR
END
'''


def test_source_a_algorithm42_preserves_inclusive_source_bounds_in_end_exclusive_aj():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm42(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )

    expected = '''FUNCTION unnamed_function ACCEPTS(Array, Target)
    FOR i <- IN RANGE 0 TO (LENGTH OF Array - 2) + 1 DO
        FOR j <- IN RANGE i + 1 TO (LENGTH OF Array - 1) + 1 DO
            IF Array[i] + Array[j] == Target THEN
                OUTPUT CALL output_values(Array[i], Array[j])
            ENDIF
        ENDFOR
    ENDFOR
ENDFUNCTION'''
    assert result.processed_source == expected

    # The neutral wrapper and endpoint adjustment are the only structural
    # additions required; do not fabricate an alternative pair-search method.
    assert "FUNCTION PROCESS" not in result.processed_source
    assert "HASH" not in result.processed_source.upper()
    assert "SET" not in result.processed_source.upper()
    assert any(t.rule == "GC169" for t in result.transformations)
    assert all(t.rule != "GC096" for t in result.transformations)

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error

    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "def unnamed_function(Array, Target):" in compiled.source_code
    assert "for i in range(0, len(Array) - 1):" in compiled.source_code
    assert "for j in range((i + 1), len(Array)):" in compiled.source_code
    assert "print(Array[i], Array[j])" in compiled.source_code
    assert "print((Array[i], Array[j]))" not in compiled.source_code


def test_range_compiler_combines_non_unit_integer_offsets():
    parsed = AJParserFacade().parse(
        '''FOR i <- IN RANGE 0 TO (Limit - 2) + 1 DO
    OUTPUT i
ENDFOR'''
    )
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "range(0, Limit - 1)" in compiled.source_code
    assert "((Limit - 2) + 1)" not in compiled.source_code


def test_range_compiler_collapses_only_exact_synthetic_x_minus_one_plus_one():
    parsed = AJParserFacade().parse(
        '''FOR i <- IN RANGE 0 TO (Limit - 1) + 1 DO
    OUTPUT i
ENDFOR'''
    )
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "range(0, Limit)" in compiled.source_code
    assert "((Limit - 1) + 1)" not in compiled.source_code


def test_aj_range_compiles_end_exclusively_without_implicit_plus_one():
    parsed = AJParserFacade().parse(
        '''FOR i <- IN RANGE 1 TO 4 DO
    OUTPUT i
ENDFOR'''
    )
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert "range(1, 4)" in compiled.source_code
    assert "+ 1" not in compiled.source_code


def test_range_compiler_combines_positive_and_negative_integer_offsets():
    cases = [
        ("(Index + 3) - 1", "range(0, Index + 2)"),
        ("(Value - 4) - 2", "range(0, Value - 6)"),
        ("(Value + 2) - 2", "range(0, Value)"),
        ("((Limit - 2) - i) + 1", "range(0, Limit - 1 - i)"),
    ]
    for endpoint, expected in cases:
        parsed = AJParserFacade().parse(
            f"FOR i <- IN RANGE 0 TO {endpoint} DO\n    OUTPUT i\nENDFOR"
        )
        assert parsed.success, parsed.error
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        assert expected in compiled.source_code


def test_range_compiler_does_not_fold_single_integer_offset_or_non_additive_math():
    cases = [
        ("Limit - 2", "range(0, (Limit - 2))"),
        ("(Limit * 2) + 1", "range(0, ((Limit * 2) + 1))"),
        ("Limit - (Other - 2)", "range(0, (Limit - (Other - 2)))"),
    ]
    for endpoint, expected in cases:
        parsed = AJParserFacade().parse(
            f"FOR i <- IN RANGE 0 TO {endpoint} DO\n    OUTPUT i\nENDFOR"
        )
        assert parsed.success, parsed.error
        compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
        assert expected in compiled.source_code
