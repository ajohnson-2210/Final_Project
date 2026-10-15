from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _authoritative_algorithm18() -> str:
    return '''BEGIN
    INPUT Text

    Create empty Dictionary

    FOR EACH Character IN Text
        IF Character EXISTS in Dictionary THEN
            Dictionary[Character] ← Dictionary[Character] + 1
        ELSE
            Dictionary[Character] ← 1
        ENDIF
    ENDFOR

    OUTPUT Dictionary
END
'''


def _lossy_export_algorithm18() -> str:
    # Only the two known assignment-arrow losses from the stored source_a TXT.
    # ``?`` remains source-loss evidence and never canonical AJ syntax.
    return _authoritative_algorithm18().replace('←', '?')


def _process(source: str):
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    return result, compiled.source_code


def test_algorithm18_authoritative_source_resolves_dictionary_from_unique_usage():
    result, python_source = _process(_authoritative_algorithm18())

    assert all(t.rule != 'GC193' for t in result.transformations)
    assert sum(t.rule == 'GC004' for t in result.transformations) == 2
    assert sum(t.rule == 'GC190' for t in result.transformations) == 1
    assert 'Dictionary <- EMPTY DICTIONARY' in result.processed_source
    assert 'Anonymous_Dictionary' not in result.processed_source
    assert 'IF Character IN Dictionary THEN' in result.processed_source
    assert 'Dictionary[Character] <- Dictionary[Character] + 1' in result.processed_source
    assert 'Dictionary = {}' in python_source
    assert 'if (Character in Dictionary):' in python_source
    assert 'Dictionary[Character] = (Dictionary[Character] + 1)' in python_source


def test_algorithm18_lossy_export_recovers_exact_two_arrows_before_strict_aj():
    result, python_source = _process(_lossy_export_algorithm18())

    recoveries = [t for t in result.transformations if t.rule == 'GC193']
    assert len(recoveries) == 2
    assert all('?' in t.source and '←' in t.target for t in recoveries)
    assert sum(t.rule == 'GC004' for t in result.transformations) == 2
    assert sum(t.rule == 'GC190' for t in result.transformations) == 1
    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert 'Dictionary <- EMPTY DICTIONARY' in result.processed_source
    assert 'Dictionary = {}' in python_source


def test_type_only_dictionary_resolution_requires_unique_downstream_state():
    ambiguous = '''FUNCTION example ACCEPTS(Text)
    CREATE EMPTY DICTIONARY
    IF Text IN FirstDictionary THEN
        FirstDictionary[Text] <- 1
    ENDIF
    SecondDictionary[Text] <- 2
    OUTPUT FirstDictionary
ENDFUNCTION
'''
    result = PseudocodeProfileProcessor().process(
        ambiguous, PseudocodeProfile.GENERIC_COMPATIBILITY
    )

    assert all(t.rule != 'GC190' for t in result.transformations)
    assert 'Anonymous_Dictionary <- EMPTY DICTIONARY' in result.processed_source


def test_algorithm18_generic_recovery_handles_indexed_assignment_targets():
    unrelated = """BEGIN
    INPUT Text
    Create empty Dictionary
    FOR EACH Character IN Text
        IF Character EXISTS in Counts THEN
            Counts[Character] ? Counts[Character] + 1
        ELSE
            Counts[Character] ? 1
        ENDIF
    ENDFOR
    OUTPUT Counts
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
