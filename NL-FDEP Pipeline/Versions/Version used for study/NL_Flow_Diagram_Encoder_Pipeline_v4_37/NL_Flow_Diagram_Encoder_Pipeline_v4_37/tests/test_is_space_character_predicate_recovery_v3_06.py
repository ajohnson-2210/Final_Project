import pytest

from pseudocode_profiles import (
    GenericObviousMismatchNormaliser,
    PseudocodeProfile,
    PseudocodeProfileProcessor,
)


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def test_generic_identifier_is_space_maps_to_single_space_char_equality():
    source = '''INPUT token
IF token is space:
    RETURN TRUE
ELSE:
    RETURN FALSE
'''
    result = _process(source)
    assert 'IF token == CHAR(" ") THEN' in result.processed_source
    assert any(item.rule == 'GC207' for item in result.transformations)


def test_generic_is_space_recovery_is_case_insensitive_and_composes_in_condition():
    source = '''INPUT token, enabled
IF token IS SPACE AND enabled == TRUE:
    RETURN TRUE
ELSE:
    RETURN FALSE
'''
    result = _process(source)
    assert 'token == CHAR(" ") AND enabled == BOOLEAN(True)' in result.processed_source
    assert any(item.rule == 'GC207' for item in result.transformations)


@pytest.mark.parametrize('phrase', ['is whitespace', 'is blank', 'is empty', 'is a space'])
def test_broader_or_different_space_phrases_are_not_recovered(phrase):
    normaliser = GenericObviousMismatchNormaliser()
    source = f'IF token {phrase} THEN'
    processed, transformations = normaliser.process(source)
    assert 'CHAR(" ")' not in processed
    assert not any(item.rule == 'GC207' for item in transformations)


def test_is_space_text_inside_quoted_string_is_untouched():
    result = _process('OUTPUT "token is space"')
    assert 'STRING("token is space")' in result.processed_source
    assert not any(item.rule == 'GC207' for item in result.transformations)


def test_is_space_text_inside_comment_or_inline_comment_is_untouched():
    normaliser = GenericObviousMismatchNormaliser()

    comment, comment_changes = normaliser.process('COMMENT token is space')
    assert comment == 'COMMENT token is space'
    assert not any(item.rule == 'GC207' for item in comment_changes)

    inline, inline_changes = normaliser.process('IF ready == TRUE THEN # token is space')
    assert inline.endswith('# token is space')
    assert 'CHAR(" ")' not in inline
    assert not any(item.rule == 'GC207' for item in inline_changes)


def test_unrelated_identifier_containing_space_word_is_not_rewritten():
    normaliser = GenericObviousMismatchNormaliser()
    source = 'IF namespace == space_value THEN'
    processed, transformations = normaliser.process(source)
    assert processed == source
    assert not any(item.rule == 'GC207' for item in transformations)
