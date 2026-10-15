FUNCTION SumEvenNumbers ACCEPTS(numbers)
    total_sum <- 0
    FOR EACH num IN numbers DO
        IF num MODULUS 2 == 0 THEN
            total_sum <- total_sum + num
        ENDIF
    ENDFOR
    RETURN total_sum
ENDFUNCTION