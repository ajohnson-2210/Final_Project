import unittest

from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


source_b_41 = '''FUNCTION solveNQueens(N):
    board ← N×N grid of 0s
    CALL placeQueens(board, 0, N)

FUNCTION placeQueens(board, row, N):
    IF row == N THEN RECORD solution; RETURN
    FOR col FROM 0 TO N - 1:
        IF isSafe(board, row, col, N) THEN
            board[row][col] ← 1
            placeQueens(board, row + 1, N)
            board[row][col] ← 0

FUNCTION isSafe(board, row, col, N):
    CHECK column, upper-left diagonal, upper-right diagonal for queens
    RETURN True if no conflicts
'''


class source_bAlgorithm41ExpectedFailureV285Tests(unittest.TestCase):
    def setUp(self):
        self.processor = PseudocodeProfileProcessor()

    def test_exact_study_occurrence_remains_visibly_non_executable(self):
        result = self.processor.process(
            source_b_41,
            PseudocodeProfile.GENERIC_COMPATIBILITY,
        )
        self.assertIn("RECORD solution", result.processed_source)
        self.assertIn(
            "CHECK column, upper-left diagonal, upper-right diagonal for queens",
            result.processed_source,
        )
        self.assertIn("RETURN True if no conflicts", result.processed_source)
        self.assertNotIn("checkRow <-", result.processed_source)
        self.assertNotIn("result <- CALL placeQueens", result.processed_source)
        self.assertNotIn("RETURN board", result.processed_source)
        self.assertNotIn("RETURN NONE", result.processed_source)
        self.assertNotIn("GC142", [item.rule for item in result.transformations])

        parsed = AJParserFacade().parse(result.processed_source)
        self.assertFalse(parsed.success)

    def test_legacy_gc142_trigger_shape_is_no_longer_reconstructed(self):
        source = '''FUNCTION solveNQueens ACCEPTS(N)
    board <- N*N grid of 0s
    CALL placeQueens(board, 0, N)
ENDFUNCTION

FUNCTION placeQueens ACCEPTS(board, row, N)
    IF row == N THEN RECORD solution; RETURN THEN
    ENDIF
    FOR col <- IN RANGE 0 TO N - 1 DO
        IF CALL isSafe(board, row, col, N) THEN
            board[row][col] <- 1
            CALL placeQueens(board, row + 1, N)
            board[row][col] <- 0
        ENDIF
    ENDFOR
ENDFUNCTION

FUNCTION isSafe ACCEPTS(board, row, col, N)
    CHECK column, upper-left diagonal, upper-right diagonal for queens
    RETURN BOOLEAN(True) if no conflicts
ENDFUNCTION
'''
        result = self.processor.process(
            source,
            PseudocodeProfile.GENERIC_COMPATIBILITY,
        )
        self.assertEqual(result.processed_source.rstrip(), source.rstrip())
        self.assertNotIn("GC142", [item.rule for item in result.transformations])
        self.assertNotIn("checkRow <-", result.processed_source)
        self.assertNotIn("RETURN board", result.processed_source)
        self.assertFalse(AJParserFacade().parse(result.processed_source).success)

    def test_defined_nqueens_routine_is_not_blocked_by_expected_failure_guard(self):
        source = '''FUNCTION isSafe ACCEPTS(board, row, col, N)
    checkRow <- 0
    WHILE checkRow < row DO
        IF board[checkRow][col] == 1 THEN
            RETURN BOOLEAN(False)
        ENDIF
        checkRow <- checkRow + 1
    ENDWHILE
    RETURN BOOLEAN(True)
ENDFUNCTION
'''
        result = self.processor.process(
            source,
            PseudocodeProfile.GENERIC_COMPATIBILITY,
        )
        parsed = AJParserFacade().parse(result.processed_source)
        self.assertTrue(parsed.success, parsed.error)


if __name__ == "__main__":
    unittest.main()
