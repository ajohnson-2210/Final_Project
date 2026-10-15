from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def _raw_algorithm5():
    return '''BEGIN
    INPUT Sentence
    Result <- ""

    FOR EACH Character IN Sentence
        IF Character is NOT punctuation THEN
            Result <- Result + Character
        ENDIF
    ENDFOR

    OUTPUT Result
END
'''


def test_source_a_algorithm5_undefined_punctuation_predicate_remains_expected_failure():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm5(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )

    processed = result.processed_source
    assert "INPUT Sentence" in processed
    assert 'Result <- ""' in processed
    assert "Character is NOT punctuation" in processed
    assert "Result <- Result + Character" in processed
    assert "OUTPUT Result" in processed

    # Do not hide the missing predicate semantics behind a generated helper or
    # a neutral wrapper merely to force parsing.
    assert "CALL is_punctuation" not in processed
    assert "FUNCTION unnamed_function" not in processed
    assert "FUNCTION PROCESS" not in processed
    assert all(t.rule != "GC104" for t in result.transformations)

    parsed = AJParserFacade().parse(processed)
    assert not parsed.success


def test_source_a_algorithm5_guard_does_not_choose_a_punctuation_definition():
    result = PseudocodeProfileProcessor().process(
        _raw_algorithm5(), PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    lowered = result.processed_source.lower()
    for forbidden in (
        "string.punctuation",
        "regex",
        "re.match",
        "unicode",
        "category(",
        "ispunct",
        "is_punctuation(",
    ):
        assert forbidden not in lowered
