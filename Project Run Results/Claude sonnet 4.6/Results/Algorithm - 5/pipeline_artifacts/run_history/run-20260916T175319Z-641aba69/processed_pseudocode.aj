FUNCTION removePunctuation ACCEPTS(sentence)
    result <- EMPTY STRING
    FOR EACH __reserved_keyword__char IN sentence DO
        IF NOT CALL is_punctuation(__reserved_keyword__char) THEN
            result <- result + __reserved_keyword__char
        ENDIF
    ENDFOR
    RETURN result
ENDFUNCTION