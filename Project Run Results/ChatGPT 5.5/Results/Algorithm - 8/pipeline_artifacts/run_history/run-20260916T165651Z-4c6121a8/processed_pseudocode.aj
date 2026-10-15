    INPUT WordList

    FOR i <- 0 TO LENGTH(WordList)-2
        FOR j <- 0 TO LENGTH(WordList)-2-i
            IF WordList[j] > WordList[j+1] THEN
                SWAP WordList[j], WordList[j+1]
            ENDIF
        ENDFOR
    ENDFOR

    OUTPUT WordList
END