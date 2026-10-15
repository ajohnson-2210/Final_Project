from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_d_ALGORITHM_45 = '''FUNCTION AddMatrices(A, B, rows, cols):
    C = rows x cols matrix filled with 0
    FOR i FROM 0 TO rows - 1 DO
        FOR j FROM 0 TO cols - 1 DO
            C[i][j] = A[i][j] + B[i][j]
        END FOR
    END FOR
    RETURN C
END FUNCTION
'''


def process(source: str):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def compile_source(source: str):
    result = process(source)
    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    return result, compiled.source_code


def test_gc249_recovers_exact_source_d45_rectangular_zero_filled_matrix():
    result, python_source = compile_source(source_d_ALGORITHM_45)
    assert any(t.rule == "GC249" for t in result.transformations)
    assert "C <- CALL create_matrix(rows, cols, 0)" in result.processed_source
    assert "rows x cols matrix filled with 0" not in result.processed_source
    assert "C = [[0 for _ in range(cols)] for _ in range(rows)]" in python_source

    namespace = {}
    exec(python_source, namespace)
    assert namespace["AddMatrices"](
        [[1, 2, 3], [4, 5, 6]],
        [[10, 20, 30], [40, 50, 60]],
        2,
        3,
    ) == [[11, 22, 33], [44, 55, 66]]


def test_gc249_preserves_independent_rows():
    source = '''FUNCTION make ACCEPTS(rows, cols)
    C <- rows x cols matrix filled with 0
    RETURN C
ENDFUNCTION
'''
    result, python_source = compile_source(source)
    assert any(t.rule == "GC249" for t in result.transformations)
    namespace = {}
    exec(python_source, namespace)
    matrix = namespace["make"](2, 2)
    matrix[0][0] = 9
    assert matrix == [[9, 0], [0, 0]]


def test_gc249_refuses_nonzero_or_missing_fill():
    for source in (
        '''FUNCTION make ACCEPTS(rows, cols)\n    C <- rows x cols matrix filled with 1\n    RETURN C\nENDFUNCTION\n''',
        '''FUNCTION make ACCEPTS(rows, cols)\n    C <- rows x cols matrix\n    RETURN C\nENDFUNCTION\n''',
    ):
        result = process(source)
        assert not any(t.rule == "GC249" for t in result.transformations)


def test_gc249_refuses_expression_dimensions():
    source = '''FUNCTION make ACCEPTS(rows, cols)
    C <- (rows + 1) x cols matrix filled with 0
    RETURN C
ENDFUNCTION
'''
    result = process(source)
    assert not any(t.rule == "GC249" for t in result.transformations)
    assert "(rows + 1) x cols matrix filled with 0" in result.processed_source


def test_gc249_does_not_capture_grid_spelling_owned_by_other_rules():
    source = '''FUNCTION make ACCEPTS(rows, cols)
    C <- rows x cols grid filled with 0
    RETURN C
ENDFUNCTION
'''
    result = process(source)
    assert not any(t.rule == "GC249" for t in result.transformations)
