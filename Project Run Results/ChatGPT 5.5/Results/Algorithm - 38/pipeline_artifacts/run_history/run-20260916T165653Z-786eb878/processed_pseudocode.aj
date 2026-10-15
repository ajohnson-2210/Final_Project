    INPUT Text

    COUNT frequency of each character

    FOR EACH Character IN Text
        IF Frequency(Character) = 1 THEN
            OUTPUT Character
            STOP
        ENDIF
    ENDFOR

    OUTPUT "None Found"
END