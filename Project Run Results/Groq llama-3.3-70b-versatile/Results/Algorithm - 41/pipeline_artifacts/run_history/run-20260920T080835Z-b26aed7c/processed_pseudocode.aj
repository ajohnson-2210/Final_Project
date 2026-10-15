FUNCTION N_QUEENS ACCEPTS(N)
  board <- EMPTY LIST
  FOR i <- IN RANGE 0 TO (N-1) + 1 DO
    board[i] <- EMPTY LIST
    FOR j <- IN RANGE 0 TO (N-1) + 1 DO
      board[i][j] <- 0
    ENDFOR
  ENDFOR
  FUNCTION IS_SAFE ACCEPTS(row, col)
    FOR i <- IN RANGE 0 TO (row-1) + 1 DO
      IF board[i][col] == 1 THEN
        RETURN BOOLEAN(False)
      ENDIF
      IF col - (row - i) >= 0 AND board[i][col - (row - i)] == 1 THEN
        RETURN BOOLEAN(False)
      ENDIF
      IF col + (row - i) < N AND board[i][col + (row - i)] == 1 THEN
        RETURN BOOLEAN(False)
      ENDIF
    ENDFOR
    RETURN BOOLEAN(True)
  ENDFUNCTION
  FUNCTION PLACE_QUEENS ACCEPTS(row)
    IF row == N THEN
      RETURN BOOLEAN(True)
    ENDIF
    FOR col <- IN RANGE 0 TO (N-1) + 1 DO
      IF CALL IS_SAFE(row, col) THEN
        board[row][col] <- 1
        IF CALL PLACE_QUEENS(row + 1) THEN
          RETURN BOOLEAN(True)
        ENDIF
        board[row][col] <- 0
      ENDIF
    ENDFOR
    RETURN BOOLEAN(False)
  ENDFUNCTION
  IF CALL PLACE_QUEENS(0) THEN
    RETURN board
  ELSE
    RETURN NULL
  ENDIF
ENDFUNCTION