FUNCTION unnamed_function ACCEPTS(Number)
        FOR i <- IN RANGE 1 TO (Number) + 1 DO
            IF Number MODULUS i == 0 THEN
                OUTPUT i
            ENDIF
        ENDFOR
ENDFUNCTION