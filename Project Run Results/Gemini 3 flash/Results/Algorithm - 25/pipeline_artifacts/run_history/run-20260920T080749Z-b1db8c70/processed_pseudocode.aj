FUNCTION LongestUniqueSubstringLength ACCEPTS(str)
    char_map <- EMPTY DICTIONARY
    max_len <- 0
    start <- 0

    FOR end <- IN RANGE 0 TO (LENGTH OF str - 1) + 1 DO
        __reserved_keyword__char <- str[end]
        IF __reserved_keyword__char IN char_map AND char_map[__reserved_keyword__char] >= start THEN
            start <- char_map[__reserved_keyword__char] + 1
        ENDIF
        char_map[__reserved_keyword__char] <- end
        max_len <- CALL max(max_len, end - start + 1)
    ENDFOR

    RETURN max_len
ENDFUNCTION