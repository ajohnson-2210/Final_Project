FUNCTION ADD_MATRICES ACCEPTS(matrix1, matrix2)
  result <- EMPTY LIST
  FOR i <- IN RANGE 0 TO (LENGTH OF matrix1 - 1) + 1 DO
    row <- EMPTY LIST
    FOR j <- IN RANGE 0 TO (LENGTH OF matrix1[0] - 1) + 1 DO
      APPEND matrix1[i][j] + matrix2[i][j] TO row
    ENDFOR
    APPEND row TO result
  ENDFOR
  RETURN result
ENDFUNCTION