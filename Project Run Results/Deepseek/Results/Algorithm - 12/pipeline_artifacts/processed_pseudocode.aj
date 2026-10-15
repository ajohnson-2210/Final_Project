FUNCTION diagonalSum ACCEPTS(grid, N)
    sum <- 0
    FOR i <- IN RANGE 0 TO (N-1) + 1 DO
        sum <- sum + grid[i][i]
    ENDFOR
    RETURN sum
ENDFUNCTION