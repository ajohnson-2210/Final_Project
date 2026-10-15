FUNCTION unnamed_function ACCEPTS(arr, target)
    seen <- EMPTY DICTIONARY
    pairs <- EMPTY LIST

    FOR EACH num IN arr DO
        comp <- target - num

        IF comp in seen THEN
            APPEND TUPLE(CALL min(num, comp), CALL max(num, comp)) TO pairs

        ENDIF
        seen[num] <- BOOLEAN(True)

    ENDFOR
    RETURN CALL to_set(pairs)
ENDFUNCTION