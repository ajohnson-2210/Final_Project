FUNCTION GetUniqueIPs ACCEPTS(ip_list)
    unique_set <- EMPTY SET
    FOR EACH ip IN ip_list DO
        CALL add_to_set(unique_set, ip)
    ENDFOR
    RETURN CALL to_list(unique_set)
ENDFUNCTION