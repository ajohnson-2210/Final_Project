import pytest

from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


SOURCE = '''INPUT matrix (N x N)

FOR i from 0 to N/2 - 1:
    FOR j from i to N-1-i-1:
        temp = matrix[i][j]
        matrix[i][j] = matrix[N-1-j][i]
        matrix[N-1-j][i] = matrix[N-1-i][N-1-j]
        matrix[N-1-i][N-1-j] = matrix[j][N-1-i]
        matrix[j][N-1-i] = temp

RETURN matrix
'''


def _process():
    return PseudocodeProfileProcessor().process(
        SOURCE,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def _compile(result):
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    return compiled.source_code


def test_source_f_algorithm27_resolves_all_square_dimension_references_without_synthetic_n():
    result = _process()

    assert 'FUNCTION unnamed_function ACCEPTS(matrix)' in result.processed_source
    assert 'N <- LENGTH OF matrix' not in result.processed_source
    assert ' N ' not in f' {result.processed_source} '
    assert 'LENGTH OF matrix/2' in result.processed_source
    assert 'matrix[LENGTH OF matrix-1-j][i]' in result.processed_source
    assert 'INTEGER DIVISION' not in result.processed_source
    assert sum(item.rule == 'GC212' for item in result.transformations) == 6

    audit = result.to_dict()['transformations']
    gc212 = [item for item in audit if item['branch'] == 'SQUARE_DIMENSION_IDENTIFIER_REFERENCE']
    assert len(gc212) == 6
    assert all(item['semantic_change'] is False for item in gc212)


def test_source_f_algorithm27_compiles_without_unbound_n_but_preserves_ordinary_division():
    result = _process()
    python_source = _compile(result)

    import re
    assert re.search(r'\bN\b', python_source) is None
    assert 'len(matrix) / 2' in python_source
    assert '//' not in python_source


def test_source_f_algorithm27_is_expected_executable_correctness_failure_from_source_division():
    result = _process()
    python_source = _compile(result)
    namespace = {}
    exec(python_source, namespace)

    with pytest.raises(TypeError, match='float.*integer'):
        namespace['unnamed_function']([[1, 2], [3, 4]])


def test_source_f_algorithm27_audit_counterfactual_only_integer_division_makes_algorithm_viable():
    """Audit-only proof: do not apply this replacement in production normalisation."""
    result = _process()
    python_source = _compile(result)

    # Counterfactual diagnosis only.  The production compiler must continue to
    # preserve the source-authored `/`; this local replacement demonstrates
    # that the surrounding rotation logic is otherwise viable.
    repaired_for_audit = python_source.replace('len(matrix) / 2', 'len(matrix) // 2')
    assert repaired_for_audit != python_source

    namespace = {}
    exec(repaired_for_audit, namespace)
    rotate = namespace['unnamed_function']

    assert rotate([[1, 2], [3, 4]]) == [[3, 1], [4, 2]]
    assert rotate([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == [
        [7, 4, 1],
        [8, 5, 2],
        [9, 6, 3],
    ]
    assert rotate([
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 16],
    ]) == [
        [13, 9, 5, 1],
        [14, 10, 6, 2],
        [15, 11, 7, 3],
        [16, 12, 8, 4],
    ]


def test_source_f_algorithm27_audit_counterfactual_is_not_present_in_production_output():
    result = _process()
    python_source = _compile(result)

    assert 'len(matrix) / 2' in python_source
    assert 'len(matrix) // 2' not in python_source
