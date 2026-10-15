FUNCTION unnamed_function ACCEPTS(Matrix, N)
        Sum <- 0

        FOR i <- IN RANGE 0 TO (N - 1) + 1 DO
            Sum <- Sum + Matrix[i][i]
        ENDFOR

        OUTPUT Sum
ENDFUNCTION