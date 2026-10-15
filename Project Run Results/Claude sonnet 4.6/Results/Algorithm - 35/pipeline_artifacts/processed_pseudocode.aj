FUNCTION LRUCache ACCEPTS(capacity)
    cache <- CALL create_ordered_dictionary()

    FUNCTION get ACCEPTS(key)
        IF key NOT IN cache THEN
            RETURN -1
        ENDIF
        MOVE key to most recently used position
        RETURN cache[key]

    ENDFUNCTION
    FUNCTION put ACCEPTS(key, value)
        IF key IN cache THEN
            REMOVE key
        ELSE IF LENGTH OF cache == capacity THEN
            REMOVE least recently CALL used (front) item
        ENDIF
        INSERT key:value at most recently used position
    ENDFUNCTION
ENDFUNCTION