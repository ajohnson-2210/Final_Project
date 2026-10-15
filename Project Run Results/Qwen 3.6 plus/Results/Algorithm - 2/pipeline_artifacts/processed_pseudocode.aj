FUNCTION unnamed_function ACCEPTS(n)
    IF n == 0 THEN
        RETURN STRING("0")

    ENDIF
    binary <- EMPTY STRING

    WHILE n > 0 DO
        binary <- (n MODULUS 2) + binary
        n <- n INTEGER DIVISION 2

    ENDWHILE
    RETURN binary
ENDFUNCTION