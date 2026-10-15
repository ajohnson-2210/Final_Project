FUNCTION charFrequency ACCEPTS(str)
    freqMap <- EMPTY DICTIONARY
    FOR EACH __reserved_keyword__char IN str DO
        IF __reserved_keyword__char IN freqMap THEN
            freqMap[__reserved_keyword__char] <- freqMap[__reserved_keyword__char] + 1
        ELSE
            freqMap[__reserved_keyword__char] <- 1
        ENDIF
    ENDFOR
    RETURN freqMap
ENDFUNCTION