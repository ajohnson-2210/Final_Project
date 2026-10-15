    INPUT Number
    Binary <- ""

    IF Number = 0 THEN
        OUTPUT "0"
    ELSE
        WHILE Number > 0
            Remainder <- Number MOD 2
            Binary <- Remainder + Binary
            Number <- Number DIV 2
        ENDWHILE

        OUTPUT Binary
    ENDIF
END