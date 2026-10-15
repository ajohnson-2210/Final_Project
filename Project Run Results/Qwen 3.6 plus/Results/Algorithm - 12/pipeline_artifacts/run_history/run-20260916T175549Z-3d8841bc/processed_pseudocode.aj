FUNCTION unnamed_function ACCEPTS(matrix)
    sum <- 0

    FOR i <- IN RANGE 0 TO LENGTH OF matrix DO
        sum <- sum + matrix[i][i]

    ENDFOR
    RETURN sum
ENDFUNCTION