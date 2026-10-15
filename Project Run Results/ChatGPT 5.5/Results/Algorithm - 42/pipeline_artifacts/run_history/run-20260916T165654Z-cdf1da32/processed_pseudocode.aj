    INPUT Array, Target

    FOR i <- 0 TO LENGTH(Array)-2
        FOR j <- i+1 TO LENGTH(Array)-1
            IF Array[i] + Array[j] = Target THEN
                OUTPUT Array[i], Array[j]
            ENDIF
        ENDFOR
    ENDFOR
END