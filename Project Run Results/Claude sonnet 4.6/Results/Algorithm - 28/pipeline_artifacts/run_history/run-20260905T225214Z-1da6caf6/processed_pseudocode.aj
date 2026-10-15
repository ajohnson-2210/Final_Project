FUNCTION slidingWindowMax ACCEPTS(arr, k)
    result <- EMPTY LIST
    deque <- EMPTY LIST
    COMMENT stores indices
    FOR i <- IN RANGE 0 TO (LENGTH OF arr - 1) + 1 DO
        WHILE LENGTH OF deque > 0 AND deque[0] < i - k + 1 DO
            REMOVE FIRST ITEM FROM deque
        ENDWHILE
        WHILE LENGTH OF deque > 0 AND arr[deque[-1]] < arr[i] DO
            REMOVE LAST ITEM FROM deque
        ENDWHILE
        APPEND i TO deque
        IF i >= k - 1 THEN
            APPEND arr[deque[0]] TO result
        ENDIF
    ENDFOR
    RETURN result
ENDFUNCTION