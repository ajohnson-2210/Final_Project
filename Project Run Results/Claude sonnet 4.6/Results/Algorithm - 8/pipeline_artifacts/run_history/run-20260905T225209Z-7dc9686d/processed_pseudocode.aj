FUNCTION sortWords ACCEPTS(wordList)
    FOR i <- IN RANGE 0 TO (LENGTH OF wordList - 2) + 1 DO
        FOR j <- IN RANGE 0 TO (LENGTH OF wordList - i - 2) + 1 DO
            IF wordList[j] > wordList[j+1] THEN
                temp_var <- wordList[j]
                wordList[j] <- wordList[j+1]
                wordList[j+1] <- temp_var
            ENDIF
        ENDFOR
    ENDFOR
    RETURN wordList
ENDFUNCTION