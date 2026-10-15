import pytest

from pseudocode_profiles import GenericPseudocodeProcessor


def _recover(source: str):
    return GenericPseudocodeProcessor()._normalise_square_dimension_loop_bounds(source)


def test_generic_square_annotation_resolves_exact_zero_to_dimension_minus_one_loop():
    source = '''INPUT grid (K x K)
FOR row from 0 to K - 1:
    OUTPUT grid[row][row]
'''
    processed, transformations = _recover(source)
    assert 'FOR row <- IN RANGE 0 TO LENGTH OF grid DO' in processed
    assert len(transformations) == 1
    assert transformations[0].rule == 'GC208'


def test_square_annotation_and_loop_matching_are_case_insensitive():
    source = '''input board (Size X size)
for r FROM 0 TO SIZE-1 do
    OUTPUT board[r][r]
'''
    processed, transformations = _recover(source)
    assert 'FOR r <- IN RANGE 0 TO LENGTH OF board DO' in processed
    assert len(transformations) == 1


@pytest.mark.parametrize(
    'source',
    [
        # Rectangular shape does not establish one square dimension symbol.
        'INPUT grid (R x C)\nFOR i from 0 to R-1:\n    OUTPUT grid[i][i]\n',
        # A separately supplied symbol is a runtime binding, not annotation-only notation.
        'INPUT grid (K x K)\nINPUT K\nFOR i from 0 to K-1:\n    OUTPUT grid[i][i]\n',
        # An independently assigned symbol must not be overridden by shape recovery.
        'INPUT grid (K x K)\nK = 4\nFOR i from 0 to K-1:\n    OUTPUT grid[i][i]\n',
        # The approved surface starts at zero; other ranges need separate reasoning.
        'INPUT grid (K x K)\nFOR i from 1 to K-1:\n    OUTPUT grid[i][i]\n',
        # K itself is not the approved inclusive K-1 source endpoint.
        'INPUT grid (K x K)\nFOR i from 0 to K:\n    OUTPUT grid[i][i]\n',
        # One annotation symbol cannot choose between multiple collections.
        'INPUT left (K x K)\nINPUT right (K x K)\nFOR i from 0 to K-1:\n    OUTPUT left[i][i]\n',
    ],
)
def test_square_dimension_recovery_refuses_unapproved_or_ambiguous_shapes(source):
    processed, transformations = _recover(source)
    assert processed == source
    assert not transformations


def test_different_square_symbols_can_resolve_independently():
    source = '''INPUT first (A x A)
INPUT second (B x B)
FOR i from 0 to A-1:
    OUTPUT first[i][i]
FOR j from 0 to B-1:
    OUTPUT second[j][j]
'''
    processed, transformations = _recover(source)
    assert 'FOR i <- IN RANGE 0 TO LENGTH OF first DO' in processed
    assert 'FOR j <- IN RANGE 0 TO LENGTH OF second DO' in processed
    assert [item.rule for item in transformations] == ['GC208', 'GC208']


def test_square_dimension_recovery_does_not_substitute_other_symbol_uses():
    source = """INPUT grid (K x K)
FOR i from 0 to K-1:
    OUTPUT grid[i][i]
OUTPUT K
"""
    processed, transformations = _recover(source)
    assert 'FOR i <- IN RANGE 0 TO LENGTH OF grid DO' in processed
    assert 'OUTPUT K' in processed
    assert len(transformations) == 1
