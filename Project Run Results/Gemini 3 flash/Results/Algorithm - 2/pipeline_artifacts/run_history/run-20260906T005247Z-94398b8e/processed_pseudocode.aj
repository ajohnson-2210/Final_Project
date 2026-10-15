FUNCTION DecimalToBinary ACCEPTS(n)
    IF n == 0 THEN
        RETURN STRING("0")

    ENDIF
    binary_str <- EMPTY STRING
    WHILE n > 0 DO
        remainder <- n MODULUS 2
        binary_str <- CALL to_string(remainder) + binary_str
        n <- n INTEGER DIVISION 2
    ENDWHILE

    RETURN binary_str
ENDFUNCTION