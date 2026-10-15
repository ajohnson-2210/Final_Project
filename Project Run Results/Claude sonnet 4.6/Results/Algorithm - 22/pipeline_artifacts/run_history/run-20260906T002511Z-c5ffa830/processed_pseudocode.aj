FUNCTION factorial ACCEPTS(n)
    IF n == 0 OR n == 1 THEN
        RETURN 1
    ENDIF
    RETURN n * CALL factorial(n - 1)
ENDFUNCTION