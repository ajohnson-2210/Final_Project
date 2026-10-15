FUNCTION unnamed_function ACCEPTS(s)
    count <- 0

    FOR EACH __reserved_keyword__char IN s DO
        count <- count + 1

    ENDFOR
    RETURN count
ENDFUNCTION