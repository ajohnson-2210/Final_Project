FUNCTION integerSqrt ACCEPTS(n)
    IF n < 2 THEN
        RETURN n
    ENDIF
    low <- 1
    high <- n
    ans <- 0
    WHILE low <= high DO
        mid <- (low + high) INTEGER DIVISION 2
        square <- mid * mid
        IF square == n THEN
            RETURN mid
        ELSE IF square < n THEN
            ans <- mid
            low <- mid + 1
        ELSE
            high <- mid - 1
        ENDIF
    ENDWHILE
    RETURN ans
ENDFUNCTION