FUNCTION unnamed_function ACCEPTS(pwd)
    IF LENGTH OF pwd < 8 THEN
        RETURN BOOLEAN(False)

    ENDIF
    hasNum <- BOOLEAN(False)
    hasUpper <- BOOLEAN(False)

    FOR EACH __reserved_keyword__char IN pwd DO
        IF CALL is_digit(__reserved_keyword__char) THEN
            hasNum <- BOOLEAN(True)
        ENDIF
        IF CALL is_uppercase(__reserved_keyword__char) THEN
            hasUpper <- BOOLEAN(True)

        ENDIF
    ENDFOR
    RETURN hasNum AND hasUpper
ENDFUNCTION