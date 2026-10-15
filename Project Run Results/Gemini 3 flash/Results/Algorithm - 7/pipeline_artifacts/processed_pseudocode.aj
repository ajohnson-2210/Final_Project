FUNCTION SplitSentence ACCEPTS(sentence)
    words <- EMPTY LIST
    current_word <- EMPTY STRING

    FOR EACH __reserved_keyword__char IN sentence DO
        IF __reserved_keyword__char == STRING(" ") THEN
            IF current_word != EMPTY STRING THEN
                APPEND current_word TO words
                current_word <- EMPTY STRING
            ENDIF
        ELSE
            current_word <- current_word + __reserved_keyword__char
        ENDIF
    ENDFOR

    IF current_word != EMPTY STRING THEN
        APPEND current_word TO words
    ENDIF

    RETURN words
ENDFUNCTION