FUNCTION find_largest ACCEPTS(numbers AS LIST)
    IF LENGTH OF numbers == 0 THEN
        RAISE STRING("The list cannot be empty")
    ENDIF
    largest <- numbers[0]
    FOR EACH number IN numbers DO
        IF number > largest THEN
            largest <- number
        ENDIF
    ENDFOR
    OUTPUT STRING("The largest value is {largest}")
    RETURN largest
ENDFUNCTION
