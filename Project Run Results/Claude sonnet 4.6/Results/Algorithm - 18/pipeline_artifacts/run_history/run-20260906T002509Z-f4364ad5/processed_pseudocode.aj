FUNCTION charFrequency ACCEPTS(str)
    freq <- EMPTY DICTIONARY
    FOR EACH __reserved_keyword__char IN str DO
        IF __reserved_keyword__char IN freq THEN
            freq[__reserved_keyword__char] <- freq[__reserved_keyword__char] + 1
        ELSE
            freq[__reserved_keyword__char] <- 1
        ENDIF
    ENDFOR
    RETURN freq
ENDFUNCTION