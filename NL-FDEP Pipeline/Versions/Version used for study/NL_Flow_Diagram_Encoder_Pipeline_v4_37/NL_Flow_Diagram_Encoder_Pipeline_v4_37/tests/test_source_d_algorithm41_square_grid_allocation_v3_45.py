from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


def process(source: str):
    return PseudocodeProfileProcessor().process(
        source,
        PseudocodeProfile.GENERIC_COMPATIBILITY,
    )


def compile_source(processed_source: str) -> str:
    parsed = AJParserFacade().parse(processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert compiled.success
    return compiled.source_code


source_d_41 = '''FUNCTION SolveNQueens(N):
    board = N x N grid initialized to 0
    solutions = empty List

    PROCEDURE Backtrack(row, cols, diag1, diag2):
        IF row == N THEN
            APPEND Copy(board) TO solutions
            RETURN
        END IF

        FOR col FROM 0 TO N - 1 DO
            IF col IN cols OR (row - col) IN diag1 OR (row + col) IN diag2 THEN
                CONTINUE
            END IF

            board[row][col] = 1
            Backtrack(row + 1, cols + {col}, diag1 + {row - col}, diag2 + {row + col})
            board[row][col] = 0 // Backtrack
        END FOR
    END PROCEDURE

    Backtrack(0, empty Set, empty Set, empty Set)
    RETURN solutions
END FUNCTION
'''


def test_gc246_recovers_exact_source_d41_square_zero_grid_and_composes_with_later_copy_recovery():
    result = process(source_d_41)
    assert any(t.rule == "GC246" for t in result.transformations)
    assert "board <- CALL create_matrix(N, N, 0)" in result.processed_source
    assert "N x N grid initialized to 0" not in result.processed_source

    # GC246 remains isolated but now composes with the separately approved
    # GC247 evidence-gated 2D board-copy recovery.
    python_source = compile_source(result.processed_source)
    assert "board = [[0 for _ in range(N)] for _ in range(N)]" in python_source
    assert "solutions.append(list(map(list, board)))" in python_source

    namespace = {}
    exec(python_source, namespace)
    assert namespace["SolveNQueens"](1) == [[[1]]]


def test_gc246_minimal_square_zero_grid_parses_compiles_and_allocates_independent_rows():
    source = '''FUNCTION make ACCEPTS(N)
    board <- N x N grid initialized to 0
    RETURN board
ENDFUNCTION
'''
    result = process(source)
    assert any(t.rule == "GC246" for t in result.transformations)
    python_source = compile_source(result.processed_source)
    namespace = {}
    exec(python_source, namespace)
    board = namespace["make"](2)
    assert board == [[0, 0], [0, 0]]
    board[0][0] = 9
    assert board == [[9, 0], [0, 0]]


def test_gc246_refuses_rectangular_grid():
    source = '''FUNCTION make ACCEPTS(rows, cols)
    board <- rows x cols grid initialized to 0
    RETURN board
ENDFUNCTION
'''
    result = process(source)
    assert all(t.rule != "GC246" for t in result.transformations)
    assert "rows x cols grid initialized to 0" in result.processed_source


def test_gc246_refuses_nonzero_or_missing_initialiser():
    sources = (
        '''FUNCTION make ACCEPTS(N)\n    board <- N x N grid initialized to 1\n    RETURN board\nENDFUNCTION\n''',
        '''FUNCTION make ACCEPTS(N)\n    board <- N x N grid\n    RETURN board\nENDFUNCTION\n''',
    )
    for source in sources:
        result = process(source)
        assert all(t.rule != "GC246" for t in result.transformations)


def test_gc246_refuses_expression_dimensions():
    source = '''FUNCTION make ACCEPTS(N)
    board <- (N + 1) x (N + 1) grid initialized to 0
    RETURN board
ENDFUNCTION
'''
    result = process(source)
    assert all(t.rule != "GC246" for t in result.transformations)
