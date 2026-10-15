FUNCTION SUM_DIAGONAL ACCEPTS(grid)
  sum <- 0
  FOR i <- IN RANGE 0 TO (LENGTH OF grid - 1) + 1 DO
    sum <- sum + grid[i][i]
  ENDFOR
  RETURN sum
ENDFUNCTION