FUNCTION firstNonRepeating ACCEPTS(str)
    freq <- EMPTY DICTIONARY
    FOR EACH __reserved_keyword__char IN str DO
        freq[__reserved_keyword__char] <- freq.GET(__reserved_keyword__char, 0) + 1
    ENDFOR
    FOR EACH __reserved_keyword__char IN str DO
        IF freq[__reserved_keyword__char] == 1 THEN
            RETURN __reserved_keyword__char
        ENDIF
    ENDFOR
    RETURN NONE
ENDFUNCTION