FUNCTION sumAndAverage ACCEPTS(__reserved_keyword__List)
    sum <- 0
    FOR EACH num IN __reserved_keyword__List DO
        sum <- sum + num
    ENDFOR
    average <- sum / LENGTH OF __reserved_keyword__List
    RETURN TUPLE(sum, average)
ENDFUNCTION