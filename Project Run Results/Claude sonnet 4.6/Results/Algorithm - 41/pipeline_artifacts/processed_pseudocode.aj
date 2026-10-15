FUNCTION solveNQueens(N):
    board <- N*N grid of 0s
    CALL placeQueens(board, 0, N)

FUNCTION placeQueens(board, row, N):
    IF row == N THEN RECORD solution; RETURN
    FOR col FROM 0 TO N - 1:
        IF isSafe(board, row, col, N) THEN
            board[row][col] <- 1
            placeQueens(board, row + 1, N)
            board[row][col] <- 0
            // backtrack

FUNCTION isSafe(board, row, col, N):
    CHECK column, upper-left diagonal, upper-right diagonal for queens
    RETURN True if no conflicts