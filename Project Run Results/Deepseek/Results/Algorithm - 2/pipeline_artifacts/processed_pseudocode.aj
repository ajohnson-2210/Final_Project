FUNCTION decimalToBinary ACCEPTS(n)
    IF n == 0 THEN
        RETURN STRING("0")
    ENDIF
    binaryString <- EMPTY STRING
    WHILE n > 0 DO
        remainder <- n MODULUS 2
        binaryString <- CALL to_string(remainder) + binaryString
        n <- n INTEGER DIVISION 2
    ENDWHILE
    RETURN binaryString
ENDFUNCTION