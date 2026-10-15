from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def process(source: str):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def compile_processed(processed: str) -> str:
    parsed = AJParserFacade().parse(processed)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    return compiled.source_code


def test_gc223_unspecified_rectangular_result_uses_none_not_zero():
    source = '''INPUT A, B (same dimensions R x C)

INIT result as R x C matrix

FOR i from 0 to R-1:
    FOR j from 0 to C-1:
        result[i][j] = A[i][j] + B[i][j]

RETURN result
'''
    result = process(source)
    canonical = result.processed_source
    assert any(t.rule == 'GC223' for t in result.transformations)
    assert 'result <- CALL create_matrix(LENGTH OF A, LENGTH OF A[0], NONE)' in canonical
    assert 'create_matrix(LENGTH OF A, LENGTH OF A[0], 0)' not in canonical
    python_source = compile_processed(canonical)
    assert 'result = [[None for _ in range(len(A[0]))] for _ in range(len(A))]' in python_source


def test_implicit_matrix_allocations_are_none_filled_across_approved_rules():
    gc160 = '''FUNCTION make ACCEPTS(rows, cols)
    result <- matrix of size rows x cols
    RETURN result
ENDFUNCTION
'''
    gc224 = '''INPUT A (M x N), B (N x P)
INIT C as M x P matrix
FOR i from 0 to M-1:
    FOR j from 0 to P-1:
        sum = 0
        FOR k from 0 to N-1:
            sum += A[i][k] * B[k][j]
        C[i][j] = sum
RETURN C
'''
    for source in (gc160, gc224):
        result = process(source)
        assert 'create_matrix' in result.processed_source
        assert ', NONE)' in result.processed_source


def test_explicit_zero_matrix_surfaces_remain_zero_filled():
    sources = (
        '''FUNCTION make ACCEPTS(rows, cols)
    result <- matrix of size rows x cols initialized with 0
    RETURN result
ENDFUNCTION
''',
        '''FUNCTION make ACCEPTS(rows, cols)
    result <- rows * cols matrix of 0s
    RETURN result
ENDFUNCTION
''',
        '''FUNCTION make ACCEPTS(N)
    board <- N x N grid initialized to 0
    RETURN board
ENDFUNCTION
''',
        '''FUNCTION make ACCEPTS(rows, cols)
    C <- rows x cols matrix filled with 0
    RETURN C
ENDFUNCTION
''',
    )
    for source in sources:
        result = process(source)
        assert 'create_matrix' in result.processed_source
        assert ', 0)' in result.processed_source
        python_source = compile_processed(result.processed_source)
        assert '[[0 for _ in range(' in python_source


def test_explicit_zero_array_fill_remains_zero_filled():
    source = '''FUNCTION make ACCEPTS(N)
    arr <- array of size N initialized to 0
    RETURN arr
ENDFUNCTION
'''
    result = process(source)
    assert 'arr <- CALL create_array(N, 0)' in result.processed_source
    python_source = compile_processed(result.processed_source)
    assert 'arr = [0 for _ in range(N)]' in python_source
