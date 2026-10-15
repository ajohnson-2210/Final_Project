FUNCTION unnamed_function ACCEPTS(Numbers)
        Sum <- 0

        FOR EACH Number IN Numbers DO
            Sum <- Sum + Number
        ENDFOR

        Average <- Sum / LENGTH OF Numbers

        OUTPUT Sum
        OUTPUT Average
ENDFUNCTION