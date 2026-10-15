FUNCTION unnamed_function ACCEPTS(Array1, Array2)
        i <- 0
        j <- 0

        WHILE i < LENGTH OF Array1 AND j < LENGTH OF Array2 DO
            IF Array1[i] == Array2[j] THEN
                OUTPUT Array1[i]
                i <- i + 1
                j <- j + 1
            ELSE IF Array1[i] < Array2[j] THEN
                i <- i + 1
            ELSE
                j <- j + 1
            ENDIF
        ENDWHILE
ENDFUNCTION