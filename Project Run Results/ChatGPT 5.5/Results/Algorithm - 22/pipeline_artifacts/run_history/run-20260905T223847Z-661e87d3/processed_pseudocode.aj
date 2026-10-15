FUNCTION unnamed_function ACCEPTS(Number)
        Factorial <- 1

        FOR i <- IN RANGE 1 TO (Number) + 1 DO
            Factorial <- Factorial * i
        ENDFOR

        OUTPUT Factorial
ENDFUNCTION