    INPUT Array

    CurrentSum <- Array[0]
    MaxSum <- Array[0]

    FOR i <- 1 TO LENGTH(Array)-1
        CurrentSum <- MAX(Array[i], CurrentSum + Array[i])

        IF CurrentSum > MaxSum THEN
            MaxSum <- CurrentSum
        ENDIF
    ENDFOR

    OUTPUT MaxSum
END