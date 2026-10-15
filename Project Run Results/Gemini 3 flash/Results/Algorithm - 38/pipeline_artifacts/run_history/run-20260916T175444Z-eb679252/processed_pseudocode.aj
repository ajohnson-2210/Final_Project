FUNCTION FirstNonRepeatingChar ACCEPTS(str)
    counts <- EMPTY DICTIONARY

    FOR EACH __reserved_keyword__char IN str DO
        counts[__reserved_keyword__char] <- counts[__reserved_keyword__char] + 1
    ENDFOR

    FOR EACH __reserved_keyword__char IN str DO
        IF counts[__reserved_keyword__char] == 1 THEN
            RETURN __reserved_keyword__char
        ENDIF
    ENDFOR

    RETURN NULL
ENDFUNCTION