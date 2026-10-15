FUNCTION unnamed_function ACCEPTS(__reserved_keyword__List, Target)
    Found <- BOOLEAN(False)

    FOR i <- IN RANGE 0 TO (LENGTH OF __reserved_keyword__List - 1) + 1 DO
        IF __reserved_keyword__List[i] == Target THEN
            OUTPUT STRING("Found at position {i}")
            Found <- BOOLEAN(True)
            BREAK
        ENDIF
    ENDFOR

    IF Found == BOOLEAN(False) THEN
        OUTPUT STRING("Target not found")
    ENDIF
ENDFUNCTION