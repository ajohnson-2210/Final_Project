FUNCTION FindUniqueCommonElements ACCEPTS(list1, list2)
    set1 <- CALL to_set(list1)
    result_set <- EMPTY SET

    FOR EACH item IN list2 DO
        IF item IN set1 THEN
            CALL add_to_set(result_set, item)
        ENDIF
    ENDFOR

    RETURN CALL to_list(result_set)
ENDFUNCTION