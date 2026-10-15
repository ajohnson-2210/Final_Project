FUNCTION unnamed_function ACCEPTS(Text)
        Reverse <- EMPTY STRING

        FOR i <- IN RANGE LENGTH OF Text-1 TO (0) - 1 STEP -1 DO
            Reverse <- Reverse + Text[i]
        ENDFOR

        OUTPUT Reverse
ENDFUNCTION