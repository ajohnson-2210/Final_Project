from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm11() -> str:
    return '''BEGIN
    INPUT IP_List

    UniqueIPs ← Empty Set

    FOR EACH IP IN IP_List
        ADD IP TO UniqueIPs
    ENDFOR

    OUTPUT UniqueIPs
END
'''


def _lossy_export_algorithm11() -> str:
    # Mirrors the isolated stored source_a TXT corruption. ``?`` is source-loss
    # evidence only; it is never AJ syntax or a canonical alias for ``<-``.
    return _authoritative_algorithm11().replace('UniqueIPs ← Empty Set', 'UniqueIPs ? Empty Set')


def _process(source: str):
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    return result, compiled.source_code


def test_algorithm11_authoritative_arrow_uses_normal_gc004_only():
    result, python_source = _process(_authoritative_algorithm11())

    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert 'UniqueIPs <- EMPTY SET' in result.processed_source
    assert sum(t.rule == 'GC004' for t in result.transformations) == 1
    assert all(t.rule != 'GC193' for t in result.transformations)
    assert 'CALL add_to_set(UniqueIPs, IP)' in result.processed_source
    assert 'UniqueIPs = set()' in python_source
    assert 'UniqueIPs.add(IP)' in python_source


def test_algorithm11_lossy_export_recovers_one_arrow_before_canonical_aj():
    result, python_source = _process(_lossy_export_algorithm11())

    recoveries = [t for t in result.transformations if t.rule == 'GC193']
    assert len(recoveries) == 1
    assert '?' in recoveries[0].source
    assert '←' in recoveries[0].target
    assert sum(t.rule == 'GC004' for t in result.transformations) == 1
    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert 'UniqueIPs <- EMPTY SET' in result.processed_source
    assert 'UniqueIPs.add(IP)' in python_source


def test_algorithm11_unambiguous_assignment_question_mark_uses_generic_source_recovery():
    unrelated = """BEGIN
    INPUT Values
    Result ? Empty Set
    OUTPUT Result
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
