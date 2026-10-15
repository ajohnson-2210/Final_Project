from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


# Exact motivating source_f Algorithm 12 occurrence retained as audit evidence.
SOURCE = '''INPUT matrix (N x N)

sum = 0

FOR i from 0 to N-1:
    sum += matrix[i][i]

RETURN sum
'''


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def test_source_f_algorithm12_resolves_square_dimension_directly_to_collection_length():
    result = _process(SOURCE)

    assert 'FUNCTION unnamed_function ACCEPTS(matrix)' in result.processed_source
    assert 'FOR i <- IN RANGE 0 TO LENGTH OF matrix DO' in result.processed_source
    assert 'N <-' not in result.processed_source
    assert '(N-1)' not in result.processed_source
    assert sum(item.rule == 'GC208' for item in result.transformations) == 1

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    assert 'for i in range(0, len(matrix)):' in compiled.source_code
    assert 'N = len(matrix)' not in compiled.source_code

    namespace = {}
    exec(compiled.source_code, namespace)
    fn = namespace['unnamed_function']
    assert fn([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == 15
    assert fn([[9]]) == 9
    assert fn([]) == 0
