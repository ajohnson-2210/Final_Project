from pseudocode_profiles import (
    GenericRecoveryNormaliser,
    GenericObviousMismatchNormaliser,
    LexicalEvidenceContext,
    _find_matching_delimiter,
    _parse_balanced_member_call,
    _split_statement_values_shared,
    _split_top_level_commas_shared,
    _unwrap_single_outer_parentheses_shared,
)


def test_shared_splitter_preserves_nested_and_quoted_commas():
    text = 'left, CALL f(a, "x,y"), [1, 2], {"k": 3}'
    expected = ['left', ' CALL f(a, "x,y")', ' [1, 2]', ' {"k": 3}']
    assert _split_top_level_commas_shared(text) == expected
    assert GenericObviousMismatchNormaliser._split_top_level_commas(text) == expected
    assert GenericRecoveryNormaliser._split_top_level_commas(text) == expected


def test_shared_outer_parenthesis_and_statement_tuple_boundaries_match_legacy_contract():
    assert _unwrap_single_outer_parentheses_shared('(a, CALL f("x)y"))') == 'a, CALL f("x)y")'
    assert _unwrap_single_outer_parentheses_shared('(a) + (b)') is None
    assert _split_statement_values_shared('(a + b)') == ['(a + b)']
    assert _split_statement_values_shared('(a, CALL f(b, c))') == ['a', ' CALL f(b, c)']


def test_shared_balanced_member_call_preserves_nested_argument_and_refuses_trailing_text():
    parsed = _parse_balanced_member_call(
        'items.append(CALL make_pair(a, STRING("x)y")))',
        ('append',),
        dotted_receiver=False,
    )
    assert parsed == ('items', 'append', 'CALL make_pair(a, STRING("x)y"))')
    assert _parse_balanced_member_call(
        'items.append(CALL f(a)) + other',
        ('append',),
        dotted_receiver=False,
    ) is None


def test_shared_delimiter_scanner_handles_nested_index_and_quotes():
    text = 'seen[s[i] + table["]"]] = value'
    close = _find_matching_delimiter(text, text.index('['), '[', ']')
    assert close is not None
    assert text[close + 1:].lstrip().startswith('=')


def test_lexical_evidence_context_supports_isolation_inheritance_shadow_and_rebind():
    evidence = LexicalEvidenceContext()
    evidence.establish('matrix', 'board')
    evidence.establish('set', 'seen')

    evidence.enter(inherit=False)
    assert not evidence.contains('matrix', 'board')
    evidence.establish('list', 'queue')
    evidence.exit()
    assert evidence.contains('matrix', 'board')
    assert not evidence.contains('list', 'queue')

    evidence.enter(inherit=True, shadow=('board',))
    assert not evidence.contains('matrix', 'board')
    assert evidence.contains('set', 'seen')
    evidence.invalidate('set', 'seen')
    assert not evidence.contains('set', 'seen')
    evidence.exit()
    assert evidence.contains('set', 'seen')


def test_matrix_surface_consolidation_preserves_gc246_and_gc249_rule_ids():
    square_source = 'board <- N x N grid initialized to 0\n'
    square, square_changes = GenericObviousMismatchNormaliser._normalise_explicit_square_grid_allocation(
        square_source
    )
    assert square == 'board <- CALL create_matrix(N, N, 0)\n'
    assert [change.rule for change in square_changes] == ['GC246']

    rectangular_source = 'C <- rows x cols matrix filled with 0\n'
    rectangular, rectangular_changes = GenericObviousMismatchNormaliser._normalise_explicit_rectangular_matrix_fill(
        rectangular_source
    )
    assert rectangular == 'C <- CALL create_matrix(rows, cols, 0)\n'
    assert [change.rule for change in rectangular_changes] == ['GC249']


def test_matrix_surface_consolidation_keeps_refusal_boundaries_separate():
    square_wrong = 'board <- N x M grid initialized to 0\n'
    rectangular_wrong_noun = 'C <- rows x cols grid filled with 0\n'
    assert GenericObviousMismatchNormaliser._normalise_explicit_square_grid_allocation(square_wrong) == (
        square_wrong,
        [],
    )
    assert GenericObviousMismatchNormaliser._normalise_explicit_rectangular_matrix_fill(
        rectangular_wrong_noun
    ) == (rectangular_wrong_noun, [])
