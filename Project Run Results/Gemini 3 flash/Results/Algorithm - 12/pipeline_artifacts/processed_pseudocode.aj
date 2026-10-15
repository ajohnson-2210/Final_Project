FUNCTION SumMainDiagonal ACCEPTS(matrix, N)
    diagonal_sum <- 0
    FOR i <- IN RANGE 0 TO (N - 1) + 1 DO
        diagonal_sum <- diagonal_sum + matrix[i][i]
    ENDFOR
    RETURN diagonal_sum
ENDFUNCTION