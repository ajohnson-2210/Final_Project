FUNCTION evenOrOdd ACCEPTS(number)
    IF number MODULUS 2 == 0 THEN
        RETURN STRING("Even")
    ELSE
        RETURN STRING("Odd")
    ENDIF
ENDFUNCTION