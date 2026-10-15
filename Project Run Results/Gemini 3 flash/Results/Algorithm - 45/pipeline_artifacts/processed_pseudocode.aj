FUNCTION AddMatrices ACCEPTS(A, B, rows, cols)
    C <- CALL create_matrix(rows, cols, 0)
    FOR i <- IN RANGE 0 TO (rows - 1) + 1 DO
        FOR j <- IN RANGE 0 TO (cols - 1) + 1 DO
            C[i][j] <- A[i][j] + B[i][j]
        ENDFOR
    ENDFOR
    RETURN C
ENDFUNCTION