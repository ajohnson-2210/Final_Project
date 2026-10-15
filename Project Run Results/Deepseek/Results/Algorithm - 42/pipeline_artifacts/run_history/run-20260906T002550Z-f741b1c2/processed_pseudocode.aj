FUNCTION findPairs ACCEPTS(arr, target)
    seen <- EMPTY SET
    result <- EMPTY LIST
    FOR EACH num IN arr DO
        complement <- target - num
        IF complement IN seen THEN
            APPEND TUPLE(num, complement) TO result
        ENDIF
        CALL add_to_set(seen, num)
    ENDFOR
    RETURN result
ENDFUNCTION