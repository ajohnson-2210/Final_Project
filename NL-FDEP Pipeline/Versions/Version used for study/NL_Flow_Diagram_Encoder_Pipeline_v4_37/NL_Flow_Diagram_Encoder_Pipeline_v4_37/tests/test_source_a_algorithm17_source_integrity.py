from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm17() -> str:
    return '''BEGIN
    INPUT Numbers

    Sum ← 0

    FOR EACH Number IN Numbers
        Sum ← Sum + Number
    ENDFOR

    Average ← Sum / LENGTH(Numbers)

    OUTPUT Sum
    OUTPUT Average
END
'''


def _lossy_export_algorithm17() -> str:
    # Mirrors only the three known arrow losses in the stored source_a TXT.
    # ``?`` is source-loss evidence, never AJ syntax or an alias for ``<-``.
    return _authoritative_algorithm17().replace('←', '?')


def _process(source: str):
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    return result, compiled.source_code


def test_algorithm17_authoritative_arrows_use_normal_gc004_only():
    result, python_source = _process(_authoritative_algorithm17())

    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert sum(t.rule == 'GC004' for t in result.transformations) == 3
    assert all(t.rule != 'GC193' for t in result.transformations)
    assert 'Sum <- 0' in result.processed_source
    assert 'Sum <- Sum + Number' in result.processed_source
    assert 'Average <- Sum / LENGTH OF Numbers' in result.processed_source
    assert 'for Number in Numbers:' in python_source
    assert 'Average = (Sum / len(Numbers))' in python_source


def test_algorithm17_lossy_export_recovers_exact_three_arrows_before_canonical_aj():
    result, python_source = _process(_lossy_export_algorithm17())

    recoveries = [t for t in result.transformations if t.rule == 'GC193']
    assert len(recoveries) == 3
    assert all('?' in t.source and '←' in t.target for t in recoveries)
    assert sum(t.rule == 'GC004' for t in result.transformations) == 3
    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert result.processed_source.count('<-') == 3
    assert 'Average <- Sum / LENGTH OF Numbers' in result.processed_source
    assert 'Average = (Sum / len(Numbers))' in python_source


def test_algorithm17_generic_recovery_handles_unambiguous_assignments():
    unrelated = """BEGIN
    INPUT Numbers
    Total ? 0
    FOR EACH Number IN Numbers
        Total ? Total + Number
    ENDFOR
    Mean ? Total / LENGTH(Numbers)
    OUTPUT Total
    OUTPUT Mean
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
