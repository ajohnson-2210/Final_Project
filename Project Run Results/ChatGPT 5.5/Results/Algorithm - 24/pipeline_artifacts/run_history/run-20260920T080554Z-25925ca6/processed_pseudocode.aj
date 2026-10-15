FUNCTION unnamed_function ACCEPTS(Password)
        HasNumber <- BOOLEAN(False)
        HasUpper <- BOOLEAN(False)

        IF LENGTH OF Password < 8 THEN
            OUTPUT STRING("Invalid Password")
        ELSE
            FOR EACH Character IN Password DO
                IF CALL is_digit(Character) THEN
                    HasNumber <- BOOLEAN(True)
                ENDIF

                IF CALL is_uppercase(Character) THEN
                    HasUpper <- BOOLEAN(True)
                ENDIF
            ENDFOR

            IF HasNumber == BOOLEAN(True) AND HasUpper == BOOLEAN(True) THEN
                OUTPUT STRING("Valid Password")
            ELSE
                OUTPUT STRING("Invalid Password")
            ENDIF
        ENDIF
ENDFUNCTION