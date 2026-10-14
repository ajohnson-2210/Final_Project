COMMENT import random

OUTPUT STRING("Steps to Add 2 Equally Sized Matrices.")
rows <- RANDOM INT(2, 5)
cols <- RANDOM INT(2, 5)
OUTPUT STRING("STEP 1: Matrix size chosen: {rows} rows x {cols} columns\n")
OUTPUT STRING("STEP 2: Generating Matrix A...\n")
A <- EMPTY LIST
r <- 0
WHILE r < rows DO
    row_list <- EMPTY LIST
    c <- 0
    WHILE c < cols DO
        IF RANDOM FLOAT(0, 1) < 0.5 THEN
            num <- RANDOM INT(-10, 10)
        ELSE
            num <- CALL round(RANDOM FLOAT(-10, 10), 2)
        ENDIF
        APPEND num TO row_list
        c <- c + 1
    ENDWHILE
    APPEND row_list TO A
    r <- r + 1
ENDWHILE
OUTPUT STRING("Matrix A:\n")
r <- 0
WHILE r < rows DO
    OUTPUT A[r]
    r <- r + 1
ENDWHILE
OUTPUT STRING("\n")
OUTPUT STRING("STEP 3: Generating Matrix B...\n")
B <- EMPTY LIST
r <- 0
WHILE r < rows DO
    row_list <- EMPTY LIST
    c <- 0
    WHILE c < cols DO
        IF RANDOM FLOAT(0, 1) < 0.5 THEN
            num <- RANDOM INT(-10, 10)
        ELSE
            num <- CALL round(RANDOM FLOAT(-10, 10), 2)
        ENDIF
        APPEND num TO row_list
        c <- c + 1
    ENDWHILE
    APPEND row_list TO B
    r <- r + 1
ENDWHILE
OUTPUT STRING("Matrix B:\n")
r <- 0
WHILE r < rows DO
    OUTPUT B[r]
    r <- r + 1
ENDWHILE
OUTPUT STRING("\n")
OUTPUT STRING("STEP 4: Adding Matrix A and Matrix B...\n")
Result <- EMPTY LIST
r <- 0
OUTPUT STRING("Adding..")
WHILE r < rows DO
    row_list <- EMPTY LIST
    c <- 0
    WHILE c < cols DO
        sum_value <- A[r][c] + B[r][c]
        rounded_value <- CALL INTEGER((sum_value * 100)) / 100.0
        APPEND rounded_value TO row_list
        a_value <- A[r][c]
        b_value <- B[r][c]
        OUTPUT STRING("A[{r}][{c}] + B[{r}][{c}] → {a_value} + {b_value} =  {rounded_value}")
        c <- c + 1
    ENDWHILE
    APPEND row_list TO Result
    r <- r + 1
ENDWHILE
OUTPUT STRING("\nSTEP 5: Final Matrix\n")
OUTPUT STRING("\nA + B =")
r <- 0
WHILE r < rows DO
    OUTPUT Result[r]
    r <- r + 1
ENDWHILE