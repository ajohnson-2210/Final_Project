FUNCTION removePunctuation ACCEPTS(sentence)
    punctuation <- CALL to_set(STRING(". , ! ? ; : ' \" - ( ) [ ] { }"))
    result <- EMPTY STRING
    FOR EACH __reserved_keyword__char IN sentence DO
        IF __reserved_keyword__char NOT IN punctuation THEN
            result <- result + __reserved_keyword__char
        ENDIF
    ENDFOR
    RETURN result
ENDFUNCTION