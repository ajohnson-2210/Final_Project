from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def test_inline_slash_comment_is_detached_before_collection_interpretation():
    source = '''FUNCTION Example ACCEPTS()
    deque = empty DoubleEndedQueue // Stores indices
    RETURN deque
END FUNCTION
'''
    result = process(source)

    assert "deque <- CALL create_deque()" in result.processed_source
    assert "COMMENT Stores indices" in result.processed_source
    assert "EMPTY DEQUE" not in result.processed_source
    assert any(t.rule == "GC236" for t in result.transformations)

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_double_slash_inside_quoted_string_is_not_a_comment_marker():
    source = '''FUNCTION Example ACCEPTS()
    value <- STRING("https://example.test/a//b")
    RETURN value
ENDFUNCTION
'''
    result = process(source)

    assert 'STRING("https://example.test/a//b")' in result.processed_source
    assert not any(t.rule == "GC236" for t in result.transformations)

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error


def test_full_line_slash_comment_remains_non_executable_comment_metadata():
    source = '''FUNCTION Example ACCEPTS()
    // explanation only
    RETURN INTEGER(1)
ENDFUNCTION
'''
    result = process(source)

    assert "COMMENT explanation only" in result.processed_source
    assert not any(t.rule == "GC236" for t in result.transformations)

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
