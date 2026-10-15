FUNCTION unnamed_function ACCEPTS(Text)
        COUNT frequency of each character

        FOR EACH Character IN Text DO
            IF CALL Frequency(Character) == 1 THEN
                OUTPUT Character
                RETURN
            ENDIF
        ENDFOR

        OUTPUT STRING("None Found")
ENDFUNCTION