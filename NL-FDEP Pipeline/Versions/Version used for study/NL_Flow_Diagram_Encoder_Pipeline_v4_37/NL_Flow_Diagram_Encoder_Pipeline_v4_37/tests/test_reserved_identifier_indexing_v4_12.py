from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor
from aj_parser import AJParserFacade


def test_source_proven_list_identifier_propagates_through_indexing():
    source = """list <- LIST [1, 2, 3]
total <- list[0]
IF list[1] > 0 THEN
    total <- total + list[1]
ENDIF
"""
    processed = PseudocodeProfileProcessor().process(source, PseudocodeProfile.AJ_DIALECT_STRICT)
    assert "__reserved_keyword__list <- LIST [1, 2, 3]" in processed.processed_source
    assert "__reserved_keyword__list[0]" in processed.processed_source
    assert "__reserved_keyword__list[1]" in processed.processed_source
    result = AJParserFacade().parse(processed.processed_source)
    assert result.success, result.error


def test_list_literal_still_remains_literal():
    source = "values <- LIST [1, 2, 3]\n"
    processed = PseudocodeProfileProcessor().process(source, PseudocodeProfile.AJ_DIALECT_STRICT)
    assert "LIST [1, 2, 3]" in processed.processed_source
    assert "__reserved_keyword__LIST" not in processed.processed_source
