FUNCTION uniqueIPs ACCEPTS(ipList)
    seen <- EMPTY SET
    result <- EMPTY LIST
    FOR EACH ip IN ipList DO
        IF ip NOT IN seen THEN
            CALL add_to_set(seen, ip)
            APPEND ip TO result
        ENDIF
    ENDFOR
    RETURN result
ENDFUNCTION