from itertools import product

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_d_ALGORITHM_42 = '''FUNCTION FindPairsWithSum(arr, target):
    seen = empty Set
    pairs = empty Set

    FOR EACH num IN arr DO
        complement = target - num
        IF complement IN seen THEN
            ADD (MIN(num, complement), MAX(num, complement)) TO pairs
        END IF
        ADD num TO seen
    END FOR

    RETURN pairs
END FUNCTION
'''


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def _compile(source: str):
    result = _process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    return result, compiled.source_code


def test_source_d42_exact_source_recovers_parenthesised_pair_as_tuple_for_set_insert():
    result, python_source = _compile(source_d_ALGORITHM_42)

    assert (
        'CALL add_to_set(pairs, TUPLE(CALL min(num, complement), CALL max(num, complement)))'
        in result.processed_source
    )
    assert any(item.rule == 'GC248' for item in result.transformations)
    assert 'pairs.add((min(num, complement), max(num, complement)))' in python_source


def test_source_d42_generated_python_matches_unique_pair_reference():
    _, python_source = _compile(source_d_ALGORITHM_42)
    namespace = {}
    exec(python_source, namespace)
    fn = namespace['FindPairsWithSum']

    values = (-2, -1, 0, 1, 2)
    for length in range(0, 6):
        for arr in product(values, repeat=length):
            for target in range(-4, 5):
                seen = set()
                expected = set()
                for num in arr:
                    complement = target - num
                    if complement in seen:
                        expected.add((min(num, complement), max(num, complement)))
                    seen.add(num)
                assert fn(list(arr), target) == expected


def test_gc248_refuses_unproven_receiver():
    source = '''FUNCTION f ACCEPTS(a, b)
CALL add_to_set(items, (a, b))
RETURN items
ENDFUNCTION
'''
    result = _process(source)
    assert 'CALL add_to_set(items, (a, b))' in result.processed_source
    assert not any(item.rule == 'GC248' for item in result.transformations)


def test_gc248_refuses_grouped_single_expression():
    source = '''FUNCTION f ACCEPTS(a, b)
pairs <- EMPTY SET
CALL add_to_set(pairs, (a + b))
RETURN pairs
ENDFUNCTION
'''
    result = _process(source)
    assert 'CALL add_to_set(pairs, (a + b))' in result.processed_source
    assert 'TUPLE(a + b)' not in result.processed_source
    assert not any(item.rule == 'GC248' for item in result.transformations)


def test_gc248_refuses_non_two_value_parenthesised_payload():
    source = '''FUNCTION f ACCEPTS(a, b, c)
pairs <- EMPTY SET
CALL add_to_set(pairs, (a, b, c))
RETURN pairs
ENDFUNCTION
'''
    result = _process(source)
    assert 'CALL add_to_set(pairs, (a, b, c))' in result.processed_source
    assert 'TUPLE(a, b, c)' not in result.processed_source
    assert not any(item.rule == 'GC248' for item in result.transformations)
