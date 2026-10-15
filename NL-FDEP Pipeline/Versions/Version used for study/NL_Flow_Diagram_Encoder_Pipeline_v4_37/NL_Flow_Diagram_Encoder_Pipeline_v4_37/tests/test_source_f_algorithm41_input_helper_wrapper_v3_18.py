from aj_parser import AJParserFacade
from aj_python_compiler import AJPythonCompiler
from flow_diagram import FlowDiagramEncoder
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_f_ALGORITHM_41 = """INPUT N

FUNCTION placeQueen(row, board):
    IF row == N:
        RETURN TRUE

    FOR col from 0 to N-1:
        IF isSafe(board, row, col):
            board[row][col] = 'Q'

            IF placeQueen(row + 1, board):
                RETURN TRUE

            board[row][col] = '.'

    RETURN FALSE

RETURN placeQueen(0, emptyBoard(N))
"""


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def test_source_f41_recovers_only_omitted_neutral_outer_wrapper():
    result = _process(source_f_ALGORITHM_41)
    assert result.processed_source.startswith("FUNCTION unnamed_function ACCEPTS(N)")
    assert "FUNCTION placeQueen ACCEPTS(row, board)" in result.processed_source
    assert "IF CALL isSafe(board, row, col) THEN" in result.processed_source
    assert "RETURN CALL placeQueen(0, CALL emptyBoard(N))" in result.processed_source
    assert [item.rule for item in result.transformations].count("GC219") == 1

    parsed = AJParserFacade().parse(result.processed_source)
    assert parsed.success, parsed.error
    compiled = AJPythonCompiler().compile(FlowDiagramEncoder().encode(parsed.ast))
    assert not compiled.success
    assert compiled.source_code == ""
    assert "Expected failure" in compiled.message
    assert "isSafe" in compiled.message
    assert "emptyBoard" in compiled.message


def test_gc219_audit_marks_wrapper_as_source_proven_nonsemantic():
    result = _process(source_f_ALGORITHM_41)
    entries = [
        item for item in result.to_dict()["transformations"]
        if item["branch"] == "EVIDENCED_INPUT_HELPER_FINAL_RETURN_WRAPPER"
    ]
    assert len(entries) == 1
    assert entries[0]["rule_family"] == "STRUCTURAL_WRAPPER"
    assert entries[0]["confidence"] == "source_proven"
    assert entries[0]["semantic_change"] is False


def test_gc219_refuses_unrelated_top_level_executable_statement():
    source = """INPUT N
state = 0
FUNCTION helper(x):
    RETURN x
RETURN helper(N)
"""
    result = _process(source)
    assert not any(item.rule == "GC219" for item in result.transformations)


def test_gc219_refuses_final_return_that_does_not_call_supplied_helper():
    source = """INPUT N
FUNCTION helper(x):
    RETURN x
RETURN N
"""
    result = _process(source)
    assert not any(item.rule == "GC219" for item in result.transformations)


def test_gc219_refuses_input_after_helper_declaration():
    source = """FUNCTION helper(x):
    RETURN x
INPUT N
RETURN helper(N)
"""
    result = _process(source)
    assert not any(item.rule == "GC219" for item in result.transformations)
