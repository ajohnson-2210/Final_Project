FUNCTION unnamed_function ACCEPTS(arr)
    first <- CALL negative_infinity()
    second <- CALL negative_infinity()

    FOR EACH num IN arr DO
        IF num > first THEN
            second <- first
            first <- num
        ELSE IF num > second AND num != first THEN
            second <- num

        ENDIF
    ENDFOR
    RETURN second
ENDFUNCTION