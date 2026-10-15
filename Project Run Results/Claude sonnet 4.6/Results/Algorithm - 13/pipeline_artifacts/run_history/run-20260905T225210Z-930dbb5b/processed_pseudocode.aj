FUNCTION reverseString ACCEPTS(str)
    result <- EMPTY STRING
    FOR i <- IN RANGE LENGTH OF str - 1 TO (0) - 1 STEP -1 DO
        result <- result + str[i]
    ENDFOR
    RETURN result
ENDFUNCTION