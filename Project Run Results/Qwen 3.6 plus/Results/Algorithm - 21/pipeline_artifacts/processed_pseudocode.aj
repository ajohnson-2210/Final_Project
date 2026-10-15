FUNCTION unnamed_function ACCEPTS(num)
    IF num MODULUS 2 == 0 THEN
        RETURN STRING("Even")
    ELSE
        RETURN STRING("Odd")
    ENDIF
ENDFUNCTION