    INPUT Matrix, N

    Sum <- 0

    FOR i <- 0 TO N - 1
        Sum <- Sum + Matrix[i][i]
    ENDFOR

    OUTPUT Sum
END