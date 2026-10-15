FUNCTION unnamed_function ACCEPTS(sentence)
    cleaned <- EMPTY STRING

    FOR EACH __reserved_keyword__char IN sentence DO
        IF NOT CALL is_punctuation(__reserved_keyword__char) THEN
            cleaned <- cleaned + __reserved_keyword__char

        ENDIF
    ENDFOR
    RETURN cleaned
ENDFUNCTION