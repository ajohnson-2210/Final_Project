FUNCTION unnamed_function ACCEPTS(sentence)
    words <- EMPTY LIST
    current <- EMPTY STRING

    FOR EACH __reserved_keyword__char IN sentence DO
        IF __reserved_keyword__char == CHAR(" ") THEN
            IF current != EMPTY STRING THEN
                APPEND current TO words
                current <- EMPTY STRING
            ENDIF
        ELSE
            current <- current + __reserved_keyword__char

        ENDIF
    ENDFOR
    IF current != EMPTY STRING THEN
        APPEND current TO words

    ENDIF
    RETURN words
ENDFUNCTION