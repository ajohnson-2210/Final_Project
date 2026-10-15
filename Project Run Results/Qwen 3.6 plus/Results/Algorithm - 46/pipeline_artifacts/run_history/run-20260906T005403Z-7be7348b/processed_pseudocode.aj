FUNCTION unnamed_function ACCEPTS(A, B)
    C <- CALL create_matrix(LENGTH OF A, LENGTH OF B[0], NONE)

    FOR i <- IN RANGE 0 TO (LENGTH OF A-1) + 1 DO
        FOR j <- IN RANGE 0 TO (LENGTH OF B[0]-1) + 1 DO
            sum <- 0

            FOR k <- IN RANGE 0 TO (LENGTH OF B-1) + 1 DO
                sum <- sum + A[i][k] * B[k][j]

            ENDFOR
            C[i][j] <- sum

        ENDFOR
    ENDFOR
    RETURN C
ENDFUNCTION