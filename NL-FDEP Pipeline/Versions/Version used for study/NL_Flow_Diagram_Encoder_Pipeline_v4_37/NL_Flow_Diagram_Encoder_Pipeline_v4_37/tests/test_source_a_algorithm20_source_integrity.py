from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm20() -> str:
    return '''BEGIN
    INPUT Number

    FOR i ← 1 TO Number
        IF Number MOD i = 0 THEN
            OUTPUT i
        ENDIF
    ENDFOR
END
'''


def _lossy_export_algorithm20() -> str:
    return _authoritative_algorithm20().replace('FOR i ← 1 TO Number', 'FOR i ? 1 TO Number')


def _process(source: str):
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    return result, compiled.source_code


def test_algorithm20_authoritative_arrow_needs_no_lossy_recovery_and_preserves_inclusive_end():
    result, python_source = _process(_authoritative_algorithm20())

    assert all(t.rule != 'GC193' for t in result.transformations)
    assert sum(t.rule == 'GC004' for t in result.transformations) == 1
    assert 'FOR i <- IN RANGE 1 TO (Number) + 1 DO' in result.processed_source
    assert 'IF Number MODULUS i == 0 THEN' in result.processed_source
    assert 'for i in range(1, (Number + 1)):' in python_source


def test_algorithm20_lossy_export_recovers_exact_loop_arrow_before_canonical_aj():
    result, python_source = _process(_lossy_export_algorithm20())

    recoveries = [t for t in result.transformations if t.rule == 'GC193']
    assert len(recoveries) == 1
    assert '?' in recoveries[0].source and '←' in recoveries[0].target
    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert 'FOR i <- IN RANGE 1 TO (Number) + 1 DO' in result.processed_source
    assert 'for i in range(1, (Number + 1)):' in python_source


def test_algorithm20_generic_recovery_handles_for_initialiser_assignment_position():
    unrelated = """BEGIN
    INPUT Limit
    FOR i ? 1 TO Limit
        OUTPUT i
    ENDFOR
END
"""
    result = PseudocodeProfileProcessor().process(
        unrelated, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    recoveries = [t for t in result.transformations if t.rule == 'GC193']
    assert len(recoveries) == 1
    assert '?' not in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
