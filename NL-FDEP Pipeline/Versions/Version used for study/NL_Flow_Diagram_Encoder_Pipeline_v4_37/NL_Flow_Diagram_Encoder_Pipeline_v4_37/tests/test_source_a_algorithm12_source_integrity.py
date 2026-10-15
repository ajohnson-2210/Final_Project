from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm12() -> str:
    return '''BEGIN
    INPUT Matrix, N

    Sum ← 0

    FOR i ← 0 TO N - 1
        Sum ← Sum + Matrix[i][i]
    ENDFOR

    OUTPUT Sum
END
'''


def _lossy_export_algorithm12() -> str:
    # Mirrors only the three known arrow losses in the stored source_a TXT.
    # ``?`` is source-loss evidence, never AJ syntax or an alias for ``<-``.
    return _authoritative_algorithm12().replace('←', '?')


def _process(source: str):
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    return result, compiled.source_code


def test_algorithm12_authoritative_arrows_use_normal_gc004_only():
    result, python_source = _process(_authoritative_algorithm12())

    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert sum(t.rule == 'GC004' for t in result.transformations) == 3
    assert all(t.rule != 'GC193' for t in result.transformations)
    assert 'Sum <- 0' in result.processed_source
    assert 'FOR i <- IN RANGE 0 TO (N - 1) + 1 DO' in result.processed_source
    assert 'Sum <- Sum + Matrix[i][i]' in result.processed_source
    assert 'for i in range(0, N):' in python_source


def test_algorithm12_lossy_export_recovers_exact_three_arrows_before_canonical_aj():
    result, python_source = _process(_lossy_export_algorithm12())

    recoveries = [t for t in result.transformations if t.rule == 'GC193']
    assert len(recoveries) == 3
    assert all('?' in t.source and '←' in t.target for t in recoveries)
    assert sum(t.rule == 'GC004' for t in result.transformations) == 3
    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert result.processed_source.count('<-') == 3
    assert 'FOR i <- IN RANGE 0 TO (N - 1) + 1 DO' in result.processed_source
    assert 'for i in range(0, N):' in python_source


def test_algorithm12_generic_recovery_handles_standalone_and_for_assignments():
    unrelated = """BEGIN
    INPUT Matrix, N
    Total ? 0
    FOR i ? 0 TO N - 1
        Total ? Total + Matrix[i][i]
    ENDFOR
    OUTPUT Total
END
"""
    result = PseudocodeProfileProcessor().process(
        unrelated, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    recoveries = [t for t in result.transformations if t.rule == 'GC193']
    assert len(recoveries) == 3
    assert '?' not in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
