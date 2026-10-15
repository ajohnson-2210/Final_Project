CLASS LRUCache ACCEPTS(capacity)
    given_capacity <- capacity
    cache <- EMPTY DICTIONARY
    order <- EMPTY LIST

    FUNCTION get ACCEPTS(key)
        IF key NOT IN cache THEN
            RETURN -1
            COMMENT or NULL
        COMMENT Move key to front of order (most recently used)
        ENDIF
        CALL remove_from_list(order, key)
        CALL insert_front(order, key)
        RETURN cache[key]
    ENDFUNCTION

    FUNCTION put ACCEPTS(key, value)
        IF key IN cache THEN
            COMMENT Update value and move key to front
            cache[key] <- value
            CALL remove_from_list(order, key)
            CALL insert_front(order, key)
        ELSE
            IF LENGTH OF order >= given_capacity THEN
                COMMENT Evict the least recently used (last element in order)
                lruKey <- order[-1]
                CALL remove_last_from_list(order)
                CALL remove_key(cache, lruKey)
            ENDIF
            CALL insert_front(order, key)
            cache[key] <- value
        ENDIF
    ENDFUNCTION
ENDCLASS