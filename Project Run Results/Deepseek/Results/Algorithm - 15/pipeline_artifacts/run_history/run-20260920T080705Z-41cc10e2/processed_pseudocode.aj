FUNCTION secondLargest ACCEPTS(arr)
    IF LENGTH OF arr < 2 THEN
        RETURN NULL
        COMMENT or error
    ENDIF
    largest <- CALL negative_infinity()
    second <- CALL negative_infinity()
    FOR EACH num IN arr DO
        IF num > largest THEN
            second <- largest
            largest <- num
        ELSE IF num > second AND num != largest THEN
            second <- num
        ENDIF
    ENDFOR
    RETURN second
ENDFUNCTION