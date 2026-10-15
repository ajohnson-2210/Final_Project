FUNCTION factorial ACCEPTS(n)
    IF n == 0 OR n == 1 THEN
        RETURN 1
    ENDIF
    result <- 1
    FOR i <- IN RANGE 2 TO (n) + 1 DO
        result <- result * i
    ENDFOR
    RETURN result
ENDFUNCTION