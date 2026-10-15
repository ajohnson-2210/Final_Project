FUNCTION unnamed_function ACCEPTS(arr, k)
    result <- EMPTY LIST
    deque <- EMPTY LIST

    FOR i <- IN RANGE 0 TO (LENGTH OF arr-1) + 1 DO
        IF deque[0] == i - k THEN
            REMOVE FIRST ITEM FROM deque

        ENDIF
        WHILE LENGTH OF deque > 0 AND arr[deque[-1]] <= arr[i] DO
            REMOVE LAST ITEM FROM deque

        ENDWHILE
        APPEND i TO deque

        IF i >= k - 1 THEN
            APPEND arr[deque[0]] TO result

        ENDIF
    ENDFOR
    RETURN result
ENDFUNCTION