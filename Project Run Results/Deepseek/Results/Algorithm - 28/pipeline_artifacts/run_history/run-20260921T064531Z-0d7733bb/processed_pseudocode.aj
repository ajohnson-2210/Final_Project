FUNCTION slidingWindowMax ACCEPTS(arr, k)
    result <- EMPTY LIST
    deque <- CALL create_deque()
    FOR i <- IN RANGE 0 TO (LENGTH OF arr-1) + 1 DO
        COMMENT Remove elements out of window from front
        WHILE NOT CALL deque_is_empty(deque) AND CALL deque_front(deque) <= i - k DO
            CALL deque_pop_front(deque)
        COMMENT Maintain decreasing order in deque
        ENDWHILE
        WHILE NOT CALL deque_is_empty(deque) AND arr[CALL deque_back(deque)] <= arr[i] DO
            CALL deque_pop_back(deque)
        ENDWHILE
        CALL deque_push_back(deque, i)
        COMMENT Add max to result once window is full
        IF i >= k - 1 THEN
            APPEND arr[CALL deque_front(deque)] TO result
        ENDIF
    ENDFOR
    RETURN result
ENDFUNCTION