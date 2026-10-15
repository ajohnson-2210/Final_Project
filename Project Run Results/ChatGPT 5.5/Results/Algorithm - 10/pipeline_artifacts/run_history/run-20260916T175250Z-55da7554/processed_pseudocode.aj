FUNCTION unnamed_function ACCEPTS(Text)
        A <- 0
        E <- 0
        I <- 0
        O <- 0
        U <- 0

        FOR EACH Character IN CALL lowercase(Text) DO
            IF Character == STRING("a") THEN
                A <- A + 1
            ELSE IF Character == STRING("e") THEN
                E <- E + 1
            ELSE IF Character == STRING("i") THEN
                I <- I + 1
            ELSE IF Character == STRING("o") THEN
                O <- O + 1
            ELSE IF Character == STRING("u") THEN
                U <- U + 1
            ENDIF
        ENDFOR

        OUTPUT CALL output_values(A, E, I, O, U)
ENDFUNCTION