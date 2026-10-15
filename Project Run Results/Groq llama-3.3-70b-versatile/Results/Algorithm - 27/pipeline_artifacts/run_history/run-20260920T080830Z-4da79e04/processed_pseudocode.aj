FUNCTION ROTATE_MATRIX ACCEPTS(matrix)
  n <- LENGTH OF matrix
  FOR layer <- IN RANGE 0 TO (n / 2) + 1 DO
    first <- layer
    last <- n - layer - 1
    FOR i <- IN RANGE first TO (last) + 1 DO
      top <- matrix[layer][i]
      matrix[layer][i] <- matrix[last - i + first][first]
      matrix[last - i + first][first] <- matrix[last][last - i + first]
      matrix[last][last - i + first] <- matrix[i][last]
      matrix[i][last] <- top
    ENDFOR
  ENDFOR
  RETURN matrix
ENDFUNCTION