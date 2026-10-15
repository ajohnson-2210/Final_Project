FUNCTION ComputeSumAndAverage ACCEPTS(numbers)
    IF LENGTH OF numbers == 0 THEN
        RETURN TUPLE(0, 0)

    ENDIF
    total_sum <- 0
    FOR EACH num IN numbers DO
        total_sum <- total_sum + num
    ENDFOR

    average <- total_sum / LENGTH OF numbers
    RETURN TUPLE(total_sum, average)
ENDFUNCTION