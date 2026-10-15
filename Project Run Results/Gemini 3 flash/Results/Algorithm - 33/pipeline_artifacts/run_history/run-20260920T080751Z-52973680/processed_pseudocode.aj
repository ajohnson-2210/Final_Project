FUNCTION IntegerSquareRoot ACCEPTS(n)
    IF n < 2 THEN
        RETURN n

    ENDIF
    low <- 1
    high <- n INTEGER DIVISION 2
    ans <- 0

    WHILE low <= high DO
        mid <- low + (high - low) INTEGER DIVISION 2
        IF mid * mid == n THEN
            RETURN mid
        ELSE IF mid * mid < n THEN
            ans <- mid
            low <- mid + 1
        ELSE
            high <- mid - 1
        ENDIF
    ENDWHILE

    RETURN ans
ENDFUNCTION