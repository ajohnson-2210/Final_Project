from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


SOURCE = """BEGIN
    INPUT Text

    COUNT frequency of each character

    FOR EACH Character IN Text
        IF Frequency(Character) = 1 THEN
            OUTPUT Character
            STOP
        ENDIF
    ENDFOR

    OUTPUT "None Found"
END
"""


def test_source_a_algorithm38_abstract_count_is_expected_failure():
    result = PseudocodeProfileProcessor().process(SOURCE, PseudocodeProfile.GENERIC_COMPATIBILITY)

    # GC122 is retired: the abstract COUNT operation must remain visible and
    # must not be expanded into a dictionary-counting algorithm.
    assert "COUNT frequency of each character" in result.processed_source
    assert "Frequency <- EMPTY DICTIONARY" not in result.processed_source
    assert "IF Character IN Frequency THEN" not in result.processed_source
    assert "Frequency[Character] <- Frequency[Character] + 1" not in result.processed_source
    assert result.processed_source.count("FOR EACH Character IN Text DO") == 1
    assert not any(t.rule == "GC122" for t in result.transformations)

    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success
    assert "Expected assignment or CALL statement" in (parsed.error or "")


def test_source_a_algorithm38_expected_failure_stops_before_python_generation():
    result = PseudocodeProfileProcessor().process(SOURCE, PseudocodeProfile.GENERIC_COMPATIBILITY)
    parsed = AJParserFacade().parse(result.processed_source)

    # This historical corpus item is intentionally unresolved.  There is no
    # valid AJ AST, so the pipeline must not manufacture executable Python for
    # it by supplying a missing frequency-count implementation.
    assert not parsed.success
    assert parsed.ast is None
