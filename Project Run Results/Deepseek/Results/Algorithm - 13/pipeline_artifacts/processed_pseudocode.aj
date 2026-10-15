FUNCTION reverseString ACCEPTS(str)
    reversed <- EMPTY STRING
    FOR i <- IN RANGE LENGTH OF str-1 TO (0) - 1 STEP -1 DO
        reversed <- reversed + str[i]
    ENDFOR
    RETURN reversed
ENDFUNCTION