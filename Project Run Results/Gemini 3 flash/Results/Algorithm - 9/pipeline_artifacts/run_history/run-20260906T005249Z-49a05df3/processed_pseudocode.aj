FUNCTION LinearSearch ACCEPTS(arr, T)
    FOR index <- IN RANGE 0 TO (LENGTH OF arr - 1) + 1 DO
        IF arr[index] == T THEN
            RETURN STRING("Target found at index: ") + index
        ENDIF
    ENDFOR
    RETURN STRING("Target does not exist in the list.")
ENDFUNCTION