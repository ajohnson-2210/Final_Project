matrix <- LIST [LIST [1, 2, 3], LIST [4, 5, 6], LIST [7, 8, 9]]
n <- LENGTH OF matrix
OUTPUT STRING("Matrix Before Rotation:")
row <- 0
loop <- BOOLEAN(TRUE)
WHILE loop DO
    TRY
        OUTPUT matrix[row]
        row <- row + 1
    CATCH
        loop <- BOOLEAN(FALSE)
    ENDTRY
ENDWHILE
row <- 0
loop <- BOOLEAN(TRUE)
WHILE loop DO
    col <- row + 1
    innerloop <- BOOLEAN(TRUE)
    WHILE innerloop DO
        TRY
            temp <- matrix[row][col]
            matrix[row][col] <- matrix[col][row]
            matrix[col][row] <- temp
            col <- col + 1
        CATCH
            innerloop <- BOOLEAN(FALSE)
        ENDTRY
    ENDWHILE
    row <- row + 1
    IF row >= n THEN
        loop <- BOOLEAN(FALSE)
    ENDIF
ENDWHILE
row <- 0
loop <- BOOLEAN(TRUE)
WHILE loop DO
    left <- 0
    right <- n - 1
    innerloop <- BOOLEAN(TRUE)
    WHILE innerloop DO
        IF left >= right THEN
            innerloop <- BOOLEAN(FALSE)
        ELSE
            temp <- matrix[row][left]
            matrix[row][left] <- matrix[row][right]
            matrix[row][right] <- temp
            left <- left + 1
            right <- right - 1
        ENDIF
    ENDWHILE
    row <- row + 1
    IF row >= n THEN
        loop <- BOOLEAN(FALSE)
    ENDIF
ENDWHILE
OUTPUT STRING("\nMatrix After 90° Clockwise Rotation:")
row <- 0
loop <- BOOLEAN(TRUE)
WHILE loop DO
    TRY
        OUTPUT matrix[row]
        row <- row + 1
    CATCH
        loop <- BOOLEAN(FALSE)
    ENDTRY
ENDWHILE