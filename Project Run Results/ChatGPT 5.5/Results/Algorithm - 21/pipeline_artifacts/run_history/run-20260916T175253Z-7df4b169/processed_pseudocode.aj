FUNCTION unnamed_function ACCEPTS(Number)
        IF Number MODULUS 2 == 0 THEN
            OUTPUT STRING("Even")
        ELSE
            OUTPUT STRING("Odd")
        ENDIF
ENDFUNCTION