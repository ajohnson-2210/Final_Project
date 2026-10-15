    FOR i <- IN RANGE 0 TO (N - 1) + 1 DO
        FOR j <- IN RANGE i TO (N - 1) + 1 DO
            temp_var <- matrix[i][j]
            matrix[i][j] <- matrix[j][i]
            matrix[j][i] <- temp_var
        ENDFOR
    ENDFOR

    COMMENT Step 2: Reverse each row
    FOR i <- IN RANGE 0 TO (N - 1) + 1 DO
        left <- 0
        right <- N - 1
        WHILE left < right DO
            temp_var <- matrix[i][left]
            matrix[i][left] <- matrix[i][right]
            matrix[i][right] <- temp_var
            left <- left + 1
            right <- right - 1
        ENDWHILE
    ENDFOR
ENDFUNCTION