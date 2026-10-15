FUNCTION sumEven ACCEPTS(__reserved_keyword__List)
    sum <- 0
    FOR EACH num IN __reserved_keyword__List DO
        IF num MODULUS 2 == 0 THEN
            sum <- sum + num
        ENDIF
    ENDFOR
    RETURN sum
ENDFUNCTION