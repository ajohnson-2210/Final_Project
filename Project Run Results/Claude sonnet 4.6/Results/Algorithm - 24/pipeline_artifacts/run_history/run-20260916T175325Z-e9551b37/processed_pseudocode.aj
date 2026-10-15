FUNCTION validatePassword ACCEPTS(password)
    IF LENGTH OF password < 8 THEN
        RETURN BOOLEAN(False)
    ENDIF
    hasDigit <- BOOLEAN(False)
    hasUpper <- BOOLEAN(False)
    FOR EACH __reserved_keyword__char IN password DO
        IF CALL is_digit(__reserved_keyword__char) THEN
            hasDigit <- BOOLEAN(True)
        ENDIF
        IF CALL is_uppercase(__reserved_keyword__char) THEN
            hasUpper <- BOOLEAN(True)
        ENDIF
    ENDFOR
    RETURN hasDigit AND hasUpper
ENDFUNCTION