from aj_parser import AJParserFacade


def parse(source: str):
    return AJParserFacade().parse(source)


def test_join_rejects_known_integer_list_elements():
    result = parse('''FUNCTION demo ACCEPTS()
    values <- LIST OF INTEGER [INTEGER(1), INTEGER(2)]
    RETURN JOIN(values, STRING(","))
ENDFUNCTION
''')
    assert not result.success
    assert 'JOIN collection elements must be STRING/CHAR-compatible' in result.error


def test_join_rejects_known_non_text_separator():
    result = parse('''FUNCTION demo ACCEPTS()
    values <- LIST OF STRING [STRING("a"), STRING("b")]
    RETURN JOIN(values, INTEGER(1))
ENDFUNCTION
''')
    assert not result.success
    assert 'JOIN separator must be STRING/CHAR-compatible' in result.error


def test_join_accepts_known_string_and_char_lists():
    for source in (
        '''FUNCTION demo ACCEPTS()
    values <- LIST OF STRING [STRING("a"), STRING("b")]
    RETURN JOIN(values, STRING(","))
ENDFUNCTION
''',
        '''FUNCTION demo ACCEPTS()
    values <- LIST OF CHAR [CHAR("a"), CHAR("b")]
    RETURN JOIN(values, EMPTY STRING)
ENDFUNCTION
''',
    ):
        result = parse(source)
        assert result.success, result.error


def test_join_keeps_unknown_collection_and_separator_types_unknown():
    result = parse('''FUNCTION demo ACCEPTS(values, separator)
    RETURN JOIN(values, separator)
ENDFUNCTION
''')
    assert result.success, result.error


def test_join_tracks_typed_list_assignment_through_identifier_copy():
    result = parse('''FUNCTION demo ACCEPTS()
    source <- LIST OF INTEGER [INTEGER(1)]
    values <- source
    RETURN JOIN(values, EMPTY STRING)
ENDFUNCTION
''')
    assert not result.success
    assert 'found INTEGER' in result.error


def test_join_branch_merge_keeps_only_agreed_element_type():
    bad = parse('''FUNCTION demo ACCEPTS(flag AS BOOLEAN)
    IF flag THEN
        values <- LIST OF INTEGER [INTEGER(1)]
    ELSE
        values <- LIST OF INTEGER [INTEGER(2)]
    ENDIF
    RETURN JOIN(values, EMPTY STRING)
ENDFUNCTION
''')
    assert not bad.success
    assert 'found INTEGER' in bad.error

    unknown = parse('''FUNCTION demo ACCEPTS(flag AS BOOLEAN)
    IF flag THEN
        values <- LIST OF INTEGER [INTEGER(1)]
    ELSE
        values <- LIST OF STRING [STRING("x")]
    ENDIF
    RETURN JOIN(values, EMPTY STRING)
ENDFUNCTION
''')
    # The branches disagree, so element type is deliberately unknown rather
    # than guessed from either branch.
    assert unknown.success, unknown.error


def test_nested_parameter_shadows_enclosing_typed_list_element_evidence():
    result = parse('''FUNCTION outer ACCEPTS()
    values <- LIST OF INTEGER [INTEGER(1)]
    FUNCTION inner ACCEPTS(values)
        RETURN JOIN(values, EMPTY STRING)
    ENDFUNCTION
    RETURN CALL inner(LIST OF STRING [STRING("x")])
ENDFUNCTION
''')
    assert result.success, result.error
