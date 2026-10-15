from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm13() -> str:
    return '''BEGIN
    INPUT Text

    Reverse ← ""

    FOR i ← LENGTH(Text)-1 DOWNTO 0
        Reverse ← Reverse + Text[i]
    ENDFOR

    OUTPUT Reverse
END
'''


def _lossy_export_algorithm13() -> str:
    # Mirrors only the three known arrow losses in the stored source_a TXT.
    # ``?`` is source-loss evidence, never AJ syntax or an alias for ``<-``.
    return _authoritative_algorithm13().replace('←', '?')


def _process(source: str):
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    return result, compiled.source_code


def test_algorithm13_authoritative_arrows_use_normal_gc004_only():
    result, python_source = _process(_authoritative_algorithm13())

    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert sum(t.rule == 'GC004' for t in result.transformations) == 3
    assert all(t.rule != 'GC193' for t in result.transformations)
    assert 'Reverse <- EMPTY STRING' in result.processed_source
    assert 'FOR i <- IN RANGE LENGTH OF Text-1 TO (0) - 1 STEP -1 DO' in result.processed_source
    assert 'Reverse <- Reverse + Text[i]' in result.processed_source
    assert 'for i in range((len(Text) - 1), (0 - 1), (-1)):' in python_source
    assert 'reversed(' not in python_source
    assert '[::-1]' not in python_source


def test_algorithm13_lossy_export_recovers_exact_three_arrows_before_canonical_aj():
    result, python_source = _process(_lossy_export_algorithm13())

    recoveries = [t for t in result.transformations if t.rule == 'GC193']
    assert len(recoveries) == 3
    assert all('?' in t.source and '←' in t.target for t in recoveries)
    assert sum(t.rule == 'GC004' for t in result.transformations) == 3
    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert result.processed_source.count('<-') == 3
    assert 'FOR i <- IN RANGE LENGTH OF Text-1 TO (0) - 1 STEP -1 DO' in result.processed_source
    assert 'reversed(' not in python_source
    assert '[::-1]' not in python_source


def test_algorithm13_generic_recovery_handles_descending_for_assignment_positions():
    unrelated = """BEGIN
    INPUT Text
    Result ? ""
    FOR i ? LENGTH(Text)-1 DOWNTO 0
        Result ? Result + Text[i]
    ENDFOR
    OUTPUT Result
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
