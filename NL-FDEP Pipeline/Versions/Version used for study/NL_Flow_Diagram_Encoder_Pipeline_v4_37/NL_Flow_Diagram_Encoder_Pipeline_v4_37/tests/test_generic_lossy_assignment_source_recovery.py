from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def test_gc193_recovers_only_unambiguous_assignment_positions():
    source = """BEGIN
    INPUT Values, Limit
    Total ? 0
    Values[0] ? 1
    FOR i ? 1 TO Limit
        Total ? Total + Values[i]
    ENDFOR
    CASE Total OF
        1: Total ? Total + 1
    ENDCASE
    OUTPUT Total
END
"""
    result = _process(source)
    recoveries = [t for t in result.transformations if t.rule == 'GC193']
    assert len(recoveries) == 5
    assert all('?' in t.source and '←' in t.target for t in recoveries)
    assert '?' not in result.processed_source
    assert '←' not in result.processed_source
    assert '<-' in result.processed_source


def test_gc193_leaves_relational_question_marks_unresolved():
    source = """BEGIN
    INPUT A, B
    A ? 1
    WHILE B ? 0
        A ? A + 1
    ENDWHILE
    IF A ? B THEN
        OUTPUT A
    ENDIF
END
"""
    result = _process(source)
    recoveries = [t for t in result.transformations if t.rule == 'GC193']
    assert len(recoveries) == 2
    assert 'WHILE B ? 0 DO' in result.processed_source
    assert 'IF A ? B THEN' in result.processed_source
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success


def test_strict_aj_still_rejects_question_mark_as_assignment_token():
    parsed = AJParserFacade().parse('Value ? 1\n')
    assert not parsed.success
