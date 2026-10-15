FUNCTION decimalToBinary ACCEPTS(n)
    IF n == 0 THEN
        RETURN STRING("0")
    ENDIF
    result <- EMPTY STRING
    WHILE n > 0 DO
        result <- (n MODULUS 2) + result
        n <- n INTEGER DIVISION 2
    ENDWHILE
    RETURN result
ENDFUNCTION