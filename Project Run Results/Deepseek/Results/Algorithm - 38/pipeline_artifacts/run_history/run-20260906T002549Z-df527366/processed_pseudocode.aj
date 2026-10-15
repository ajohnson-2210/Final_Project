FUNCTION firstNonRepeating ACCEPTS(str)
    freqMap <- EMPTY DICTIONARY
    FOR EACH __reserved_keyword__char IN str DO
        freqMap[__reserved_keyword__char] <- freqMap.GET(__reserved_keyword__char, 0) + 1
    ENDFOR
    FOR EACH __reserved_keyword__char IN str DO
        IF freqMap[__reserved_keyword__char] == 1 THEN
            RETURN __reserved_keyword__char
        ENDIF
    ENDFOR
    RETURN NULL
    COMMENT or special character
ENDFUNCTION