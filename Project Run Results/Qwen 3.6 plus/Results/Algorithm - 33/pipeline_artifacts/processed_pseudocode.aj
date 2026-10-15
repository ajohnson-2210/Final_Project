FUNCTION unnamed_function ACCEPTS(n)
    IF n < 2 THEN
        RETURN n

    ENDIF
    left <- 1
    right <- n INTEGER DIVISION 2
    ans <- 1

    WHILE left <= right DO
        mid <- (left + right) INTEGER DIVISION 2

        IF mid * mid <= n THEN
            ans <- mid
            left <- mid + 1
        ELSE
            right <- mid - 1

        ENDIF
    ENDWHILE
    RETURN ans
ENDFUNCTION