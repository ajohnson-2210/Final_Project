FUNCTION sortWords ACCEPTS(words)
    COMMENT Using a simple bubble sort for demonstration
    n <- LENGTH OF words
    FOR i <- IN RANGE 0 TO (n-2) + 1 DO
        FOR j <- IN RANGE 0 TO (n-i-2) + 1 DO
            IF words[j] > words[j+1] THEN
                temp_var <- words[j]
                words[j] <- words[j+1]
                words[j+1] <- temp_var
            ENDIF
        ENDFOR
    ENDFOR
    RETURN words
ENDFUNCTION