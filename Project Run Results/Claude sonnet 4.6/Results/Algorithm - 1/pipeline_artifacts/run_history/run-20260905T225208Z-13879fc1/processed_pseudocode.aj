FUNCTION isAnagram ACCEPTS(str1, str2)
    IF LENGTH OF str1 != LENGTH OF str2 THEN
        RETURN BOOLEAN(False)
    ENDIF
    sorted1 <- CALL sort_characters(str1)
    sorted2 <- CALL sort_characters(str2)
    RETURN sorted1 == sorted2
ENDFUNCTION