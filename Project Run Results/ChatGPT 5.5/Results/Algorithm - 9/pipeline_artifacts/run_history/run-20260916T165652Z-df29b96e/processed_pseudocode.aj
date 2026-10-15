    INPUT List, Target

    Found <- FALSE

    FOR i <- 0 TO LENGTH(List)-1
        IF List[i] = Target THEN
            OUTPUT "Found at position", i
            Found <- TRUE
            EXIT FOR
        ENDIF
    ENDFOR

    IF Found = FALSE THEN
        OUTPUT "Target not found"
    ENDIF
END