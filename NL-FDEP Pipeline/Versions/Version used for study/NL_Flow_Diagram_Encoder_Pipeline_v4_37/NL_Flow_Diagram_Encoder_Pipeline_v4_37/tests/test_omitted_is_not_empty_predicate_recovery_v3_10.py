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


def test_generic_identifier_not_empty_maps_to_existing_empty_state_form():
    source = '''INPUT items
WHILE items not empty:
    RETURN TRUE
RETURN FALSE
'''
    result = _process(source)
    assert 'WHILE LENGTH OF items > 0 DO' in result.processed_source
    assert any(item.rule == 'GC211' for item in result.transformations)


def test_omitted_is_not_empty_recovery_is_case_insensitive_and_composes():
    source = '''INPUT queue, enabled
WHILE queue NOT EMPTY AND enabled == TRUE:
    RETURN TRUE
RETURN FALSE
'''
    result = _process(source)
    assert 'WHILE LENGTH OF queue > 0 AND enabled == BOOLEAN(True) DO' in result.processed_source
    assert any(item.rule == 'GC211' for item in result.transformations)


def test_existing_is_not_empty_form_is_not_claimed_by_gc211():
    result = _process('''INPUT queue
WHILE queue IS NOT EMPTY:
    RETURN TRUE
RETURN FALSE
''')
    assert 'LENGTH OF queue > 0' in result.processed_source
    assert not any(item.rule == 'GC211' for item in result.transformations)


@pytest.mark.parametrize('phrase', ['not blank', 'not null', 'not whitespace', 'not missing', 'is not empty'])
def test_other_predicate_phrases_are_not_reinterpreted_by_gc211(phrase):
    normaliser = GenericObviousMismatchNormaliser()
    source = f'IF queue {phrase} THEN'
    processed, transformations = normaliser.process(source)
    assert not any(item.rule == 'GC211' for item in transformations)
    if phrase != 'is not empty':
        assert 'LENGTH OF queue > 0' not in processed


def test_not_empty_text_inside_quoted_string_is_untouched_by_gc211():
    result = _process('OUTPUT "queue not empty"')
    assert 'STRING("queue not empty")' in result.processed_source
    assert not any(item.rule == 'GC211' for item in result.transformations)


def test_not_empty_text_inside_comment_or_inline_comment_is_untouched_by_gc211():
    normaliser = GenericObviousMismatchNormaliser()

    comment, changes = normaliser.process('COMMENT queue not empty')
    assert comment == 'COMMENT queue not empty'
    assert not any(item.rule == 'GC211' for item in changes)

    inline, inline_changes = normaliser.process('IF ready == TRUE THEN # queue not empty')
    assert inline.endswith('# queue not empty')
    assert not any(item.rule == 'GC211' for item in inline_changes)


def test_member_or_longer_identifier_surface_is_outside_gc211_boundary():
    normaliser = GenericObviousMismatchNormaliser()
    for source in ('IF state.queue not empty THEN', 'IF queue_not_empty THEN'):
        processed, transformations = normaliser.process(source)
        assert not any(item.rule == 'GC211' for item in transformations)
        assert 'LENGTH OF queue > 0' not in processed
