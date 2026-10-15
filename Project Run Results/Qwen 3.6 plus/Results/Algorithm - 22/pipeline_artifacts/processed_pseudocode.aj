FUNCTION unnamed_function ACCEPTS(n)
    result <- 1

    FOR i <- IN RANGE 2 TO (n) + 1 DO
        result <- result * i

    ENDFOR
    RETURN result
ENDFUNCTION