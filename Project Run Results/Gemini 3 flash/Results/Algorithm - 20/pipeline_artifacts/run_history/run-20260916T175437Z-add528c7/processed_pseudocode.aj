FUNCTION FindDivisors ACCEPTS(n)
    divisors <- EMPTY LIST
    FOR i <- IN RANGE 1 TO ((n EXP 0.5)) + 1 DO
        IF n MODULUS i == 0 THEN
            APPEND i TO divisors
            IF i != (n INTEGER DIVISION i) THEN
                APPEND TUPLE(n INTEGER DIVISION i) TO divisors
            ENDIF
        ENDIF
    ENDFOR
    RETURN divisors
ENDFUNCTION