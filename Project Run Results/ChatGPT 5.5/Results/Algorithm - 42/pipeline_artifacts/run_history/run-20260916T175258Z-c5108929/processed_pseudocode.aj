FUNCTION unnamed_function ACCEPTS(Array, Target)
    FOR i <- IN RANGE 0 TO (LENGTH OF Array - 2) + 1 DO
        FOR j <- IN RANGE i + 1 TO (LENGTH OF Array - 1) + 1 DO
            IF Array[i] + Array[j] == Target THEN
                OUTPUT CALL output_values(Array[i], Array[j])
            ENDIF
        ENDFOR
    ENDFOR
ENDFUNCTION