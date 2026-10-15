FUNCTION solveNQueens ACCEPTS(N)
    board <- CALL create_matrix(N, N, 0)
    solutions <- EMPTY LIST

    FUNCTION isSafe ACCEPTS(board, row, col)
        COMMENT Check column
        FOR i <- IN RANGE 0 TO (row-1) + 1 DO
            IF board[i][col] == 1 THEN
                RETURN BOOLEAN(False)
        COMMENT Check upper-left diagonal
            ENDIF
        ENDFOR
        i <- row - 1
        j <- col - 1
        WHILE i >= 0 AND j >= 0 DO
            IF board[i][j] == 1 THEN
                RETURN BOOLEAN(False)
            ENDIF
            i <- i - 1
            j <- j - 1
        COMMENT Check upper-right diagonal
        ENDWHILE
        i <- row - 1
        j <- col + 1
        WHILE i >= 0 AND j < N DO
            IF board[i][j] == 1 THEN
                RETURN BOOLEAN(False)
            ENDIF
            i <- i - 1
            j <- j + 1
        ENDWHILE
        RETURN BOOLEAN(True)

    ENDFUNCTION
    FUNCTION placeQueen ACCEPTS(board, row)
        IF row == N THEN
            APPEND CALL copy_value(board) TO solutions
            RETURN
        ENDIF
        FOR col <- IN RANGE 0 TO (N-1) + 1 DO
            IF CALL isSafe(board, row, col) THEN
                board[row][col] <- 1
                CALL placeQueen(board, row + 1)
                board[row][col] <- 0
                COMMENT Backtrack

            ENDIF
        ENDFOR
    ENDFUNCTION
    CALL placeQueen(board, 0)
    RETURN solutions
ENDFUNCTION