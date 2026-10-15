FUNCTION searchRotated ACCEPTS(arr, target)
    low <- 0
    high <- LENGTH OF arr - 1
    WHILE low <= high DO
        mid <- (low + high) INTEGER DIVISION 2
        IF arr[mid] == target THEN
            RETURN mid
        ENDIF
        IF arr[low] <= arr[mid] THEN
        COMMENT left half is sorted
            IF arr[low] <= target AND target < arr[mid] THEN
                high <- mid - 1
            ELSE
                low <- mid + 1
            ENDIF
        ELSE
        COMMENT right half is sorted
            IF arr[mid] < target AND target <= arr[high] THEN
                low <- mid + 1
            ELSE
                high <- mid - 1
            ENDIF
        ENDIF
    ENDWHILE
    RETURN -1
ENDFUNCTION