FUNCTION unnamed_function ACCEPTS(WordList)
    FOR i <- IN RANGE 0 TO (LENGTH OF WordList - 2) + 1 DO
        FOR j <- IN RANGE 0 TO (LENGTH OF WordList - 2 - i) + 1 DO
            IF WordList[j] > WordList[j + 1] THEN
                CALL swap(WordList, j, j + 1)
            ENDIF
        ENDFOR
    ENDFOR

    OUTPUT WordList
ENDFUNCTION