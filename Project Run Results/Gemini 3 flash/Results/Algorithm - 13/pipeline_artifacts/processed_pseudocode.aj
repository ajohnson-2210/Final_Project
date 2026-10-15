FUNCTION ReverseString ACCEPTS(str)
    reversed_str <- EMPTY STRING
    FOR i <- IN RANGE LENGTH OF str - 1 TO (0) - 1 STEP -1 DO
        reversed_str <- reversed_str + str[i]
    ENDFOR
    RETURN reversed_str
ENDFUNCTION