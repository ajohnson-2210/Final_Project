FUNCTION unnamed_function ACCEPTS(Numbers)
        Sum <- 0

        FOR EACH Number IN Numbers DO
            IF Number MODULUS 2 == 0 THEN
                Sum <- Sum + Number
            ENDIF
        ENDFOR

        OUTPUT Sum
ENDFUNCTION