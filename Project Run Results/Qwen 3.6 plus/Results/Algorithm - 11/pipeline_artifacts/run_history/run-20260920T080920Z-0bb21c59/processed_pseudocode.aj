FUNCTION unnamed_function ACCEPTS(ipList)
    uniqueSet <- EMPTY SET

    FOR EACH ip IN ipList DO
        CALL add_to_set(uniqueSet, ip)
    ENDFOR
    RETURN CALL to_list(uniqueSet)
ENDFUNCTION