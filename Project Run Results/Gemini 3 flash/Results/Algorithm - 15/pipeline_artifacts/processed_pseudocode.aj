FUNCTION FindSecondLargest ACCEPTS(arr)
    IF LENGTH OF arr < 2 THEN
        RETURN NULL

    ENDIF
    largest <- CALL negative_infinity()
    second_largest <- CALL negative_infinity()

    FOR EACH num IN arr DO
        IF num > largest THEN
            second_largest <- largest
            largest <- num
        ELSE IF num > second_largest AND num != largest THEN
            second_largest <- num
        ENDIF
    ENDFOR

    RETURN second_largest
ENDFUNCTION