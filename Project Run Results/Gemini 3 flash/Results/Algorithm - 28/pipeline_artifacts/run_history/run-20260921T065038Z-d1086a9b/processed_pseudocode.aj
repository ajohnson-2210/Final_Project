FUNCTION SlidingWindowMaximum ACCEPTS(arr, k)
    result <- EMPTY LIST
    deque <- CALL create_deque()
    COMMENT Stores indices

    FOR i <- IN RANGE 0 TO (LENGTH OF arr - 1) + 1 DO
        IF NOT CALL deque_is_empty(deque) AND CALL deque_front(deque) <= i - k THEN
            CALL deque_pop_front(deque)
        ENDIF

        WHILE NOT CALL deque_is_empty(deque) AND arr[CALL deque_back(deque)] <= arr[i] DO
            CALL deque_pop_back(deque)
        ENDWHILE

        CALL deque_push_back(deque, i)

        IF i >= k - 1 THEN
            APPEND arr[CALL deque_front(deque)] TO result
        ENDIF
    ENDFOR

    RETURN result
ENDFUNCTION