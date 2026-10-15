FUNCTION areAnagrams ACCEPTS(str1, str2)
    IF LENGTH OF str1 != LENGTH OF str2 THEN
        RETURN BOOLEAN(False)
    ENDIF
    countArray <- CALL create_array(256, 0)
    FOR EACH __reserved_keyword__char IN str1 DO
        countArray[CHAR(__reserved_keyword__char)] <- countArray[CHAR(__reserved_keyword__char)] + 1
    ENDFOR
    FOR EACH __reserved_keyword__char IN str2 DO
        countArray[CHAR(__reserved_keyword__char)] <- countArray[CHAR(__reserved_keyword__char)] - 1
        IF countArray[CHAR(__reserved_keyword__char)] < 0 THEN
            RETURN BOOLEAN(False)
        ENDIF
    ENDFOR
    RETURN BOOLEAN(True)
ENDFUNCTION