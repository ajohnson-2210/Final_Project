from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm10() -> str:
    return '''BEGIN
    INPUT Text

    A ← 0
    E ← 0
    I ← 0
    O ← 0
    U ← 0

    FOR EACH Character IN LOWERCASE(Text)
        CASE Character OF
            'a': A ← A + 1
            'e': E ← E + 1
            'i': I ← I + 1
            'o': O ← O + 1
            'u': U ← U + 1
        ENDCASE
    ENDFOR

    OUTPUT A, E, I, O, U
END
'''


def _lossy_export_algorithm10() -> str:
    # Mirrors the stored source_a TXT export only. The authoritative source uses
    # left arrows; ``?`` is not AJ syntax and is not a canonical assignment alias.
    return _authoritative_algorithm10().replace('←', '?')


def _process(source: str):
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    return result, compiled.source_code


def test_algorithm10_authoritative_arrows_use_normal_gc004_only():
    result, python_source = _process(_authoritative_algorithm10())

    assert '?' not in result.processed_source
    assert result.processed_source.count('<-') == 10
    assert sum(t.rule == 'GC004' for t in result.transformations) == 10
    assert all(t.rule != 'GC193' for t in result.transformations)
    assert 'FOR EACH Character IN CALL lowercase(Text) DO' in result.processed_source
    assert 'OUTPUT CALL output_values(A, E, I, O, U)' in result.processed_source
    assert 'print(A, E, I, O, U)' in python_source
    assert 'for Character in str(Text).lower():' in python_source


def test_algorithm10_lossy_export_recovers_exact_ten_arrows_before_canonical_aj():
    result, python_source = _process(_lossy_export_algorithm10())

    recoveries = [t for t in result.transformations if t.rule == 'GC193']
    assert len(recoveries) == 10
    assert all('?' in t.source and '←' in t.target for t in recoveries)
    assert sum(t.rule == 'GC004' for t in result.transformations) == 10
    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert result.processed_source.count('<-') == 10
    assert 'A <- 0' in result.processed_source
    assert 'A <- A + 1' in result.processed_source
    assert 'for Character in str(Text).lower():' in python_source
