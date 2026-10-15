FUNCTION unnamed_function ACCEPTS(__reserved_keyword__List)
    total <- 0

    FOR EACH num IN __reserved_keyword__List DO
        IF num MODULUS 2 == 0 THEN
            total <- total + num

        ENDIF
    ENDFOR
    RETURN total
ENDFUNCTION