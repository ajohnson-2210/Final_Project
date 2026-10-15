FUNCTION MultiplyMatrices ACCEPTS(A, B, r1, c1, r2, c2)
    IF c1 != r2 THEN
        RETURN STRING("Invalid matrix dimensions")

    ENDIF
    C <- CALL create_matrix(r1, c2, 0)
    FOR i <- IN RANGE 0 TO (r1 - 1) + 1 DO
        FOR j <- IN RANGE 0 TO (c2 - 1) + 1 DO
            FOR k <- IN RANGE 0 TO (c1 - 1) + 1 DO
                C[i][j] <- C[i][j] + (A[i][k] * B[k][j])
            ENDFOR
        ENDFOR
    ENDFOR
    RETURN C
ENDFUNCTION