from aj_parser import AJParserFacade
from pseudocode_profiles import (
    GenericCharacterNormaliser,
    GenericPseudocodeProcessor,
    PseudocodeProfile,
    PseudocodeProfileProcessor,
)


def test_canonical_character_lookup_is_explicit_and_never_maps_question_mark():
    lookup = GenericCharacterNormaliser.CANONICAL_CHARACTER_LOOKUP
    assert lookup["←"][0] == "<-"
    assert lookup["≠"][0] == "!="
    assert lookup["≤"][0] == "<="
    assert lookup["≥"][0] == ">="
    assert "?" not in lookup


def test_evidence_table_contains_known_relational_cases_including_algorithm37():
    table = GenericPseudocodeProcessor.EVIDENCE_BACKED_GLYPH_RECOVERIES
    case_ids = {entry.case_id for entry in table}
    assert {
        "A1_ANAGRAM_LENGTH_NE",
        "A33_BINARY_SQRT_LE",
        "A36_ROTATED_SEARCH_RELATIONS",
        "A37_STACK_PEEK_NE",
    } <= case_ids
    recovered = {
        replacement.recovered_glyph
        for entry in table
        for replacement in entry.replacements
    }
    assert {"≠", "≤", "≥"} <= recovered


def test_question_mark_remains_invalid_when_neither_assignment_nor_evidence_matches():
    source = """BEGIN
    INPUT Left, Right
    IF Left ? Right THEN
        OUTPUT Left
    ENDIF
END
"""
    result = PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )
    assert "?" in result.processed_source
    assert all(not t.rule.startswith("GC194:") for t in result.transformations)
    parsed = AJParserFacade().parse(result.processed_source)
    assert not parsed.success
