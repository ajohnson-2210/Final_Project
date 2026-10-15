FUNCTION unnamed_function ACCEPTS(N)
    FUNCTION placeQueen ACCEPTS(row, board)
        IF row == N THEN
            RETURN BOOLEAN(True)

        ENDIF
        FOR col <- IN RANGE 0 TO (N-1) + 1 DO
            IF CALL isSafe(board, row, col) THEN
                board[row][col] <- STRING("Q")

                IF CALL placeQueen(row + 1, board) THEN
                    RETURN BOOLEAN(True)

                ENDIF
                board[row][col] <- STRING(".")

            ENDIF
        ENDFOR
        RETURN BOOLEAN(False)

    ENDFUNCTION
    RETURN CALL placeQueen(0, CALL emptyBoard(N))
ENDFUNCTION