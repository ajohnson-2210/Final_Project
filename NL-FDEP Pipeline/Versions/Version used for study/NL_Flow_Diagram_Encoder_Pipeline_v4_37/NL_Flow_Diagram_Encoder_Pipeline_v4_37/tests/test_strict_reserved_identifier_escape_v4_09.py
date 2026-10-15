from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def process(source: str):
    return PseudocodeProfileProcessor().process(source, PseudocodeProfile.AJ_DIALECT_STRICT)


def test_strict_assignment_lhs_proves_string_is_identifier_and_preserves_constructor():
    result = process('string <- STRING("1a23")\nOUTPUT string')
    assert result.processed_source == '__reserved_keyword__string <- STRING("1a23")\nOUTPUT __reserved_keyword__string'
    audit = result.to_dict()['transformations']
    escaped = [t for t in audit if t['rule_family'] == 'RESERVED_IDENTIFIER_ESCAPE']
    assert escaped
    assert all(t['confidence'] == 'source_proven' for t in escaped)
    assert all(t['semantic_change'] is False for t in escaped)
    assert AJParserFacade().parse(result.processed_source).success


def test_strict_for_each_binder_proves_char_is_identifier_and_preserves_char_constructor():
    source = 'items <- LIST OF CHAR [CHAR("a")]\nFOR EACH char IN items DO\nOUTPUT char\nENDFOR'
    result = process(source)
    assert 'LIST OF CHAR [CHAR("a")]' in result.processed_source
    assert 'FOR EACH __reserved_keyword__char IN items DO' in result.processed_source
    assert 'OUTPUT __reserved_keyword__char' in result.processed_source
    assert AJParserFacade().parse(result.processed_source).success


def test_strict_reserved_lhs_rule_is_general_for_type_keyword_identifiers():
    source = '\n'.join([
        'string <- STRING("x")',
        'integer <- INTEGER(1)',
        'char <- CHAR("a")',
        'list <- EMPTY LIST',
        'OUTPUT string',
        'OUTPUT integer',
        'OUTPUT char',
        'OUTPUT list',
    ])
    result = process(source)
    for name in ('string', 'integer', 'char', 'list'):
        assert f'__reserved_keyword__{name}' in result.processed_source
    assert 'STRING("x")' in result.processed_source
    assert 'INTEGER(1)' in result.processed_source
    assert 'CHAR("a")' in result.processed_source
    assert 'EMPTY LIST' in result.processed_source
    assert AJParserFacade().parse(result.processed_source).success


def test_reserved_escape_never_rewrites_quoted_text():
    result = process('string <- STRING("string CHAR LIST")\nOUTPUT string')
    assert 'STRING("string CHAR LIST")' in result.processed_source
    assert '__reserved_keyword__string <-' in result.processed_source


def test_user_anagram_sample_advances_past_keyword_collision_to_top_level_return_rule():
    source = '''string <- STRING("1a23")
string1 <- EMPTY STRING
FOR EACH char IN string DO
    IF CALL ISALPHA(char) THEN
        string1 <- string1 + CALL LOWERCASE(char)
    ENDIF
ENDFOR
IF LENGTH OF string1 == 0 THEN
    RETURN
ENDIF'''
    result = process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert '__reserved_keyword__string <- STRING("1a23")' in result.processed_source
    assert 'FOR EACH __reserved_keyword__char IN __reserved_keyword__string DO' in result.processed_source
    assert parsed.success is False
    assert parsed.error is not None
    assert 'RETURN outside function' in parsed.error
    assert "Expected '('" not in parsed.error


def test_v1_3_quit_keyword_still_uses_general_reserved_identifier_escape_when_bound():
    result = process('quit <- BOOLEAN(FALSE)\nOUTPUT quit\n')
    assert '__reserved_keyword__quit <- BOOLEAN(FALSE)' in result.processed_source
    assert 'OUTPUT __reserved_keyword__quit' in result.processed_source
    assert AJParserFacade().parse(result.processed_source).success
