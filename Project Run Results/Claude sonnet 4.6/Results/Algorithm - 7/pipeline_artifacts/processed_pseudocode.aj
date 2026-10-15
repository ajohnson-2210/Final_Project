FUNCTION splitIntoWords ACCEPTS(sentence)
    words <- EMPTY LIST
    currentWord <- EMPTY STRING
    FOR EACH __reserved_keyword__char IN sentence DO
        IF __reserved_keyword__char == STRING(" ") THEN
            IF currentWord != EMPTY STRING THEN
                APPEND currentWord TO words
            ENDIF
            currentWord <- EMPTY STRING
        ELSE
            currentWord <- currentWord + __reserved_keyword__char
        ENDIF
    ENDFOR
    IF currentWord != EMPTY STRING THEN
        APPEND currentWord TO words
    ENDIF
    RETURN words
ENDFUNCTION