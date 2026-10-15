FUNCTION diagonalSum ACCEPTS(grid, N)
    total <- 0
    FOR i <- IN RANGE 0 TO (N - 1) + 1 DO
        total <- total + grid[i][i]
    ENDFOR
    RETURN total
ENDFUNCTION