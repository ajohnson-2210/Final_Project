FUNCTION unnamed_function ACCEPTS(Text)
        Count <- 0

        FOR EACH Character IN Text DO
            Count <- Count + 1
        ENDFOR

        OUTPUT Count
ENDFUNCTION