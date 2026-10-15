FUNCTION unnamed_function ACCEPTS(Array)
    CurrentSum <- Array[0]
    MaxSum <- Array[0]

    FOR i <- IN RANGE 1 TO (LENGTH OF Array - 1) + 1 DO
        CurrentSum <- CALL max(Array[i], CurrentSum + Array[i])

        IF CurrentSum > MaxSum THEN
            MaxSum <- CurrentSum
        ENDIF
    ENDFOR

    OUTPUT MaxSum
ENDFUNCTION