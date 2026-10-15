FUNCTION commonElements ACCEPTS(list1, list2)
    set1 <- CALL to_set(list1)
    result <- EMPTY SET
    FOR EACH item IN list2 DO
        IF item IN set1 THEN
            CALL add_to_set(result, item)
        ENDIF
    ENDFOR
    RETURN CALL to_list(result)
ENDFUNCTION