FUNCTION uniqueIPs ACCEPTS(ipList)
    seen <- EMPTY SET
    uniqueList <- EMPTY LIST
    FOR EACH ip IN ipList DO
        IF ip NOT IN seen THEN
            CALL add_to_set(seen, ip)
            APPEND ip TO uniqueList
        ENDIF
    ENDFOR
    RETURN uniqueList
ENDFUNCTION