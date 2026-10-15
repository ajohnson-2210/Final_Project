FUNCTION stringLength ACCEPTS(str)
    count <- 0
    FOR EACH character IN str DO
        count <- count + 1
    ENDFOR
    RETURN count
ENDFUNCTION