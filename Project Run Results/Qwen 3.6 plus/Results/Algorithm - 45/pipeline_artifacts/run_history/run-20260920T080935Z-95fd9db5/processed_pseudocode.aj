FUNCTION unnamed_function ACCEPTS(A, B)
    result <- CALL create_matrix(LENGTH OF A, LENGTH OF A[0], NONE)

    FOR i <- IN RANGE 0 TO (LENGTH OF A-1) + 1 DO
        FOR j <- IN RANGE 0 TO (LENGTH OF A[0]-1) + 1 DO
            result[i][j] <- A[i][j] + B[i][j]

        ENDFOR
    ENDFOR
    RETURN result
ENDFUNCTION