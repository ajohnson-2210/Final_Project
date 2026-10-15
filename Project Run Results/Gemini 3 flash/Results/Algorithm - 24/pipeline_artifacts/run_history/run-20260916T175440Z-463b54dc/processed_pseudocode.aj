FUNCTION ValidatePassword ACCEPTS(password)
    IF LENGTH OF password < 8 THEN
        RETURN BOOLEAN(False)

    ENDIF
    has_digit <- BOOLEAN(False)
    has_uppercase <- BOOLEAN(False)

    FOR EACH __reserved_keyword__char IN password DO
        IF CALL is_digit(__reserved_keyword__char) THEN
            has_digit <- BOOLEAN(True)
        ENDIF
        IF CALL is_uppercase(__reserved_keyword__char) THEN
            has_uppercase <- BOOLEAN(True)
        ENDIF
    ENDFOR

    RETURN (has_digit AND has_uppercase)
ENDFUNCTION