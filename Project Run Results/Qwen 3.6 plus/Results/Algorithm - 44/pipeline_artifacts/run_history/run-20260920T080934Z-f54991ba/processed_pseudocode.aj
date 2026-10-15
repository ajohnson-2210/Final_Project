FUNCTION unnamed_function ACCEPTS(arr)
    maxSoFar <- CALL negative_infinity()
    currentMax <- 0

    FOR EACH num IN arr DO
        currentMax <- currentMax + num

        IF maxSoFar < currentMax THEN
            maxSoFar <- currentMax

        ENDIF
        IF currentMax < 0 THEN
            currentMax <- 0

        ENDIF
    ENDFOR
    RETURN maxSoFar
ENDFUNCTION