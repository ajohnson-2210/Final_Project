FUNCTION multiplyMatrices ACCEPTS(A, B, n, m, p)
    COMMENT A is n*m, B is m*p
    result <- CALL create_matrix(n, p, 0)
    FOR i <- IN RANGE 0 TO (n - 1) + 1 DO
        FOR j <- IN RANGE 0 TO (p - 1) + 1 DO
            FOR k <- IN RANGE 0 TO (m - 1) + 1 DO
                result[i][j] <- result[i][j] + A[i][k] * B[k][j]
            ENDFOR
        ENDFOR
    ENDFOR
    RETURN result
ENDFUNCTION