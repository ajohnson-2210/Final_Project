FUNCTION AreAnagrams ACCEPTS(str1, str2)
    IF LENGTH OF str1 != LENGTH OF str2 THEN
        RETURN BOOLEAN(False)
    ENDIF

    char_counts <- EMPTY DICTIONARY

    FOR EACH __reserved_keyword__char IN str1 DO
        char_counts[__reserved_keyword__char] <- char_counts[__reserved_keyword__char] + 1
    ENDFOR

    FOR EACH __reserved_keyword__char IN str2 DO
        IF __reserved_keyword__char NOT IN char_counts OR char_counts[__reserved_keyword__char] == 0 THEN
            RETURN BOOLEAN(False)
        ENDIF
        char_counts[__reserved_keyword__char] <- char_counts[__reserved_keyword__char] - 1
    ENDFOR

    RETURN BOOLEAN(True)
ENDFUNCTION