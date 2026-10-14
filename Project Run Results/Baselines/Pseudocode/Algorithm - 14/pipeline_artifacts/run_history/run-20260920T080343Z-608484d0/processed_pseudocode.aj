__reserved_keyword__list <- LIST [6, 7, 9, 4, 66, 8, 34, 5, 2]
total <- 0
FOR i <- IN RANGE 0 TO LENGTH OF __reserved_keyword__list DO
    IF (__reserved_keyword__list[i] MODULUS 2) == 0 THEN
        total <- total + __reserved_keyword__list[i]
    ELSE
        CONTINUE
    ENDIF
ENDFOR
OUTPUT STRING("The Sum of Even list elements = {total}")