FUNCTION unnamed_function ACCEPTS(Text)
        Dictionary <- EMPTY DICTIONARY

        FOR EACH Character IN Text DO
            IF Character IN Dictionary THEN
                Dictionary[Character] <- Dictionary[Character] + 1
            ELSE
                Dictionary[Character] <- 1
            ENDIF
        ENDFOR

        OUTPUT Dictionary
ENDFUNCTION