FUNCTION RemovePunctuation ACCEPTS(sentence)
    punctuation_set <- CALL to_set(CALL list_value(STRING("."), STRING(","), STRING("!"), STRING("?"), STRING(";"), STRING(":"), STRING("-"), STRING("'"), STRING("\""), STRING("("), STRING(")")))
    clean_sentence <- EMPTY STRING

    FOR EACH __reserved_keyword__char IN sentence DO
        IF __reserved_keyword__char NOT IN punctuation_set THEN
            clean_sentence <- clean_sentence + __reserved_keyword__char
        ENDIF
    ENDFOR

    RETURN clean_sentence
ENDFUNCTION