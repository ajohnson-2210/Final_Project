FUNCTION MULTIPLY_MATRICES ACCEPTS(matrix1, matrix2)
  result <- EMPTY LIST
  FOR i <- IN RANGE 0 TO (LENGTH OF matrix1 - 1) + 1 DO
    row <- EMPTY LIST
    FOR j <- IN RANGE 0 TO (LENGTH OF matrix2[0] - 1) + 1 DO
      sum <- 0
      FOR k <- IN RANGE 0 TO (LENGTH OF matrix1[0] - 1) + 1 DO
        sum <- sum + matrix1[i][k] * matrix2[k][j]
      ENDFOR
      APPEND sum TO row
    ENDFOR
    APPEND row TO result
  ENDFOR
  RETURN result
ENDFUNCTION