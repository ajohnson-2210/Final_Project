FUNCTION unnamed_function ACCEPTS(n)
    divs <- EMPTY LIST

    FOR i <- IN RANGE 1 TO (n) + 1 DO
        IF n MODULUS i == 0 THEN
            APPEND i TO divs

        ENDIF
    ENDFOR
    RETURN divs
ENDFUNCTION