FUNCTION findCommonElements ACCEPTS(list1, list2)
    set1 <- CALL to_set(list1)
    result <- EMPTY LIST
    FOR EACH item IN list2 DO
        IF item IN set1 AND item NOT IN result THEN
            APPEND item TO result
        ENDIF
    ENDFOR
    RETURN result
ENDFUNCTION