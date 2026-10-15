    INPUT Text

    Create empty Dictionary

    FOR EACH Character IN Text
        IF Character EXISTS in Dictionary THEN
            Dictionary[Character] <- Dictionary[Character] + 1
        ELSE
            Dictionary[Character] <- 1
        ENDIF
    ENDFOR

    OUTPUT Dictionary
END