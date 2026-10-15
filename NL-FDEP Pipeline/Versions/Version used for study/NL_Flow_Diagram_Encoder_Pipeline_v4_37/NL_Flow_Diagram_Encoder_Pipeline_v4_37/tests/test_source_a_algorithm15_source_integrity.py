from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm15() -> str:
    return '''BEGIN
    INPUT Array

    Largest ← -∞
    SecondLargest ← -∞

    FOR EACH Number IN Array
        IF Number > Largest THEN
            SecondLargest ← Largest
            Largest ← Number
        ELSE IF Number > SecondLargest AND Number < Largest THEN
            SecondLargest ← Number
        ENDIF
    ENDFOR

    OUTPUT SecondLargest
END
'''


def _lossy_export_algorithm15() -> str:
    # Mirrors exactly the five lost arrows and two lost infinity glyphs in the
    # stored source_a TXT export. ``?`` is source-loss evidence only.
    return '''BEGIN
    INPUT Array

    Largest ? -?
    SecondLargest ? -?

    FOR EACH Number IN Array
        IF Number > Largest THEN
            SecondLargest ? Largest
            Largest ? Number
        ELSE IF Number > SecondLargest AND Number < Largest THEN
            SecondLargest ? Number
        ENDIF
    ENDFOR

    OUTPUT SecondLargest
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


def test_algorithm15_authoritative_symbols_use_only_normal_canonical_rules():
    result, python_source = _process(_authoritative_algorithm15())

    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert '∞' not in result.processed_source
    assert sum(t.rule == 'GC004' for t in result.transformations) == 5
    assert sum(t.rule == 'GC006' for t in result.transformations) == 2
    assert sum(t.rule == 'GC151' for t in result.transformations) == 2
    assert all(t.rule not in {'GC193', 'GC185'} for t in result.transformations)
    assert 'Largest <- CALL negative_infinity()' in result.processed_source
    assert 'SecondLargest <- CALL negative_infinity()' in result.processed_source
    assert "Largest = float('-inf')" in python_source
    assert "SecondLargest = float('-inf')" in python_source


def test_algorithm15_lossy_export_recovers_five_arrows_and_two_infinities_upstream():
    result, python_source = _process(_lossy_export_algorithm15())

    arrows = [t for t in result.transformations if t.rule == 'GC193']
    infinities = [t for t in result.transformations if t.rule == 'GC185']
    assert len(arrows) == 5
    assert len(infinities) == 2
    assert all('?' in t.source and '←' in t.target for t in arrows)
    assert all('-?' in t.source and '-∞' in t.target for t in infinities)
    assert sum(t.rule == 'GC004' for t in result.transformations) == 5
    assert sum(t.rule == 'GC006' for t in result.transformations) == 2
    assert sum(t.rule == 'GC151' for t in result.transformations) == 2
    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert '∞' not in result.processed_source
    assert result.processed_source.count('<-') == 5
    assert 'CALL negative_infinity()' in result.processed_source
    assert "float('-inf')" in python_source


def test_algorithm15_generic_arrow_recovery_does_not_infer_infinity_without_evidence():
    unrelated = """BEGIN
    INPUT Values
    Largest ? -?
    SecondLargest ? -?
    FOR EACH Number IN Values
        IF Number > Largest THEN
            SecondLargest ? Largest
            Largest ? Number
        ENDIF
    ENDFOR
    OUTPUT SecondLargest
END
"""
    result = PseudocodeProfileProcessor().process(
        unrelated, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    arrows = [t for t in result.transformations if t.rule == 'GC193']
    assert len(arrows) == 4
    assert all(t.rule != 'GC185' for t in result.transformations)
    assert '-?' in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success
