from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm14() -> str:
    return '''BEGIN
    INPUT Numbers

    Sum ← 0

    FOR EACH Number IN Numbers
        IF Number MOD 2 = 0 THEN
            Sum ← Sum + Number
        ENDIF
    ENDFOR

    OUTPUT Sum
END
'''


def _lossy_export_algorithm14() -> str:
    # Mirrors only the two known arrow losses in the stored source_a TXT.
    # ``?`` is source-loss evidence, never AJ syntax or an alias for ``<-``.
    return _authoritative_algorithm14().replace('←', '?')


def _process(source: str):
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    return result, compiled.source_code


def test_algorithm14_authoritative_arrows_use_normal_gc004_only():
    result, python_source = _process(_authoritative_algorithm14())

    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert sum(t.rule == 'GC004' for t in result.transformations) == 2
    assert all(t.rule != 'GC193' for t in result.transformations)
    assert 'Sum <- 0' in result.processed_source
    assert 'Number MODULUS 2 == 0' in result.processed_source
    assert 'Sum <- Sum + Number' in result.processed_source
    assert '(Number % 2) == 0' in python_source


def test_algorithm14_lossy_export_recovers_exact_two_arrows_before_canonical_aj():
    result, python_source = _process(_lossy_export_algorithm14())

    recoveries = [t for t in result.transformations if t.rule == 'GC193']
    assert len(recoveries) == 2
    assert all('?' in t.source and '←' in t.target for t in recoveries)
    assert sum(t.rule == 'GC004' for t in result.transformations) == 2
    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert result.processed_source.count('<-') == 2
    assert 'Sum <- Sum + Number' in result.processed_source
    assert '(Number % 2) == 0' in python_source


def test_algorithm14_generic_recovery_handles_unambiguous_accumulator_assignments():
    unrelated = """BEGIN
    INPUT Numbers
    Total ? 0
    FOR EACH Number IN Numbers
        IF Number MOD 2 = 0 THEN
            Total ? Total + Number
        ENDIF
    ENDFOR
    OUTPUT Total
END
"""
    result = PseudocodeProfileProcessor().process(
        unrelated, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    recoveries = [t for t in result.transformations if t.rule == 'GC193']
    assert len(recoveries) == 2
    assert '?' not in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
