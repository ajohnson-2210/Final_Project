FUNCTION unnamed_function ACCEPTS(Number)
        Binary <- EMPTY STRING

        IF Number == 0 THEN
            OUTPUT STRING("0")
        ELSE
            WHILE Number > 0 DO
                Remainder <- Number MODULUS 2
                Binary <- Remainder + Binary
                Number <- Number INTEGER DIVISION 2
            ENDWHILE

            OUTPUT Binary
        ENDIF
ENDFUNCTION