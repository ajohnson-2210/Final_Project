FUNCTION ComputeFactorial ACCEPTS(n)
    IF n < 0 THEN
        RETURN NULL
    ENDIF
    result <- 1
    FOR i <- IN RANGE 1 TO (n) + 1 DO
        result <- result * i
    ENDFOR
    RETURN result
ENDFUNCTION