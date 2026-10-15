FUNCTION unnamed_function ACCEPTS(arr, target)
    left <- 0
    right <- LENGTH OF arr-1

    WHILE left <= right DO
        mid <- (left + right) INTEGER DIVISION 2

        IF arr[mid] == target THEN
            RETURN mid

        ENDIF
        IF arr[left] <= arr[mid] THEN
            IF arr[left] <= target AND target < arr[mid] THEN
                right <- mid - 1
            ELSE
                left <- mid + 1
            ENDIF
        ELSE
            IF arr[mid] < target AND target <= arr[right] THEN
                left <- mid + 1
            ELSE
                right <- mid - 1

            ENDIF
        ENDIF
    ENDWHILE
    RETURN -1
ENDFUNCTION