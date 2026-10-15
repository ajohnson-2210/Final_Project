FUNCTION sumAndAverage ACCEPTS(__reserved_keyword__List)
    total <- 0
    FOR EACH num IN __reserved_keyword__List DO
        total <- total + num
    ENDFOR
    average <- total / LENGTH OF __reserved_keyword__List
    RETURN TUPLE(total, average)
ENDFUNCTION