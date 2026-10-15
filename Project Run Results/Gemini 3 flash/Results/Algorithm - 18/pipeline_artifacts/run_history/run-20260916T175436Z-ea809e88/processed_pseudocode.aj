FUNCTION CharacterFrequency ACCEPTS(str)
    freq_map <- EMPTY DICTIONARY
    FOR EACH __reserved_keyword__char IN str DO
        IF __reserved_keyword__char IN freq_map THEN
            freq_map[__reserved_keyword__char] <- freq_map[__reserved_keyword__char] + 1
        ELSE
            freq_map[__reserved_keyword__char] <- 1
        ENDIF
    ENDFOR
    RETURN freq_map
ENDFUNCTION