FUNCTION unnamed_function ACCEPTS(__reserved_keyword__List)
    sum <- 0

    FOR EACH num IN __reserved_keyword__List DO
        sum <- sum + num

    ENDFOR
    avg <- sum / LENGTH OF __reserved_keyword__List

    RETURN TUPLE(sum, avg)
ENDFUNCTION