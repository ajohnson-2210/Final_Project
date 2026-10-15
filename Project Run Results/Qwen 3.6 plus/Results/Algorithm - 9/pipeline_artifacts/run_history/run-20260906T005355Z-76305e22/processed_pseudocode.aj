FUNCTION unnamed_function ACCEPTS(__reserved_keyword__List, target)
    FOR i <- IN RANGE 0 TO (LENGTH OF __reserved_keyword__List-1) + 1 DO
        IF __reserved_keyword__List[i] == target THEN
            RETURN i

        ENDIF
    ENDFOR
    RETURN STRING("Not Found")
ENDFUNCTION