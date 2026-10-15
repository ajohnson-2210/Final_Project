    INPUT Sentence
    Result <- ""

    FOR EACH Character IN Sentence
        IF Character is NOT punctuation THEN
            Result <- Result + Character
        ENDIF
    ENDFOR

    OUTPUT Result
END