FUNCTION unnamed_function ACCEPTS(s)
    freq <- EMPTY DICTIONARY

    FOR EACH __reserved_keyword__char IN s DO
        freq[__reserved_keyword__char] <- freq.GET(__reserved_keyword__char, 0) + 1

    ENDFOR
    RETURN freq
ENDFUNCTION