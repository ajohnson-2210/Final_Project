FUNCTION linearSearch ACCEPTS(__reserved_keyword__List, T)
    FOR i <- IN RANGE 0 TO (LENGTH OF __reserved_keyword__List - 1) + 1 DO
        IF __reserved_keyword__List[i] == T THEN
            RETURN i
        ENDIF
    ENDFOR
    RETURN -1
ENDFUNCTION