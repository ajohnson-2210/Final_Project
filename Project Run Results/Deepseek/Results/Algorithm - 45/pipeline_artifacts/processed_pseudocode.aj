FUNCTION addMatrices ACCEPTS(A, B, rows, cols)
    result <- CALL create_matrix(rows, cols, NONE)
    FOR i <- IN RANGE 0 TO (rows-1) + 1 DO
        FOR j <- IN RANGE 0 TO (cols-1) + 1 DO
            result[i][j] <- A[i][j] + B[i][j]
        ENDFOR
    ENDFOR
    RETURN result
ENDFUNCTION