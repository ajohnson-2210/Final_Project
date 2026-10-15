FUNCTION stringLength ACCEPTS(str)
    count <- 0
    FOR EACH __reserved_keyword__char IN str DO
        count <- count + 1
    ENDFOR
    RETURN count
ENDFUNCTION