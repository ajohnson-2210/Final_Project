FUNCTION unnamed_function ACCEPTS(matrix)
    FOR i <- IN RANGE 0 TO (LENGTH OF matrix/2 - 1) + 1 DO
        FOR j <- IN RANGE i TO (LENGTH OF matrix-1-i-1) + 1 DO
            temp <- matrix[i][j]
            matrix[i][j] <- matrix[LENGTH OF matrix-1-j][i]
            matrix[LENGTH OF matrix-1-j][i] <- matrix[LENGTH OF matrix-1-i][LENGTH OF matrix-1-j]
            matrix[LENGTH OF matrix-1-i][LENGTH OF matrix-1-j] <- matrix[j][LENGTH OF matrix-1-i]
            matrix[j][LENGTH OF matrix-1-i] <- temp

        ENDFOR
    ENDFOR
    RETURN matrix
ENDFUNCTION