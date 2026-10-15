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


def test_gc247_recovers_source_d41_evidenced_board_copy_and_executes():
    result = process(source_d_41)
    assert any(t.rule == "GC247" for t in result.transformations)
    assert "APPEND CALL copy_2d_list(board) TO solutions" in result.processed_source
    python_source = compile_source(result.processed_source)
    assert "solutions.append(list(map(list, board)))" in python_source

    namespace = {}
    exec(python_source, namespace)
    solve = namespace["SolveNQueens"]
    assert [len(solve(n)) for n in (1, 2, 3, 4)] == [1, 0, 0, 2]
    solutions = solve(4)
    assert all(sum(sum(row) for row in board) == 4 for board in solutions)
    assert solutions[0] != solutions[1]


def test_gc247_inherits_matrix_evidence_into_nested_routine():
    source = '''FUNCTION outer ACCEPTS(N)
    board <- CALL create_matrix(N, N, 0)
    saved <- EMPTY LIST
    FUNCTION inner ACCEPTS()
        APPEND Copy(board) TO saved
    ENDFUNCTION
    CALL inner()
    RETURN saved
ENDFUNCTION
'''
    result = process(source)
    assert any(t.rule == "GC247" for t in result.transformations)
    assert "APPEND CALL copy_2d_list(board) TO saved" in result.processed_source


def test_gc247_refuses_unproven_copy_value():
    source = '''FUNCTION f ACCEPTS(board)
    RETURN Copy(board)
ENDFUNCTION
'''
    result = process(source)
    assert all(t.rule != "GC247" for t in result.transformations)
    assert "CALL Copy(board)" in result.processed_source


def test_gc247_refuses_shadowed_nested_parameter():
    source = '''FUNCTION outer ACCEPTS(N)
    board <- CALL create_matrix(N, N, 0)
    FUNCTION inner ACCEPTS(board)
        RETURN Copy(board)
    ENDFUNCTION
    RETURN CALL inner(board)
ENDFUNCTION
'''
    result = process(source)
    assert all(t.rule != "GC247" for t in result.transformations)
    assert "RETURN CALL Copy(board)" in result.processed_source


def test_gc247_refuses_after_direct_rebind():
    source = '''FUNCTION f ACCEPTS(N)
    board <- CALL create_matrix(N, N, 0)
    board <- EMPTY LIST
    RETURN Copy(board)
ENDFUNCTION
'''
    result = process(source)
    assert all(t.rule != "GC247" for t in result.transformations)
    assert "RETURN CALL Copy(board)" in result.processed_source


def test_gc247_refuses_member_wrong_arity_comment_and_quoted_text():
    source = '''FUNCTION f ACCEPTS(N, obj)
    board <- CALL create_matrix(N, N, 0)
    CALL obj.Copy(board)
    CALL Copy(board, board)
    COMMENT CALL Copy(board)
    OUTPUT STRING("CALL Copy(board)")
    RETURN board
ENDFUNCTION
'''
    result = process(source)
    assert all(t.rule != "GC247" for t in result.transformations)
    assert "CALL obj.Copy(board)" in result.processed_source
    assert "CALL Copy(board, board)" in result.processed_source
    assert "COMMENT CALL Copy(board)" in result.processed_source
