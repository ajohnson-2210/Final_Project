FUNCTION MaxSubarraySum ACCEPTS(arr)
    max_so_far <- arr[0]
    current_max <- arr[0]

    FOR i <- IN RANGE 1 TO (LENGTH OF arr - 1) + 1 DO
        current_max <- CALL max(arr[i], current_max + arr[i])
        max_so_far <- CALL max(max_so_far, current_max)
    ENDFOR

    RETURN max_so_far
ENDFUNCTION