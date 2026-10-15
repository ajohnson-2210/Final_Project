import pytest

from pseudocode_profiles import GenericPseudocodeProcessor


def _recover(source: str):
    return GenericPseudocodeProcessor()._normalise_square_dimension_identifier_references(source)


def test_generic_square_dimension_resolves_compound_executable_references_without_changing_arithmetic():
    source = '''INPUT grid (K x K)
FOR layer from 0 to K/2 - 1:
    value = grid[K-1-layer][K-1]
RETURN K
'''
    processed, transformations = _recover(source)

    assert 'FOR layer from 0 to LENGTH OF grid/2 - 1:' in processed
    assert 'grid[LENGTH OF grid-1-layer][LENGTH OF grid-1]' in processed
    assert 'RETURN LENGTH OF grid' in processed
    assert 'INTEGER DIVISION' not in processed
    assert 'K <- LENGTH OF grid' not in processed
    assert [item.rule for item in transformations] == ['GC212', 'GC212', 'GC212']


def test_gc212_is_quote_comment_member_and_call_name_safe():
    source = '''INPUT grid (K x K)
OUTPUT STRING("K stays text")
OUTPUT obj.K
CALL K()
OUTPUT K COMMENT K stays comment text
COMMENT K stays comment text
'''
    processed, transformations = _recover(source)

    assert 'STRING("K stays text")' in processed
    assert 'OUTPUT obj.K' in processed
    assert 'CALL K()' in processed
    assert 'OUTPUT LENGTH OF grid COMMENT K stays comment text' in processed
    assert 'COMMENT K stays comment text' in processed
    assert len(transformations) == 1


@pytest.mark.parametrize(
    'source',
    [
        # Rectangular shape does not establish one square-dimension identity.
        'INPUT grid (R x C)\nOUTPUT R\n',
        # A separately supplied symbol is an independent runtime binding.
        'INPUT grid (K x K)\nINPUT K\nOUTPUT K\n',
        # A separately assigned symbol must not be overridden.
        'INPUT grid (K x K)\nK = 4\nOUTPUT K\n',
        # A loop iterator is an independent binding.
        'INPUT grid (K x K)\nFOR K from 0 to 3:\n    OUTPUT K\n',
        # One symbol cannot select between two square collections in one scope.
        'INPUT left (K x K)\nINPUT right (K x K)\nOUTPUT K\n',
    ],
)
def test_gc212_refuses_rectangular_bound_or_ambiguous_dimension_symbols(source):
    processed, transformations = _recover(source)
    assert processed == source
    assert transformations == []


def test_gc212_is_routine_scoped_and_does_not_capture_nested_parameter_binding():
    source = '''INPUT outer (N x N)
OUTPUT N
FUNCTION inner ACCEPTS(N)
    OUTPUT N
ENDFUNCTION
OUTPUT N
'''
    processed, transformations = _recover(source)

    assert processed.splitlines()[1] == 'OUTPUT LENGTH OF outer'
    assert 'FUNCTION inner ACCEPTS(N)' in processed
    assert '    OUTPUT N' in processed
    assert processed.splitlines()[-1] == 'OUTPUT LENGTH OF outer'
    assert len(transformations) == 2


def test_gc208_can_run_first_and_gc212_resolves_only_remaining_symbol_uses():
    source = '''INPUT grid (K x K)
FOR i from 0 to K-1:
    OUTPUT grid[i][i]
OUTPUT K
'''
    processor = GenericPseudocodeProcessor()
    after_gc208, gc208 = processor._normalise_square_dimension_loop_bounds(source)
    processed, gc212 = processor._normalise_square_dimension_identifier_references(after_gc208)

    assert 'FOR i <- IN RANGE 0 TO LENGTH OF grid DO' in processed
    assert 'OUTPUT LENGTH OF grid' in processed
    assert len(gc208) == 1 and gc208[0].rule == 'GC208'
    assert len(gc212) == 1 and gc212[0].rule == 'GC212'
