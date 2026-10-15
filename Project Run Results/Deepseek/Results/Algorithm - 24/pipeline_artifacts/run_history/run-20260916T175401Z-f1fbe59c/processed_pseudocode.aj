FUNCTION isPasswordStrong ACCEPTS(password)
    IF LENGTH OF password < 8 THEN
        RETURN BOOLEAN(False)
    ENDIF
    hasNumber <- BOOLEAN(False)
    hasUpper <- BOOLEAN(False)
    FOR EACH __reserved_keyword__char IN password DO
        IF CALL is_digit(__reserved_keyword__char) THEN
            hasNumber <- BOOLEAN(True)
        ENDIF
        IF CALL is_uppercase(__reserved_keyword__char) THEN
            hasUpper <- BOOLEAN(True)
        ENDIF
    ENDFOR
    RETURN hasNumber AND hasUpper
ENDFUNCTION