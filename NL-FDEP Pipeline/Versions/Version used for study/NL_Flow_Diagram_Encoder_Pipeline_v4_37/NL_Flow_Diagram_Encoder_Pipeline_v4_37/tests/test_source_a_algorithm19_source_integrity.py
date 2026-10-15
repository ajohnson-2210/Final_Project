from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm19() -> str:
    return '''BEGIN
    INPUT A, B

    A ← A + B
    B ← A - B
    A ← A - B

    OUTPUT A, B
END
'''


def _lossy_export_algorithm19() -> str:
    # Mirrors only the three known arrow losses in the stored source_a TXT.
    # ``?`` is source-loss evidence, never AJ syntax or an alias for ``<-``.
    return _authoritative_algorithm19().replace('←', '?')


def _process(source: str):
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    return result, compiled.source_code


def test_algorithm19_authoritative_arrows_preserve_explicit_arithmetic_swap():
    result, python_source = _process(_authoritative_algorithm19())

    assert all(t.rule != 'GC193' for t in result.transformations)
    assert sum(t.rule == 'GC004' for t in result.transformations) == 3
    assert 'A <- A + B' in result.processed_source
    assert 'B <- A - B' in result.processed_source
    assert 'A <- A - B' in result.processed_source
    assert 'CALL swap' not in result.processed_source
    assert 'temp' not in result.processed_source.lower()
    assert 'A = (A + B)' in python_source
    assert 'B = (A - B)' in python_source
    assert 'A = (A - B)' in python_source


def test_algorithm19_lossy_export_recovers_exact_three_arrows_before_canonical_aj():
    result, python_source = _process(_lossy_export_algorithm19())

    recoveries = [t for t in result.transformations if t.rule == 'GC193']
    assert len(recoveries) == 3
    assert all('?' in t.source and '←' in t.target for t in recoveries)
    assert sum(t.rule == 'GC004' for t in result.transformations) == 3
    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert result.processed_source.count('<-') == 3
    assert 'CALL swap' not in result.processed_source
    assert 'A = (A + B)' in python_source


def test_algorithm19_generic_recovery_handles_arithmetic_assignments():
    unrelated = """BEGIN
    INPUT A, B
    A ? A * B
    B ? A / B
    A ? A / B
    OUTPUT A, B
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
