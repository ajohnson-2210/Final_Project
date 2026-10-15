from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder


def _compile(canonical: str):
    parsed = AJParserFacade().parse(canonical)
    assert parsed.success, parsed.error
    return AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))


def test_undefined_nqueens_core_helpers_are_expected_failure_before_python_generation():
    compiled = _compile('''FUNCTION solve ACCEPTS(N)
    FUNCTION placeQueen ACCEPTS(row, board)
        IF row == N THEN
            RETURN BOOLEAN(TRUE)
        ENDIF
        FOR col <- IN RANGE 0 TO N DO
            IF CALL isSafe(board, row, col) THEN
                board[row][col] <- CHAR("Q")
            ENDIF
        ENDFOR
        RETURN BOOLEAN(FALSE)
    ENDFUNCTION
    RETURN CALL placeQueen(0, CALL emptyBoard(N))
ENDFUNCTION
''')
    assert not compiled.success
    assert compiled.source_code == ""
    assert "Expected failure" in compiled.message
    assert "isSafe" in compiled.message
    assert "emptyBoard" in compiled.message


def test_explicit_nqueens_core_helper_definitions_remove_expected_failure_block():
    compiled = _compile('''FUNCTION emptyBoard ACCEPTS(N)
    RETURN EMPTY LIST
ENDFUNCTION
FUNCTION isSafe ACCEPTS(board, row, col)
    RETURN BOOLEAN(TRUE)
ENDFUNCTION
FUNCTION solve ACCEPTS(N)
    board <- CALL emptyBoard(N)
    IF CALL isSafe(board, 0, 0) THEN
        RETURN BOOLEAN(TRUE)
    ENDIF
    RETURN BOOLEAN(FALSE)
ENDFUNCTION
''')
    assert compiled.success, compiled.message
    assert "def emptyBoard(N):" in compiled.source_code
    assert "def isSafe(board, row, col):" in compiled.source_code
    assert "board = emptyBoard(N)" in compiled.source_code
    assert "if isSafe(board, 0, 0):" in compiled.source_code


def test_only_missing_nqueens_helper_is_reported_when_other_is_defined():
    compiled = _compile('''FUNCTION isSafe ACCEPTS(board, row, col)
    RETURN BOOLEAN(TRUE)
ENDFUNCTION
FUNCTION solve ACCEPTS(N)
    board <- CALL emptyBoard(N)
    RETURN CALL isSafe(board, 0, 0)
ENDFUNCTION
''')
    assert not compiled.success
    assert compiled.source_code == ""
    assert "emptyBoard" in compiled.message
    assert "isSafe" not in compiled.message


def test_unrelated_external_dependency_remains_permitted():
    compiled = _compile('''FUNCTION demo ACCEPTS(value)
    RETURN CALL external_library_operation(value)
ENDFUNCTION
''')
    assert compiled.success, compiled.message
    assert "return external_library_operation(value)" in compiled.source_code
