FUNCTION unnamed_function ACCEPTS(Text)
        MaxLength <- 0

        FOR Start <- IN RANGE 0 TO (LENGTH OF Text-1) + 1 DO
            Seen <- EMPTY SET
            CurrentLength <- 0

            FOR End <- IN RANGE Start TO (LENGTH OF Text-1) + 1 DO
                IF Text[End] IN Seen THEN
                    BREAK
                ENDIF

                CALL add_to_set(Seen, Text[End])
                CurrentLength <- CurrentLength + 1
            ENDFOR

            IF CurrentLength > MaxLength THEN
                MaxLength <- CurrentLength
            ENDIF
        ENDFOR

        OUTPUT MaxLength
ENDFUNCTION