FUNCTION intSqrt ACCEPTS(n)
    IF n == 0 THEN
        RETURN 0
    ENDIF
    low <- 1
    high <- n
    WHILE low <= high DO
        mid <- (low + high) INTEGER DIVISION 2
        IF mid * mid == n THEN
            RETURN mid
        ELSE IF mid * mid < n THEN
            result <- mid
            low <- mid + 1
        ELSE
            high <- mid - 1
        ENDIF
    ENDWHILE
    RETURN result
ENDFUNCTION