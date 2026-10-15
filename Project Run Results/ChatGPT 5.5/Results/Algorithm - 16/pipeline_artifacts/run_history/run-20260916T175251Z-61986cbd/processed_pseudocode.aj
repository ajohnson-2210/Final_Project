FUNCTION unnamed_function ACCEPTS(A, B)
        WHILE B != 0 DO
            Temp <- B
            B <- A MODULUS B
            A <- Temp
        ENDWHILE

        OUTPUT A
ENDFUNCTION