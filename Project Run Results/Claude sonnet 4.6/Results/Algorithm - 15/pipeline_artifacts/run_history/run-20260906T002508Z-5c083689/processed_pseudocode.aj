FUNCTION secondLargest ACCEPTS(arr)
    second <- CALL negative_infinity()
    largest <- second
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