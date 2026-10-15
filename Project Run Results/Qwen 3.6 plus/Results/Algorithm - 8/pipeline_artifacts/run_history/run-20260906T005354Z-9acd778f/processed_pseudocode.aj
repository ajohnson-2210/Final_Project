FUNCTION unnamed_function ACCEPTS(wordList)
    FOR i <- IN RANGE 0 TO (LENGTH OF wordList-1) + 1 DO
        FOR j <- IN RANGE i+1 TO (LENGTH OF wordList-1) + 1 DO
            IF wordList[j] < wordList[i] THEN
                temp_var <- wordList[i]
                wordList[i] <- wordList[j]
                wordList[j] <- temp_var

            ENDIF
        ENDFOR
    ENDFOR
    RETURN wordList
ENDFUNCTION