FUNCTION findPairs ACCEPTS(arr, target)
    seen <- EMPTY SET
    pairs <- EMPTY LIST
    FOR EACH num IN arr DO
        complement <- target - num
        IF complement IN seen THEN
            APPEND TUPLE(complement, num) TO pairs
        ENDIF
        CALL add_to_set(seen, num)
    ENDFOR
    RETURN pairs
ENDFUNCTION