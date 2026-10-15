FUNCTION SolveNQueens ACCEPTS(N)
    board <- CALL create_matrix(N, N, 0)
    solutions <- EMPTY LIST

    FUNCTION Backtrack ACCEPTS(row, cols, diag1, diag2)
        IF row == N THEN
            APPEND CALL copy_2d_list(board) TO solutions
            RETURN
        ENDIF

        FOR col <- IN RANGE 0 TO (N - 1) + 1 DO
            IF col IN cols OR (row - col) IN diag1 OR (row + col) IN diag2 THEN
                CONTINUE
            ENDIF

            board[row][col] <- 1
            CALL Backtrack(row + 1, CALL to_set(CALL to_list(cols) + CALL list_value(col)), CALL to_set(CALL to_list(diag1) + CALL list_value(row - col)), CALL to_set(CALL to_list(diag2) + CALL list_value(row + col)))
            board[row][col] <- 0
            COMMENT Backtrack
        ENDFOR
    ENDFUNCTION

    CALL Backtrack(0, EMPTY SET, EMPTY SET, EMPTY SET)
    RETURN solutions
ENDFUNCTION