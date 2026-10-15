FUNCTION unnamed_function ACCEPTS(str1, str2)
    IF LENGTH OF str1 != LENGTH OF str2 THEN
        RETURN BOOLEAN(False)

    ENDIF
    charCounts <- EMPTY DICTIONARY

    FOR EACH __reserved_keyword__char IN str1 DO
        charCounts[__reserved_keyword__char] <- charCounts[__reserved_keyword__char] + 1

    ENDFOR
    FOR EACH __reserved_keyword__char IN str2 DO
        charCounts[__reserved_keyword__char] <- charCounts[__reserved_keyword__char] - 1

    ENDFOR
    FOR EACH count IN charCounts DO
        IF count != 0 THEN
            RETURN BOOLEAN(False)

        ENDIF
    ENDFOR
    RETURN BOOLEAN(True)
ENDFUNCTION