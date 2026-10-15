from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm16() -> str:
    return '''BEGIN
    INPUT A, B

    WHILE B ≠ 0
        Temp ← B
        B ← A MOD B
        A ← Temp
    ENDWHILE

    OUTPUT A
END
'''


def _lossy_export_algorithm16() -> str:
    # Mirrors exactly the one lost ≠ glyph and three lost assignment arrows in
    # the stored source_a TXT export. ``?`` is source-loss evidence only.
    return '''BEGIN
    INPUT A, B

    WHILE B ? 0
        Temp ? B
        B ? A MOD B
        A ? Temp
    ENDWHILE

    OUTPUT A
END
'''


def _process(source: str):
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    return result, compiled.source_code


def test_algorithm16_authoritative_symbols_use_only_normal_canonical_rules():
    result, python_source = _process(_authoritative_algorithm16())

    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert '≠' not in result.processed_source
    assert sum(t.rule == 'GC004' for t in result.transformations) == 3
    assert all(t.rule not in {'GC193', 'GC187'} for t in result.transformations)
    assert 'WHILE B != 0 DO' in result.processed_source
    assert 'Temp <- B' in result.processed_source
    assert 'B <- A MODULUS B' in result.processed_source
    assert 'A <- Temp' in result.processed_source
    assert 'while (B != 0):' in python_source
    assert 'B = (A % B)' in python_source


def test_algorithm16_lossy_export_recovers_three_arrows_and_one_not_equal_upstream():
    result, python_source = _process(_lossy_export_algorithm16())

    arrows = [t for t in result.transformations if t.rule == 'GC193']
    not_equal = [t for t in result.transformations if t.rule == 'GC187']
    assert len(arrows) == 3
    assert len(not_equal) == 1
    assert all('?' in t.source and '←' in t.target for t in arrows)
    assert '?' in not_equal[0].source and '≠' in not_equal[0].target
    assert sum(t.rule == 'GC004' for t in result.transformations) == 3
    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert '≠' not in result.processed_source
    assert 'WHILE B != 0 DO' in result.processed_source
    assert result.processed_source.count('<-') == 3
    assert 'while (B != 0):' in python_source


def test_algorithm16_generic_arrow_recovery_does_not_infer_relational_glyph():
    unrelated = """BEGIN
    INPUT X, Y
    WHILE Y ? 0
        Temp ? Y
        Y ? X MOD Y
        X ? Temp
    ENDWHILE
    OUTPUT X
END
"""
    result = PseudocodeProfileProcessor().process(
        unrelated, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    arrows = [t for t in result.transformations if t.rule == 'GC193']
    assert len(arrows) == 3
    assert all(t.rule != 'GC187' for t in result.transformations)
    assert 'WHILE Y ? 0' in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success
