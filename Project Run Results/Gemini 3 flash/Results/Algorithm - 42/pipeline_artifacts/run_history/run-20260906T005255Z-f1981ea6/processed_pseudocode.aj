FUNCTION FindPairsWithSum ACCEPTS(arr, target)
    seen <- EMPTY SET
    pairs <- EMPTY SET

    FOR EACH num IN arr DO
        complement <- target - num
        IF complement IN seen THEN
            CALL add_to_set(pairs, TUPLE(CALL min(num, complement), CALL max(num, complement)))
        ENDIF
        CALL add_to_set(seen, num)
    ENDFOR

    RETURN pairs
ENDFUNCTION