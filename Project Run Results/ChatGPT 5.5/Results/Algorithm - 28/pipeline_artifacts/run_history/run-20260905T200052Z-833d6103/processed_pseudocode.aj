FUNCTION unnamed_function ACCEPTS(Array, WindowSize)
        FOR i <- IN RANGE 0 TO (LENGTH OF Array - WindowSize) + 1 DO
            Maximum <- Array[i]

            FOR j <- IN RANGE i TO (i + WindowSize - 1) + 1 DO
                IF Array[j] > Maximum THEN
                    Maximum <- Array[j]
                ENDIF
            ENDFOR

            OUTPUT Maximum
        ENDFOR
ENDFUNCTION