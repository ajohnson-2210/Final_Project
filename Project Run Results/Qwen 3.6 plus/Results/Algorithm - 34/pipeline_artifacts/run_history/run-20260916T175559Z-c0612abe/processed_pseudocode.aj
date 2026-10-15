FUNCTION unnamed_function ACCEPTS(list1, list2)
    set1 <- CALL to_set(list1)
    result <- EMPTY LIST

    FOR EACH item IN list2 DO
        IF item in set1 AND item not in result THEN
            APPEND item TO result

        ENDIF
    ENDFOR
    RETURN CALL to_set(result)
ENDFUNCTION