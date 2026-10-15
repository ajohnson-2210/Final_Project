FUNCTION rotateMatrix ACCEPTS(matrix, N)
    COMMENT Transpose
    FOR i <- IN RANGE 0 TO (N - 1) + 1 DO
        FOR j <- IN RANGE i+1 TO (N - 1) + 1 DO
            temp_var <- matrix[i][j]
            matrix[i][j] <- matrix[j][i]
            matrix[j][i] <- temp_var
    COMMENT Reverse each row
        ENDFOR
    ENDFOR
    FOR i <- IN RANGE 0 TO (N - 1) + 1 DO
        CALL reverse_list(matrix[i])
    ENDFOR
    RETURN matrix
ENDFUNCTION