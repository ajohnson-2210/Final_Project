FUNCTION multiplyMatrices ACCEPTS(A, B, rowsA, colsA, colsB)
    COMMENT Assumes A is rowsA x colsA, B is colsA x colsB
    result <- CALL create_matrix(rowsA, colsB, 0)
    FOR i <- IN RANGE 0 TO (rowsA-1) + 1 DO
        FOR j <- IN RANGE 0 TO (colsB-1) + 1 DO
            sum <- 0
            FOR k <- IN RANGE 0 TO (colsA-1) + 1 DO
                sum <- sum + A[i][k] * B[k][j]
            ENDFOR
            result[i][j] <- sum
        ENDFOR
    ENDFOR
    RETURN result
ENDFUNCTION