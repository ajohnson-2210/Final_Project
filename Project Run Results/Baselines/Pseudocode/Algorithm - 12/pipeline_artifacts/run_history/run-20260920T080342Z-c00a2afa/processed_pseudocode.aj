COMMENT import random

rows <- RANDOM INT(3, 15)
OUTPUT STRING("{rows} x {rows} Matrix")
x <- rows
y <- rows
matrix <- EMPTY LIST
FOR j <- IN RANGE 0 TO x DO
    row_values <- EMPTY LIST
    FOR i <- IN RANGE 0 TO y DO
        APPEND RANDOM INT(0, 99) TO row_values
    ENDFOR
    APPEND row_values TO matrix
ENDFOR
FOR t <- IN RANGE 0 TO rows DO
    OUTPUT matrix[t]
ENDFOR
total <- 0
counter <- 0
__reserved_keyword__string <- EMPTY STRING
FOR a <- IN RANGE 0 TO rows DO
    diagonal_value <- matrix[counter][counter]
    total <- total + diagonal_value
    IF __reserved_keyword__string == EMPTY STRING THEN
        __reserved_keyword__string <- __reserved_keyword__string + CALL STRING(diagonal_value) + STRING(" ")
    ELSE
        __reserved_keyword__string <- __reserved_keyword__string + STRING("+ ") + CALL STRING(diagonal_value) + STRING(" ")
    ENDIF
    counter <- counter + 1
ENDFOR
OUTPUT STRING("{__reserved_keyword__string} = {total}")