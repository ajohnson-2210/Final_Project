    INPUT Text

    MaxLength <- 0

    FOR Start <- 0 TO LENGTH(Text)-1
        Seen <- Empty Set
        CurrentLength <- 0

        FOR End <- Start TO LENGTH(Text)-1
            IF Text[End] EXISTS IN Seen THEN
                EXIT FOR
            ENDIF

            ADD Text[End] TO Seen
            CurrentLength <- CurrentLength + 1
        ENDFOR

        IF CurrentLength > MaxLength THEN
            MaxLength <- CurrentLength
        ENDIF
    ENDFOR

    OUTPUT MaxLength
END